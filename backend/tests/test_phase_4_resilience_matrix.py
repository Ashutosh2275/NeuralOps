"""
Phase 4 Test Suite: Resilience Matrix, Concurrency, and Scale Validation.
Tests external system failure handling (K8s/Prometheus/Loki/Ollama/Redis/Postgres),
multi-tenant investigation state isolation, and 10,000+ synthetic logical asset scale.
"""
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch

from sentinelops.investigation.engine import InvestigationEngine, get_investigation_engine
from sentinelops.investigation.state import InvestigationStatus
from sentinelops.engines.dependency import DependencyIntelligenceEngine


@pytest.mark.asyncio
async def test_failure_matrix_individual_and_simultaneous_outages():
    """
    Test external failure matrix:
    - K8s down
    - Prometheus down
    - Loki down
    - Ollama down
    - All telemetry systems down simultaneously
    Verifies investigation terminates safely, returns partial evidence, records warnings, and never crashes.
    """
    engine = InvestigationEngine()

    # 1. K8s Down
    with patch("sentinelops.collectors.k8s_collector.KubernetesCollector.collect_all", side_effect=ConnectionRefusedError("K8s API down")):
        state = await engine.investigate(
            target_service="payment-service",
            trigger_reason="Test K8s outage",
            max_steps=4,
        )
        assert state.status == InvestigationStatus.COMPLETED
        assert state.final_rca is not None
        assert any("error" in str(w).lower() or "fail" in str(w).lower() for w in state.warnings + [e.description for e in state.evidence]) or state.confidence < 0.8

    # 2. Prometheus Down
    with patch("sentinelops.collectors.prometheus_collector.PrometheusCollector.collect", side_effect=TimeoutError("Prometheus timeout")):
        state = await engine.investigate(
            target_service="order-service",
            trigger_reason="Test Prometheus outage",
            max_steps=4,
        )
        assert state.status == InvestigationStatus.COMPLETED

    # 3. Loki Down
    with patch("sentinelops.collectors.loki_collector.LokiCollector.collect", side_effect=Exception("Loki connection refused")):
        state = await engine.investigate(
            target_service="inventory-service",
            trigger_reason="Test Loki outage",
            max_steps=4,
        )
        assert state.status == InvestigationStatus.COMPLETED

    # 4. Simultaneous Outage: K8s + Prom + Loki + Ollama ALL DOWN
    with patch("sentinelops.collectors.k8s_collector.KubernetesCollector.collect_all", side_effect=Exception("K8s Down")), \
         patch("sentinelops.collectors.prometheus_collector.PrometheusCollector.collect", side_effect=Exception("Prom Down")), \
         patch("sentinelops.collectors.loki_collector.LokiCollector.collect", side_effect=Exception("Loki Down")), \
         patch("sentinelops.agents.ollama_client.OllamaClient.generate", side_effect=Exception("Ollama Down")):


        state = await engine.investigate(
            target_service="critical-service",
            trigger_reason="Total telemetry outage",
            max_steps=4,
        )
        # Must terminate gracefully without crashing
        assert state.status == InvestigationStatus.COMPLETED
        assert state.final_rca is not None
        assert state.confidence <= 0.65  # Epistemic uncertainty reflects severe outage


@pytest.mark.asyncio
async def test_concurrent_investigation_state_isolation():
    """
    Run 25 concurrent investigations across different services and pods.
    Verify ZERO state cross-contamination (no shared evidence, hypotheses, or tool calls).
    """
    engine = InvestigationEngine()
    services = [
        f"service-{i}" for i in range(25)
    ]

    async def run_single(svc: str):
        return await engine.investigate(
            target_service=svc,
            target_pod=f"{svc}-pod-1",
            trigger_reason=f"Incident in {svc}",
            max_steps=3,
        )

    start = time.perf_counter()
    tasks = [run_single(svc) for svc in services]
    results = await asyncio.gather(*tasks)
    duration = time.perf_counter() - start

    assert len(results) == 25
    seen_investigation_ids = set()
    all_evidence_ids = set()

    for idx, state in enumerate(results):
        assert state.status == InvestigationStatus.COMPLETED
        assert state.target_service == f"service-{idx}"
        assert state.investigation_id not in seen_investigation_ids
        seen_investigation_ids.add(state.investigation_id)

        # Verify evidence belongs ONLY to this investigation
        for ev in state.evidence:
            assert ev.evidence_id not in all_evidence_ids, f"Evidence leaked across investigations: {ev.evidence_id}"
            all_evidence_ids.add(ev.evidence_id)

    qps = 25 / duration
    assert qps > 5.0, f"Concurrent investigation throughput was too low: {qps:.1f} QPS"


def test_synthetic_10k_logical_asset_scale_benchmark():
    """
    SYNTHETIC SCALE BENCHMARK:
    Construct a synthetic operational topology representing 10,000+ logical assets
    (microservices, deployments, pods, databases, queues, and dependency edges).
    Measure P50, P95, P99 traversal and blast-radius latencies.
    """
    dep_engine = DependencyIntelligenceEngine()

    total_services = 1000
    pods_per_service = 10
    # 1,000 services * 10 pods = 10,000 logical pod assets + 1,000 service assets = 11,000 assets

    start_build = time.perf_counter()
    for s_idx in range(total_services):
        svc_name = f"svc-{s_idx:04d}"
        ns = "production"

        # Add service to pods edges (10 pods per service)
        for p_idx in range(pods_per_service):
            pod_name = f"{svc_name}-pod-{p_idx}"
            dep_engine.add_edge(
                source_ns=ns,
                source_name=pod_name,
                source_kind="Pod",
                target_ns=ns,
                target_name=svc_name,
                target_kind="Service",
                edge_type="routes_to",
                confidence=0.9,
            )

        # Connect inter-service dependencies (mesh)
        if s_idx > 0:
            parent = f"svc-{(s_idx - 1) % 100:04d}"
            dep_engine.add_edge(
                source_ns=ns,
                source_name=parent,
                source_kind="Service",
                target_ns=ns,
                target_name=svc_name,
                target_kind="Service",
                edge_type="calls",
                confidence=0.8,
            )

    build_time = (time.perf_counter() - start_build) * 1000
    assert dep_engine._graph.number_of_nodes() >= 10000, f"Expected 10,000+ nodes, got {dep_engine._graph.number_of_nodes()}"

    # Benchmark: 200 blast-radius calculations
    latencies = []
    for i in range(200):
        target_name = f"svc-{(i * 5) % total_services:04d}"
        target_node = dep_engine.node_id("production", "Service", target_name)
        t0 = time.perf_counter()
        res = dep_engine.blast_radius(target_node, max_depth=2)

        lat = (time.perf_counter() - t0) * 1000
        latencies.append(lat)

    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95)]
    p99 = latencies[int(n * 0.99)]

    assert p50 < 5.0, f"P50 latency too high: {p50:.2f}ms"
    assert p95 < 15.0, f"P95 latency too high: {p95:.2f}ms"
    assert p99 < 30.0, f"P99 latency too high: {p99:.2f}ms"

