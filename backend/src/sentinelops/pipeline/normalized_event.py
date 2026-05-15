import json
from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from sentinelops.events.schemas import EventType, Severity


def _json_dumps(obj: dict[str, Any]) -> str:
    def _default(o: object) -> str:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, default=_default)


class StreamKind(StrEnum):
    METRICS = "metrics.events"
    TOPOLOGY = "topology.events"
    ANOMALY = "anomaly.events"
    INCIDENT = "incident.events"
    RCA = "rca.events"
    RAW = "so:events:raw"


class NormalizedEvent(BaseModel):
    """Unified production-grade event schema for all ingestion sources."""

    trace_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: UUID | None = None
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    event_type: EventType
    source: str
    cluster_id: str = "default"
    namespace: str = "default"

    pod_name: str | None = None
    service_name: str | None = None
    node_name: str | None = None

    metric_name: str | None = None
    metric_value: float | None = None
    metric_unit: str | None = None

    severity: Severity = Severity.INFO
    stream_kind: StreamKind = StreamKind.RAW

    topology_context: dict[str, Any] = Field(default_factory=dict)
    dependency_context: dict[str, Any] = Field(default_factory=dict)
    replay_metadata: dict[str, Any] = Field(default_factory=dict)
    incident_metadata: dict[str, Any] = Field(default_factory=dict)

    labels: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    incident_id: UUID | None = None

    def to_stream_fields(self) -> dict[str, str]:
        return {
            "trace_id": self.trace_id,
            "correlation_id": str(self.correlation_id) if self.correlation_id else "",
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "source": self.source,
            "cluster_id": self.cluster_id,
            "namespace": self.namespace,
            "pod_name": self.pod_name or "",
            "service_name": self.service_name or "",
            "node_name": self.node_name or "",
            "metric_name": self.metric_name or "",
            "metric_value": str(self.metric_value) if self.metric_value is not None else "",
            "metric_unit": self.metric_unit or "",
            "severity": self.severity.value,
            "stream_kind": self.stream_kind.value,
            "topology_context": _json_dumps(self.topology_context),
            "dependency_context": _json_dumps(self.dependency_context),
            "replay_metadata": _json_dumps(self.replay_metadata),
            "incident_metadata": _json_dumps(self.incident_metadata),
            "labels": _json_dumps(self.labels),
            "payload": _json_dumps(self.payload),
            "incident_id": str(self.incident_id) if self.incident_id else "",
        }

    @classmethod
    def from_stream_fields(cls, fields: dict[str, str]) -> "NormalizedEvent":
        def _json(key: str) -> dict[str, Any]:
            raw = fields.get(key, "{}")
            return json.loads(raw) if raw else {}

        return cls(
            trace_id=fields.get("trace_id") or str(uuid4()),
            correlation_id=UUID(fields["correlation_id"]) if fields.get("correlation_id") else None,
            event_id=UUID(fields["event_id"]),
            timestamp=datetime.fromisoformat(fields["timestamp"]),
            event_type=EventType(fields["event_type"]),
            source=fields["source"],
            cluster_id=fields.get("cluster_id", "default"),
            namespace=fields.get("namespace", "default"),
            pod_name=fields.get("pod_name") or None,
            service_name=fields.get("service_name") or None,
            node_name=fields.get("node_name") or None,
            metric_name=fields.get("metric_name") or None,
            metric_value=float(fields["metric_value"]) if fields.get("metric_value") else None,
            metric_unit=fields.get("metric_unit") or None,
            severity=Severity(fields.get("severity", "info")),
            stream_kind=StreamKind(fields.get("stream_kind", StreamKind.RAW.value)),
            topology_context=_json("topology_context"),
            dependency_context=_json("dependency_context"),
            replay_metadata=_json("replay_metadata"),
            incident_metadata=_json("incident_metadata"),
            labels=_json("labels"),
            payload=_json("payload"),
            incident_id=UUID(fields["incident_id"]) if fields.get("incident_id") else None,
        )

    def to_base_event(self) -> "BaseEvent":
        from sentinelops.events.schemas import BaseEvent

        return BaseEvent(
            event_id=self.event_id,
            event_type=self.event_type,
            source=self.source,
            timestamp=self.timestamp,
            cluster_id=self.cluster_id,
            namespace=self.namespace,
            severity=self.severity,
            labels=self.labels,
            payload={
                **self.payload,
                "pod_name": self.pod_name,
                "service_name": self.service_name,
                "metric_name": self.metric_name,
                "metric_value": self.metric_value,
                "node_name": self.node_name,
            },
            correlation_id=self.correlation_id,
            incident_id=self.incident_id,
            trace_id=self.trace_id,
        )
