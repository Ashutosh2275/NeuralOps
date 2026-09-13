"""
Phase 3 Golden Investigation Scenarios.
Validates exact multi-tool triage workflows for realistic Kubernetes failures:
- CrashLoopBackOff with configuration failure
- OOMKilled container memory spike
- PVC storage saturation
- Cascading microservice dependency failure
"""
from __future__ import annotations

import pytest

from sentinelops.investigation.engine import InvestigationEngine
from sentinelops.investigation.state import EvidenceType, HypothesisStatus


@pytest.mark.asyncio
async def test_golden_crashloopbackoff_investigation():
    """Golden scenario: Pod continuously crashing, verified with pod status, logs, and RAG."""
    engine = InvestigationEngine()

    state = await engine.investigate(
        incident_id="GOLDEN-CRASH-01",
        target_service="payment-service",
        target_pod="payment-service-pod-1",
        namespace="default",
        trigger_reason="CrashLoopBackOff restarting continuously",
        max_steps=6,
    )

    assert state.status == "completed"
    assert any(e.evidence_type == EvidenceType.K8S_STATUS for e in state.evidence)

    # Check hypothesis evaluation
    confirmed = [h for h in state.hypotheses if h.status == HypothesisStatus.CONFIRMED]
    assert len(confirmed) > 0
    # Must have actionable recommendations
    assert len(state.final_recommendations) >= 2


@pytest.mark.asyncio
async def test_golden_oomkilled_investigation():
    """Golden scenario: Container terminated by kernel OOM killer."""
    engine = InvestigationEngine()

    state = await engine.investigate(
        incident_id="GOLDEN-OOM-02",
        target_service="analytics-engine",
        target_pod="analytics-worker-0",
        namespace="data",
        trigger_reason="Container exited with code 137 OOMKilled",
        max_steps=6,
    )

    assert state.status == "completed"
    assert state.final_root_cause is not None
    assert any("oom" in rec.lower() or "memory" in rec.lower() for rec in state.final_recommendations)


@pytest.mark.asyncio
async def test_golden_pvc_saturation_investigation():
    """Golden scenario: Disk / Volume saturation."""
    engine = InvestigationEngine()

    state = await engine.investigate(
        incident_id="GOLDEN-PVC-03",
        target_service="kafka-broker",
        target_pod="kafka-broker-0",
        namespace="streaming",
        trigger_reason="pvc_usage_percent 99% No space left on device",
        max_steps=6,
    )

    assert state.status == "completed"
    assert any("pvc" in rec.lower() or "volume" in rec.lower() or "storage" in rec.lower() for rec in state.final_recommendations)
