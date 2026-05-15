from typing import Any
from uuid import uuid4

from sentinelops.events.schemas import BaseEvent, EventType
from sentinelops.pipeline.normalized_event import NormalizedEvent, StreamKind


class EventNormalizer:
    """Converts collector output into unified NormalizedEvent instances."""

    def normalize(
        self,
        raw: dict[str, Any],
        *,
        event_type: EventType,
        source: str,
        stream_kind: StreamKind,
        trace_id: str | None = None,
    ) -> NormalizedEvent:
        namespace = raw.get("namespace", "default")
        pod_name = raw.get("pod_name") or raw.get("pod")
        service_name = (
            raw.get("service_name")
            or raw.get("service")
            or (raw.get("labels", {}) or {}).get("app")
        )

        return NormalizedEvent(
            trace_id=trace_id or raw.get("trace_id") or str(uuid4()),
            correlation_id=raw.get("correlation_id"),
            event_id=raw.get("event_id", uuid4()),
            timestamp=raw.get("timestamp"),
            event_type=event_type,
            source=source,
            cluster_id=raw.get("cluster_id", "default"),
            namespace=namespace,
            pod_name=pod_name,
            service_name=service_name,
            node_name=raw.get("node_name"),
            metric_name=raw.get("metric_name"),
            metric_value=raw.get("metric_value") if raw.get("metric_value") is not None else raw.get("value"),
            metric_unit=raw.get("metric_unit") or raw.get("unit"),
            stream_kind=stream_kind,
            topology_context=raw.get("topology_context", {}),
            dependency_context=raw.get("dependency_context", {}),
            replay_metadata=raw.get("replay_metadata", {}),
            incident_metadata=raw.get("incident_metadata", {}),
            labels=raw.get("labels", {}),
            payload={k: v for k, v in raw.items() if k not in ("topology_context", "dependency_context")},
        )

    def from_base_event(self, event: BaseEvent, stream_kind: StreamKind) -> NormalizedEvent:
        payload = event.payload
        return NormalizedEvent(
            trace_id=event.trace_id or str(uuid4()),
            correlation_id=event.correlation_id,
            event_id=event.event_id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            source=event.source,
            cluster_id=event.cluster_id,
            namespace=event.namespace,
            pod_name=payload.get("pod_name"),
            service_name=payload.get("service_name") or event.labels.get("app"),
            node_name=payload.get("node_name"),
            metric_name=payload.get("metric_name"),
            metric_value=payload.get("value") or payload.get("metric_value"),
            metric_unit=payload.get("unit"),
            stream_kind=stream_kind,
            labels=event.labels,
            payload=payload,
            incident_id=event.incident_id,
        )
