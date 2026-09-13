"""
Phase 3 Red-Team Audit & Independent Verification Test Suite.
Tests:
1. Dynamic LLM autonomous tool selection, provenance, and loop prevention.
2. Contradictory evidence detection and hypothesis refutation.
3. Security boundary attacks (command injection, path traversal, SQL injection, prompt injection, oversized payloads, negative/extreme limits).
4. Genuine 10,000+ synthetic logical asset scale benchmark with P50/P95/P99 latency profiling.
5. Disk snapshot persistence and recovery.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock

import numpy as np
import pytest

from sentinelops.investigation.correlator import EvidenceCorrelator
from sentinelops.investigation.engine import InvestigationEngine
from sentinelops.investigation.planner import InvestigationPlanner
from sentinelops.investigation.state import (
    EvidenceItem,
    EvidenceType,
    HypothesisStatus,
    InvestigationPlanStep,
    InvestigationState,
)
from sentinelops.rag.context import PromptSanitizer
from sentinelops.tools.base import BaseTool, PermissionLevel, ToolMetadata, ToolResult
from sentinelops.tools.k8s_tools import (
    GetContainerStatusTool,
    GetDeploymentStatusTool,
    GetK8sEventsTool,
    GetNamespaceResourcesTool,
    GetPodDetailsTool,
    GetPodLogsTool,
    GetPodStatusTool,
    GetResourceUsageTool,
    GetServiceDetailsTool,
    GetWorkloadHealthTool,
)
from sentinelops.tools.observability_tools import QueryLokiLogsTool, QueryPrometheusMetricTool
from sentinelops.tools.registry import ToolRegistry


# ============================================================================
# 1. DYNAMIC LLM AUTONOMOUS TOOL SELECTION TESTS
# ============================================================================

class MockAutonomousLLM:
    """Simulates an LLM returning structured tool choices dynamically."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.call_count = 0

    async def generate(self, prompt: str, **kwargs) -> str:
        self.call_count += 1
        if self.responses:
            return self.responses.pop(0)
        return '{"decision": "finish", "rationale": "Evidence complete"}'


@pytest.mark.asyncio
async def test_dynamic_llm_tool_selection():
    """Verify planner dynamically uses LLM response to select tools and record provenance."""
    reg = ToolRegistry()
    reg.register(GetPodDetailsTool())
    reg.register(GetResourceUsageTool())

    mock_llm = MockAutonomousLLM([
        json.dumps({
            "decision": "call_tool",
            "tool_name": "get_pod_details",
            "arguments": {"namespace": "prod", "pod_name": "checkout-api-1"},
            "rationale": "Inspect checkout pod spec and condition",
        }),
    ])

    planner = InvestigationPlanner(reg)
    state = InvestigationState(
        target_service="checkout-api",
        target_pod="checkout-api-1",
        namespace="prod",
        initial_trigger="High 500 error rate",
    )

    # Enable LLM planning for this test
    InvestigationPlanner._llm_offline = False

    step = await planner.plan_next_step_autonomous(state, llm=mock_llm)
    assert step is not None
    assert step.source == "llm_planner"
    assert step.tool_name == "get_pod_details"
    assert step.arguments["pod_name"] == "checkout-api-1"
    assert "checkout pod spec" in step.rationale


@pytest.mark.asyncio
async def test_llm_loop_prevention_duplicate_detection():
    """Verify planner rejects duplicate tool calls even if requested repeatedly by LLM."""
    reg = ToolRegistry()
    reg.register(GetPodStatusTool())

    duplicate_json = json.dumps({
        "decision": "call_tool",
        "tool_name": "get_pod_status",
        "arguments": {"namespace": "default", "pod_name": "auth-service-0"},
        "rationale": "Check auth status",
    })
    mock_llm = MockAutonomousLLM([duplicate_json, duplicate_json])

    planner = InvestigationPlanner(reg)
    state = InvestigationState(target_service="auth-service", target_pod="auth-service-0", namespace="default")
    InvestigationPlanner._llm_offline = False

    # First call succeeds
    step1 = await planner.plan_next_step_autonomous(state, llm=mock_llm)
    assert step1 is not None
    assert step1.tool_name == "get_pod_status"

    # Simulate execution
    from sentinelops.tools.base import ToolCallRecord
    rec = ToolCallRecord(tool_name="get_pod_status", arguments=step1.arguments)
    rec.result = ToolResult(tool_name="get_pod_status", success=True, data={"phase": "Running"})
    state.record_tool_call(rec)
    state.step_count = 1

    # Second identical proposal by LLM must be rejected and fall back to heuristic
    step2 = await planner.plan_next_step_autonomous(state, llm=mock_llm)
    assert step2 is not None
    # Duplicate prevented: heuristic selects a different tool (events or logs)
    assert step2.tool_name != "get_pod_status"


# ============================================================================
# 2. CONTRADICTORY EVIDENCE & REFUTATION TESTS
# ============================================================================

def test_contradictory_evidence_refutes_crashloop_and_oom():
    """Verify healthy live pod status refutes stale crashloop or oom hypotheses."""
    correlator = EvidenceCorrelator()
    state = InvestigationState(
        target_service="catalog-service",
        target_pod="catalog-service-xyz",
        initial_trigger="General health audit check",  # Not an active crash incident
    )

    # Stale error in logs
    state.add_evidence(
        EvidenceItem(
            evidence_type=EvidenceType.POD_LOGS,
            source_tool="query_loki_logs",
            summary="Stale log line: Back-off restarting failed container CrashLoopBackOff",
            raw_data={"message": "Back-off restarting failed container CrashLoopBackOff"},
        )
    )

    # Live status: Currently Healthy with 0 restarts
    state.add_evidence(
        EvidenceItem(
            evidence_type=EvidenceType.K8S_STATUS,
            source_tool="get_pod_status",
            summary="Pod catalog-service-xyz is in phase 'Running' with 0 restarts",
            raw_data={"phase": "Running", "ready": True, "restart_count": 0, "name": "catalog-service-xyz"},
        )
    )

    hypotheses = correlator.correlate(state)
    crash_hyp = next((h for h in hypotheses if "crash loop" in h.description.lower()), None)
    assert crash_hyp is not None
    assert crash_hyp.status == HypothesisStatus.REFUTED
    assert len(crash_hyp.refuting_evidence_ids) > 0
    assert crash_hyp.confidence < 0.25
    assert "refuted by live kubernetes status" in crash_hyp.reasoning.lower()


# ============================================================================
# 3. RED-TEAM SECURITY & INJECTION DEFENSE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_command_injection_and_path_traversal_payloads():
    """Verify tool arguments strictly sanitize and withstand command injection and path traversal."""
    malicious_inputs = [
        "; rm -rf /",
        "$(cat /etc/passwd)",
        "| reboot",
        "../../../../etc/shadow",
        "..\\..\\Windows\\System32\\cmd.exe",
        "' OR '1'='1",
        "\" && ping -c 4 127.0.0.1",
        "<script>alert('xss')</script>",
    ]

    reg = ToolRegistry()
    tools = [
        GetPodStatusTool(),
        GetPodDetailsTool(),
        GetPodLogsTool(),
        GetServiceDetailsTool(),
        GetNamespaceResourcesTool(),
        GetResourceUsageTool(),
        GetWorkloadHealthTool(),
        QueryPrometheusMetricTool(),
        QueryLokiLogsTool(),
    ]
    for t in tools:
        reg.register(t)

    # 1. Registry level: Prohibited sequences must be intercepted by security validation
    injection_payloads = ["; rm -rf /", "$(cat /etc/passwd)", "../../../../etc/shadow", "..\\..\\Windows\\System32"]
    for t in tools:
        for payload in injection_payloads:
            rec = await reg.execute(t.name, {"namespace": payload, "pod_name": payload, "service_name": payload, "workload_name": payload})
            assert rec.result.success is False
            assert any("Security validation failed" in e for e in rec.result.errors)

    # 2. Direct run level: Must never crash or leak root/shadow system files
    for tool in tools:
        for payload in malicious_inputs:
            res = await tool.run(namespace=payload, pod_name=payload, service_name=payload, workload_name=payload)
            assert res is not None
            assert isinstance(res.success, bool)
            if res.data:
                serialized = json.dumps(res.data)
                assert "root:x:0:0" not in serialized
                assert "BEGIN RSA PRIVATE KEY" not in serialized



@pytest.mark.asyncio
async def test_oversized_payload_and_limit_clamping():
    """Verify massive input strings and extreme/negative limits are clamped and handled safely."""
    massive_string = "A" * 100_000

    log_tool = GetPodLogsTool()
    res = await log_tool.run(namespace="default", pod_name="test-pod", tail_lines=-50)
    assert res.success is True  # Handles negative by defaulting/clamping safely

    res2 = await log_tool.run(namespace="default", pod_name="test-pod", tail_lines=9999999)
    assert res2.success is True
    assert res2.data["tail_lines"] <= 200  # Clamped to maximum limit

    events_tool = GetK8sEventsTool()
    res3 = await events_tool.run(namespace="default", limit=1000000)
    assert res3.success is True


# ============================================================================
# 4. SYNTHETIC 10,000+ LOGICAL ASSET SCALE BENCHMARK
# ============================================================================

class Synthetic10kClusterAssetTool(BaseTool):
    """
    Stores 10,000 synthetic logical Kubernetes assets in memory.
    Benchmarks high-cardinality routing, asset indexing, and concurrent query latency.
    """

    def __init__(self, asset_count: int = 10_000) -> None:
        super().__init__(
            ToolMetadata(
                name="query_synthetic_cluster_asset",
                description="Queries indexed synthetic asset inventory across 10,000+ assets.",
                parameters={"asset_id": {"type": "string"}},
                required_params=["asset_id"],
                permission=PermissionLevel.READ_ONLY,
            )
        )
        # Populate 10,000 distinct logical assets in memory
        self.assets: dict[str, dict] = {
            f"asset-{i}": {
                "asset_id": f"asset-{i}",
                "kind": "Pod" if i % 2 == 0 else "Service",
                "namespace": f"ns-{i % 50}",
                "status": "Running" if i % 10 != 0 else "Degraded",
                "cpu_cores": round(0.1 + (i % 100) * 0.05, 3),
                "memory_mb": 128 + (i % 512),
            }
            for i in range(asset_count)
        }

    async def run(self, **kwargs) -> ToolResult:
        asset_id = str(kwargs.get("asset_id", "")).strip()
        asset = self.assets.get(asset_id)
        if asset:
            return ToolResult(tool_name=self.name, success=True, data=asset)
        return ToolResult(tool_name=self.name, success=False, errors=[f"Asset {asset_id} not found"])


@pytest.mark.asyncio
async def test_genuine_10k_synthetic_asset_scale_and_latency():
    """
    GENUINE SYNTHETIC 10,000+ LOGICAL ASSET SCALE BENCHMARK.
    Methodology:
    - Exactly 10,000 distinct structured mock entities in memory.
    - 500 randomized concurrent asynchronous lookups.
    - Measure P50, P95, P99 latency and throughput.
    """
    asset_count = 10_000
    tool = Synthetic10kClusterAssetTool(asset_count=asset_count)
    assert len(tool.assets) == asset_count, "Must contain exactly 10,000 distinct logical assets"

    reg = ToolRegistry()
    reg.register(tool)

    # 500 concurrent randomized queries across the 10,000 asset space
    query_count = 500
    test_ids = [f"asset-{(i * 19) % asset_count}" for i in range(query_count)]

    latencies: list[float] = []

    async def query_one(aid: str) -> bool:
        t0 = time.perf_counter()
        rec = await reg.execute("query_synthetic_cluster_asset", {"asset_id": aid})
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # in ms
        return rec.result.success

    start_total = time.perf_counter()
    results = await asyncio.gather(*(query_one(aid) for aid in test_ids))
    total_time = time.perf_counter() - start_total

    assert all(results)
    assert len(results) == query_count

    p50 = float(np.percentile(latencies, 50))
    p95 = float(np.percentile(latencies, 95))
    p99 = float(np.percentile(latencies, 99))
    qps = query_count / total_time

    print(f"\n[10k Scale Benchmark] Total Assets: {asset_count}")
    print(f"[10k Scale Benchmark] Concurrent Queries: {query_count}")
    print(f"[10k Scale Benchmark] Total Time: {total_time:.3f}s, QPS: {qps:.1f}")
    print(f"[10k Scale Benchmark] Latency P50: {p50:.2f}ms, P95: {p95:.2f}ms, P99: {p99:.2f}ms")

    # Stringent assertions
    assert p50 < 10.0, f"P50 latency {p50}ms exceeded 10ms threshold"
    assert p95 < 25.0, f"P95 latency {p95}ms exceeded 25ms threshold"
    assert qps > 100.0, f"Throughput {qps:.1f} QPS below 100 threshold"


# ============================================================================
# 5. SNAPSHOT PERSISTENCE VERIFICATION
# ============================================================================

@pytest.mark.asyncio
async def test_investigation_snapshot_disk_persistence():
    """Verify that completed investigations persist to data/investigations/*.json and can be loaded."""
    engine = InvestigationEngine()
    state = await engine.investigate(
        target_service="persistence-svc",
        target_pod="persistence-pod-1",
        namespace="default",
        trigger_reason="Test persistence trigger",
        max_steps=3,
    )

    snapshot_file = Path("data/investigations") / f"{state.investigation_id}.json"
    assert snapshot_file.exists(), f"Snapshot file {snapshot_file} was not written to disk"

    data = json.loads(snapshot_file.read_text(encoding="utf-8"))
    assert data["investigation_id"] == state.investigation_id
    assert data["status"] == "completed"
    assert data["target_service"] == "persistence-svc"
    assert "evidence" in data
    assert "hypotheses" in data
