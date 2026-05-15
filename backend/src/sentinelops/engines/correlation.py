from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sentinelops.config import Settings, get_settings
from sentinelops.core.logging import get_logger
from sentinelops.engines.dependency import DependencyIntelligenceEngine
from sentinelops.events.schemas import BaseEvent, CorrelationEvent, EventType, IncidentEvent, Severity

log = get_logger(__name__)


@dataclass
class CorrelationCluster:
    correlation_id: UUID
    events: list[BaseEvent] = field(default_factory=list)
    trigger: str = "unknown"
    severity: Severity = Severity.WARNING
    affected_services: list[str] = field(default_factory=list)
    dependency_context: dict = field(default_factory=dict)
    confidence: float = 0.5


class CorrelationEngine:
    """Cross-resource, dependency-aware, temporal correlation intelligence."""

    def __init__(
        self,
        settings: Settings | None = None,
        dependency: DependencyIntelligenceEngine | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._window = timedelta(seconds=self._settings.ingestion_correlation_window_seconds)
        self._event_buffer: dict[str, list[BaseEvent]] = defaultdict(list)
        self._dependency = dependency or DependencyIntelligenceEngine()

    def _key(self, event: BaseEvent) -> str:
        svc = event.payload.get("service_name") or event.payload.get("pod_name") or "*"
        return f"{event.cluster_id}:{event.namespace}:{svc}"

    def ingest(self, event: BaseEvent, dependency_engine: DependencyIntelligenceEngine | None = None) -> list[CorrelationEvent]:
        if dependency_engine:
            self._dependency = dependency_engine
        key = self._key(event)
        now = event.timestamp
        self._event_buffer[key] = [
            e for e in self._event_buffer[key] if now - e.timestamp <= self._window
        ]
        self._event_buffer[key].append(event)
        cluster = self._build_cluster(key)
        if not cluster or len(cluster.events) < 2:
            return []
        return [self._to_correlation_event(cluster)]

    def _build_cluster(self, key: str) -> CorrelationCluster | None:
        events = self._event_buffer[key]
        if len(events) < 2:
            return None

        anomalies = [e for e in events if e.event_type == EventType.ANOMALY]
        pod_failures = [
            e for e in events
            if e.event_type == EventType.POD
            and e.payload.get("phase") in ("Failed", "CrashLoopBackOff")
        ]
        metric_breaches = [e for e in events if e.event_type == EventType.METRIC and e.payload.get("breached")]
        log_events = [e for e in events if e.event_type == EventType.LOG]
        storage_events = [
            e for e in events
            if "pvc" in str(e.payload).lower() or "disk" in e.payload.get("metric_name", "").lower()
        ]
        restart_events = [e for e in events if e.payload.get("restart_count", 0) >= 2]

        if not (anomalies or pod_failures or metric_breaches or log_events):
            return None

        trigger = self._determine_trigger(anomalies, pod_failures, metric_breaches, log_events, storage_events)
        severity = Severity.CRITICAL if (pod_failures or restart_events) else Severity.WARNING
        if metric_breaches and storage_events:
            severity = Severity.CRITICAL

        affected = list({
            e.payload.get("service_name") or e.payload.get("pod_name") or e.labels.get("app", "unknown")
            for e in events
            if e.payload.get("pod_name") or e.payload.get("service_name")
        })

        root_pod = None
        if pod_failures:
            root_pod = pod_failures[0].payload.get("pod_name")
        elif metric_breaches:
            root_pod = metric_breaches[0].payload.get("pod_name")

        dep_ctx: dict = {"affected_services": affected, "trigger": trigger}
        if root_pod:
            ns = events[0].namespace
            root_id = self._dependency.node_id(ns, "Pod", root_pod)
            from dataclasses import asdict
            dep_ctx["blast_radius"] = asdict(self._dependency.blast_radius(root_id))
            dep_ctx["cascade_path"] = self._dependency.find_cascade_path(root_id)

        confidence = min(1.0, 0.4 + 0.1 * len(events) + 0.15 * len(anomalies) + 0.2 * len(pod_failures))

        return CorrelationCluster(
            correlation_id=uuid4(),
            events=events[-50:],
            trigger=trigger,
            severity=severity,
            affected_services=[s for s in affected if s],
            dependency_context=dep_ctx,
            confidence=confidence,
        )

    def _to_correlation_event(self, cluster: CorrelationCluster) -> CorrelationEvent:
        return CorrelationEvent(
            event_id=uuid4(),
            source="correlation-engine",
            cluster_id=cluster.events[0].cluster_id,
            namespace=cluster.events[0].namespace,
            severity=cluster.severity,
            correlation_id=cluster.correlation_id,
            payload={
                "correlation_id": str(cluster.correlation_id),
                "related_event_ids": [str(e.event_id) for e in cluster.events],
                "trigger": cluster.trigger,
                "affected_services": cluster.affected_services,
                "dependency_context": cluster.dependency_context,
                "confidence_score": cluster.confidence,
                "anomaly_count": sum(1 for e in cluster.events if e.event_type == EventType.ANOMALY),
                "event_count": len(cluster.events),
            },
        )

    def _determine_trigger(
        self,
        anomalies: list[BaseEvent],
        pod_failures: list[BaseEvent],
        metric_breaches: list[BaseEvent],
        log_events: list[BaseEvent],
        storage_events: list[BaseEvent],
    ) -> str:
        if pod_failures and storage_events:
            return "pod_failure_with_storage_stress"
        if pod_failures:
            return "pod_failure"
        if metric_breaches and log_events:
            return "metric_log_correlation"
        if metric_breaches:
            return "metric_breach"
        if storage_events:
            return "storage_stress"
        if log_events:
            return "log_anomaly"
        if anomalies:
            return "anomaly_chain"
        return "unknown"

    def build_incident_from_correlation(
        self, correlation: CorrelationEvent, affected_services: list[str] | None = None
    ) -> IncidentEvent:
        services = affected_services or correlation.payload.get("affected_services", [])
        cascade = correlation.payload.get("dependency_context", {}).get("cascade_path", [])
        return IncidentEvent(
            event_id=uuid4(),
            source="correlation-engine",
            cluster_id=correlation.cluster_id,
            namespace=correlation.namespace,
            severity=Severity.ERROR,
            correlation_id=correlation.correlation_id,
            incident_id=uuid4(),
            payload={
                "incident_id": str(uuid4()),
                "title": f"Cascading failure in {correlation.namespace} — {correlation.payload.get('trigger')}",
                "status": "open",
                "affected_services": services,
                "cascade_chain": cascade,
                "confidence_score": correlation.payload.get("confidence_score", 0.6),
                "dependency_context": correlation.payload.get("dependency_context", {}),
            },
        )

    def reconstruct_anomaly_chain(self, events: list[BaseEvent]) -> list[dict]:
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        chain = []
        for i, e in enumerate(sorted_events):
            chain.append({
                "order": i,
                "timestamp": e.timestamp.isoformat(),
                "type": e.event_type.value,
                "severity": e.severity.value,
                "resource": e.payload.get("pod_name") or e.payload.get("service_name"),
                "detail": e.payload.get("anomaly_type") or e.payload.get("reason") or e.source,
            })
        return chain
