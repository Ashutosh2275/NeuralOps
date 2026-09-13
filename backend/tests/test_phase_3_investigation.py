"""
Phase 3 Autonomous Investigation Engine Tests.
Verifies multi-step investigation, planning, evidence correlation, hypotheses evaluation, and duplicate prevention.
"""
from __future__ import annotations

import pytest

from sentinelops.investigation.correlator import EvidenceCorrelator
from sentinelops.investigation.engine import InvestigationEngine, get_investigation_engine
from sentinelops.investigation.planner import InvestigationPlanner
from sentinelops.investigation.state import (
    EvidenceItem,
    EvidenceType,
    HypothesisStatus,
    InvestigationState,
)
from sentinelops.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_planner_priority_and_duplicate_prevention():
    reg = ToolRegistry()
    planner = InvestigationPlanner(reg)
    state = InvestigationState(
        target_service="payment-service",
        target_pod="payment-service-pod-1",
        namespace="default",
        max_steps=5,
    )

    # Step 1 should inspect pod status
    s1 = planner.plan_next_step(state)
    assert s1 is not None
    assert s1.tool_name == "get_pod_status"
    assert s1.arguments["pod_name"] == "payment-service-pod-1"

    # Simulate execution of step 1
    from sentinelops.tools.base import ToolCallRecord, ToolResult
    record = ToolCallRecord(tool_name="get_pod_status", arguments=s1.arguments)
    record.result = ToolResult(tool_name="get_pod_status", success=True, data={"phase": "Failed", "restart_count": 5})
    state.record_tool_call(record)
    state.add_evidence(
        EvidenceItem(
            evidence_type=EvidenceType.K8S_STATUS,
            source_tool="get_pod_status",
            summary="Pod failed with 5 restarts",
            raw_data=record.result.data,
        )
    )
    state.step_count = 1

    # Step 2 should not repeat get_pod_status; should plan get_k8s_events or logs
    s2 = planner.plan_next_step(state)
    assert s2 is not None
    assert s2.tool_name != "get_pod_status"
    assert s2.tool_name in ("get_k8s_events", "get_pod_logs")


@pytest.mark.asyncio
async def test_evidence_correlator_oom_detection():
    correlator = EvidenceCorrelator()
    state = InvestigationState(target_service="analytics-worker")

    state.add_evidence(
        EvidenceItem(
            evidence_type=EvidenceType.K8S_STATUS,
            source_tool="get_pod_status",
            summary="Container terminated with reason OOMKilled and exit code 137",
            raw_data={"reason": "OOMKilled", "exit_code": 137},
        )
    )
    state.add_evidence(
        EvidenceItem(
            evidence_type=EvidenceType.METRIC_ANOMALY,
            source_tool="query_prometheus_metric",
            summary="Memory usage 99.8% breached limit",
            raw_data={"metrics": [{"metric": "memory_percent", "value": 99.8, "breached": True}]},
        )
    )

    hypotheses = correlator.correlate(state)
    assert len(hypotheses) > 0
    oom_hyp = next((h for h in hypotheses if "oomkilled" in h.description.lower()), None)
    assert oom_hyp is not None
    assert oom_hyp.status == HypothesisStatus.CONFIRMED
    assert oom_hyp.confidence >= 0.85

    conf = correlator.compute_composite_confidence(state)
    assert conf >= 0.80


@pytest.mark.asyncio
async def test_end_to_end_autonomous_investigation():
    engine = InvestigationEngine()

    state = await engine.investigate(
        incident_id="INC-3001",
        target_service="payment-service",
        target_pod="payment-service-pod-1",
        namespace="default",
        trigger_reason="CrashLoopBackOff detected in payment-service",
        max_steps=6,
    )

    assert state.status == "completed"
    assert state.step_count > 0
    assert len(state.evidence) > 0
    assert len(state.tool_history) > 0
    assert state.final_root_cause is not None
    assert len(state.final_recommendations) > 0
    assert state.confidence > 0.0

    # Retrieve from engine registry
    retrieved = engine.get_investigation(state.investigation_id)
    assert retrieved is not None
    assert retrieved.investigation_id == state.investigation_id

    # Verify serialization
    state_dict = state.to_dict()
    assert state_dict["investigation_id"] == state.investigation_id
    assert "evidence" in state_dict
    assert "hypotheses" in state_dict
    assert "tool_history" in state_dict
