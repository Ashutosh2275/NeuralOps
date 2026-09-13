from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sentinelops.core.logging import get_logger
from sentinelops.engines.dependency import DependencyIntelligenceEngine
from sentinelops.events.schemas import BaseEvent, IncidentEvent, Severity

log = get_logger(__name__)


@dataclass
class RCAResult:
    root_cause: str
    root_service: str
    origin_pod: str | None
    confidence: float
    cascade_chain: list[dict[str, Any]]
    blast_radius: dict[str, Any]
    evidence: list[str]
    timeline: list[dict[str, Any]] = field(default_factory=list)
    propagation_chain: list[str] = field(default_factory=list)
    report: dict[str, Any] = field(default_factory=dict)


class RCAEngine:
    """Deterministic root-cause analysis with dependency traversal and causal scoring."""

    def __init__(self, dependency: DependencyIntelligenceEngine | None = None) -> None:
        self._dependency = dependency or DependencyIntelligenceEngine()

    def analyze(
        self,
        events: list[BaseEvent],
        cascade_chain: list[dict[str, Any]] | None = None,
        dependency_engine: DependencyIntelligenceEngine | None = None,
    ) -> RCAResult:
        dep = dependency_engine or self._dependency
        if not events:
            return self._empty_result()

        timeline = self._reconstruct_timeline(events)
        scored = [(e, self._causal_score(e, events)) for e in events]
        scored.sort(key=lambda x: x[1], reverse=True)
        top_event, top_score = scored[0]

        origin_pod = top_event.payload.get("pod_name")
        root_service = self._extract_service(top_event)
        root_cause = self._build_cause_description(top_event, scored[:3])

        ns = top_event.namespace
        root_id = dep.node_id(ns, "Pod", origin_pod) if origin_pod else None
        if root_id and root_id in dep._graph:
            dep.mark_unhealthy(root_id)
            cascade = dep.find_cascade_path(root_id)
            blast = dep.blast_radius(root_id)
        else:
            cascade = cascade_chain or []
            blast = {"affected_nodes": [], "affected_count": 0}

        propagation = [c.get("service", "") for c in cascade if c.get("service")]
        evidence = [
            f"[{e.severity.value}] {e.event_type.value}: {e.payload.get('reason', e.payload.get('anomaly_type', e.source))}"
            for e, _ in scored[:8]
        ]

        confidence = min(1.0, top_score + 0.1 * len(cascade) + 0.05 * blast.get("affected_count", 0))

        report = {
            "summary": root_cause,
            "origin": {"pod": origin_pod, "service": root_service, "namespace": ns},
            "confidence": round(confidence, 3),
            "blast_radius": blast,
            "cascade_chain": cascade,
            "timeline_entries": len(timeline),
            "evidence_count": len(evidence),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return RCAResult(
            root_cause=root_cause,
            root_service=root_service,
            origin_pod=origin_pod,
            confidence=confidence,
            cascade_chain=cascade,
            blast_radius=blast if isinstance(blast, dict) else blast.__dict__,
            evidence=evidence,
            timeline=timeline,
            propagation_chain=propagation,
            report=report,
        )

    def _causal_score(self, event: BaseEvent, all_events: list[BaseEvent]) -> float:
        score = 0.25
        if event.severity in (Severity.ERROR, Severity.CRITICAL):
            score += 0.25
        if event.event_type.value == "pod":
            restarts = event.payload.get("restart_count", 0)
            if restarts >= 3:
                score += 0.3
            elif event.payload.get("phase") in ("Failed", "CrashLoopBackOff"):
                score += 0.25
        if event.event_type.value == "metric" and event.payload.get("breached"):
            score += 0.2
        if event.event_type.value == "anomaly":
            score += 0.15
        if event.event_type.value == "log":
            score += 0.1
        earlier = sum(1 for e in all_events if e.timestamp < event.timestamp and e.severity.value in ("error", "critical"))
        if earlier == 0 and event.severity.value in ("error", "critical"):
            score += 0.15
        return min(score, 1.0)

    def _reconstruct_timeline(self, events: list[BaseEvent]) -> list[dict[str, Any]]:
        return sorted(
            [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type.value,
                    "severity": e.severity.value,
                    "resource": e.payload.get("pod_name") or e.payload.get("service_name"),
                    "detail": e.payload.get("reason") or e.payload.get("metric_name") or e.source,
                }
                for e in events
            ],
            key=lambda x: x["timestamp"],
        )

    def _extract_service(self, event: BaseEvent) -> str:
        return (
            event.payload.get("service_name")
            or event.payload.get("pod_name")
            or event.labels.get("app", "unknown")
        )

    def _build_cause_description(self, event: BaseEvent, top_scored: list[tuple[BaseEvent, float]]) -> str:
        primary = self._describe_event(event)
        contributors = [self._describe_event(e) for e, _ in top_scored[1:3]]
        if contributors:
            return f"{primary}. Contributing factors: {'; '.join(contributors)}"
        return primary

    def _describe_event(self, event: BaseEvent) -> str:
        etype = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        pod_target = (
            event.payload.get("pod_name")
            or event.payload.get("pod")
            or event.payload.get("service_name")
            or event.payload.get("service")
            or event.labels.get("app")
            or "workload"
        )
        if etype == "pod":
            phase = event.payload.get("phase") or "Unknown"
            reason = event.payload.get("reason") or "unspecified disturbance"
            return f"Pod {pod_target} ({phase}) — {reason}"
        if etype == "metric":
            metric_name = (
                event.payload.get("metric_name")
                or event.payload.get("metric")
                or event.payload.get("name")
                or "Resource usage"
            )
            val = event.payload.get("metric_value") or event.payload.get("value")
            val_str = f"{val}%" if isinstance(val, (int, float)) and val <= 100 else str(val) if val is not None else "high"
            return f"{metric_name}={val_str} threshold exceeded on {pod_target}"
        if etype == "anomaly":
            atype = event.payload.get("anomaly_type") or "Resource saturation"
            return f"Anomaly {atype} on {pod_target}"
        if etype == "log":
            ltype = event.payload.get("anomaly_type") or "error"
            line = str(event.payload.get("log_line") or event.payload.get("message") or "")[:80]
            return f"Log pattern: {ltype} — {line}"
        return f"{etype} from {event.source or pod_target}"

    def enrich_incident(self, incident: IncidentEvent, result: RCAResult) -> IncidentEvent:
        incident.payload["root_cause"] = result.root_cause
        incident.payload["confidence_score"] = result.confidence
        incident.payload["cascade_chain"] = result.cascade_chain
        incident.payload["blast_radius"] = result.blast_radius
        incident.payload["rca_report"] = result.report
        incident.payload["origin_pod"] = result.origin_pod
        return incident

    def _empty_result(self) -> RCAResult:
        return RCAResult(
            root_cause="Insufficient evidence",
            root_service="unknown",
            origin_pod=None,
            confidence=0.0,
            cascade_chain=[],
            blast_radius={},
            evidence=[],
        )
