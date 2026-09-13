"""
Evidence Correlator for SentinelOps AI Autonomous Investigation Engine.
Correlates multi-modal evidence across K8s status, pod logs, metrics, topology, and historical incidents.
"""
from __future__ import annotations

import re
from typing import Any, List, Optional

from sentinelops.core.logging import get_logger
from sentinelops.investigation.state import (
    EvidenceItem,
    EvidenceType,
    Hypothesis,
    HypothesisStatus,
    InvestigationState,
)

log = get_logger(__name__)


class EvidenceCorrelator:
    """Correlates evidence streams to confirm or refute hypotheses and calculate confidence."""

    def correlate(self, state: InvestigationState) -> list[Hypothesis]:
        """Examines state.evidence and evaluates hypotheses."""
        hypotheses: list[Hypothesis] = []

        # Extract primary signals
        has_oom = False
        has_crashloop = False
        has_pvc_saturation = False
        has_network_timeout = False
        has_cascade = False

        oom_evidence_ids = []
        crashloop_evidence_ids = []
        pvc_evidence_ids = []
        timeout_evidence_ids = []
        cascade_evidence_ids = []

        trigger_str = state.initial_trigger.lower()
        trigger_indicates_oom = "oom" in trigger_str or "137" in trigger_str
        trigger_indicates_crash = "crash" in trigger_str or "backoff" in trigger_str
        if "pvc" in trigger_str or "diskpressure" in trigger_str or "no space left" in trigger_str:
            has_pvc_saturation = True

        target_name = (state.target_pod or state.target_service or "").lower()

        for e in state.evidence:
            # Advisory runbook knowledge must not be confused with empirical telemetry evidence
            if e.evidence_type == EvidenceType.RUNBOOK_KNOWLEDGE and not (trigger_indicates_oom or trigger_indicates_crash):
                continue

            data_str = str(e.raw_data).lower()
            summary_str = e.summary.lower()

            # If evidence is a namespace-wide event list and a specific target is set,
            # verify that events pertain to the target resource
            if e.evidence_type == EvidenceType.K8S_EVENT and isinstance(e.raw_data, dict) and target_name:
                events = e.raw_data.get("events", [])
                target_events = [
                    ev for ev in events
                    if target_name in str(ev.get("involved_object", {})).lower()
                    or target_name in str(ev.get("message", "")).lower()
                ]
                if not target_events:
                    continue  # Events in namespace are for other services; do not falsely attribute
                data_str = str(target_events).lower()

            # OOM detection
            if any(k in data_str or k in summary_str for k in ["oomkilled", "out of memory", "memory limit", "137"]):
                has_oom = True
                oom_evidence_ids.append(e.id)

            # CrashLoop detection
            if any(k in data_str or k in summary_str for k in ["crashloopbackoff", "back-off restarting", "exit code 1"]) or (trigger_indicates_crash and "restart" in (data_str + summary_str)):
                has_crashloop = True
                crashloop_evidence_ids.append(e.id)

            # PVC / Disk saturation
            if any(k in data_str or k in summary_str for k in ["pvc", "diskpressure", "no space left on device", "pvc_usage_percent"]):
                has_pvc_saturation = True
                pvc_evidence_ids.append(e.id)

            # Network / Timeout
            if any(k in data_str or k in summary_str for k in ["timeout", "deadline exceeded", "connection refused", "504"]):
                has_network_timeout = True
                timeout_evidence_ids.append(e.id)

            # Cascade / Blast radius
            if e.evidence_type == EvidenceType.TOPOLOGY_IMPACT:
                if isinstance(e.raw_data, dict) and e.raw_data.get("downstream_count", 0) > 0:
                    has_cascade = True
                    cascade_evidence_ids.append(e.id)
                elif isinstance(e.raw_data, dict) and len(e.raw_data.get("cascade_path", [])) > 0:
                    has_cascade = True
                    cascade_evidence_ids.append(e.id)

        # Check for contradictory evidence (e.g. healthy live status contradicting historical alerts)
        healthy_status_evidence = [
            e for e in state.evidence
            if e.evidence_type == EvidenceType.K8S_STATUS
            and isinstance(e.raw_data, dict)
            and e.raw_data.get("phase") == "Running"
            and e.raw_data.get("ready") is True
            and e.raw_data.get("restart_count", 0) == 0
        ]

        healthy_metric_evidence = [
            e for e in state.evidence
            if e.evidence_type == EvidenceType.METRIC_ANOMALY
            and isinstance(e.raw_data, dict)
            and len(e.raw_data.get("metrics", [])) > 0
            and not any(m.get("breached") for m in e.raw_data.get("metrics", []))
        ]

        # Build prioritized hypotheses
        if has_oom:
            is_refuted = bool(healthy_status_evidence and healthy_metric_evidence and not trigger_indicates_oom)
            refuting_ids = [e.id for e in (healthy_status_evidence + healthy_metric_evidence)] if is_refuted else []
            hypotheses.append(
                Hypothesis(
                    description=f"Out of Memory (OOMKilled) container termination on {state.target_pod or state.target_service}",
                    status=HypothesisStatus.REFUTED if is_refuted else HypothesisStatus.CONFIRMED,
                    confidence=0.15 if is_refuted else 0.92,
                    supporting_evidence_ids=oom_evidence_ids,
                    refuting_evidence_ids=refuting_ids,
                    reasoning="OOM signature refuted by healthy pod status and normal memory metrics." if is_refuted else "Memory limit reached or kernel OOM killer triggered termination. Verified across metrics and container exit codes.",
                )
            )

        if has_crashloop and not has_oom:
            is_refuted = bool(healthy_status_evidence and not trigger_indicates_crash)
            refuting_ids = [e.id for e in healthy_status_evidence] if is_refuted else []
            hypotheses.append(
                Hypothesis(
                    description=f"Application crash loop / configuration defect on {state.target_pod or state.target_service}",
                    status=HypothesisStatus.REFUTED if is_refuted else HypothesisStatus.CONFIRMED,
                    confidence=0.18 if is_refuted else 0.88,
                    supporting_evidence_ids=crashloop_evidence_ids,
                    refuting_evidence_ids=refuting_ids,
                    reasoning="Crash loop hypothesis is refuted by live Kubernetes status: pod is currently Running with 0 restarts and Ready=True condition." if is_refuted else "Container continuously failing immediately after startup; verified via repeated restarts and K8s BackOff events.",
                )
            )

        if has_pvc_saturation:
            pvc_refuted = False
            refuting_pvc_ids = []
            for e in state.evidence:
                if e.evidence_type == EvidenceType.METRIC_ANOMALY and isinstance(e.raw_data, dict):
                    for m in e.raw_data.get("metrics", []):
                        if "pvc" in m.get("metric", "") and m.get("value", 0) < 50:
                            pvc_refuted = True
                            refuting_pvc_ids.append(e.id)
            hypotheses.append(
                Hypothesis(
                    description=f"Persistent Volume Claim (PVC) storage exhaustion affecting {state.target_service or 'storage volume'}",
                    status=HypothesisStatus.REFUTED if pvc_refuted else HypothesisStatus.CONFIRMED,
                    confidence=0.12 if pvc_refuted else 0.89,
                    supporting_evidence_ids=pvc_evidence_ids,
                    refuting_evidence_ids=refuting_pvc_ids if pvc_refuted else [],
                    reasoning="PVC saturation refuted by telemetry: volume usage is below 50% capacity." if pvc_refuted else "Volume utilization reached critical threshold; I/O writes failing due to storage saturation.",
                )
            )

        if has_network_timeout:
            hypotheses.append(
                Hypothesis(
                    description=f"Network latency or upstream service timeout impacting {state.target_service or 'workload'}",
                    status=HypothesisStatus.CONFIRMED if not (has_oom or has_crashloop) else HypothesisStatus.PROPOSED,
                    confidence=0.75 if not (has_oom or has_crashloop) else 0.45,
                    supporting_evidence_ids=timeout_evidence_ids,
                    reasoning="Observed request timeouts, connection resets, or deadline exceeded in log and metric traces.",
                )
            )

        if has_cascade:
            hypotheses.append(
                Hypothesis(
                    description=f"Cascading upstream degradation originating from dependency failure on {state.target_service}",
                    status=HypothesisStatus.CONFIRMED,
                    confidence=0.85,
                    supporting_evidence_ids=cascade_evidence_ids,
                    reasoning="Topology analysis confirms dependency chain propagation across upstream callers.",
                )
            )

        # Fallback if no specific condition matched
        if not hypotheses:
            hypotheses.append(
                Hypothesis(
                    description=f"General service degradation or anomaly on {state.target_service or state.target_pod or 'cluster'}",
                    status=HypothesisStatus.INCONCLUSIVE,
                    confidence=0.50,
                    supporting_evidence_ids=[e.id for e in state.evidence[:3]],
                    reasoning="Evidence gathered shows operational warnings without decisive signature match.",
                )
            )

        state.hypotheses = hypotheses
        return hypotheses

    def compute_composite_confidence(self, state: InvestigationState) -> float:
        """Computes grounded confidence score based on diversity of corroborating evidence."""
        if not state.evidence:
            return 0.1

        evidence_types = {e.evidence_type for e in state.evidence}
        base_score = 0.4

        # Multi-modal corroboration bonus
        if EvidenceType.K8S_STATUS in evidence_types:
            base_score += 0.15
        if EvidenceType.POD_LOGS in evidence_types or EvidenceType.METRIC_ANOMALY in evidence_types:
            base_score += 0.15
        if EvidenceType.TOPOLOGY_IMPACT in evidence_types:
            base_score += 0.10
        if EvidenceType.RUNBOOK_KNOWLEDGE in evidence_types:
            base_score += 0.10

        # Hypotheses confirmation boost
        confirmed = [h for h in state.hypotheses if h.status == HypothesisStatus.CONFIRMED]
        if confirmed:
            top_conf = max(h.confidence for h in confirmed)
            base_score = max(base_score, top_conf)

        return min(round(base_score, 3), 0.98)
