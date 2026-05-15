import json
from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _json_dumps(obj: dict[str, Any]) -> str:
    def _default(o: object) -> str:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, default=_default)


class EventType(StrEnum):
    POD = "pod"
    METRIC = "metric"
    LOG = "log"
    TOPOLOGY = "topology"
    INCIDENT = "incident"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    AI_RESULT = "ai_result"


class Severity(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BaseEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    cluster_id: str = "default"
    namespace: str = "default"
    severity: Severity = Severity.INFO
    labels: dict[str, str] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID | None = None
    incident_id: UUID | None = None
    trace_id: str | None = None

    def to_stream_fields(self) -> dict[str, str]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "cluster_id": self.cluster_id,
            "namespace": self.namespace,
            "severity": self.severity.value,
            "labels": _json_dumps(self.labels),
            "payload": _json_dumps(self.payload),
            "correlation_id": str(self.correlation_id) if self.correlation_id else "",
            "incident_id": str(self.incident_id) if self.incident_id else "",
            "trace_id": self.trace_id or "",
        }

    @classmethod
    def _parse_json_dict(cls, raw: str) -> dict[str, Any]:
        import json

        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            return {}
        # Legacy streams stored model_dump_json(include={"labels"}) → {"labels": {...}}
        if len(data) == 1 and isinstance(next(iter(data.values())), dict):
            inner = next(iter(data.values()))
            if isinstance(inner, dict):
                return inner
        return data

    @classmethod
    def from_stream_fields(cls, fields: dict[str, str]) -> "BaseEvent":
        return cls(
            event_id=UUID(fields["event_id"]),
            event_type=EventType(fields["event_type"]),
            source=fields["source"],
            timestamp=datetime.fromisoformat(fields["timestamp"]),
            cluster_id=fields["cluster_id"],
            namespace=fields["namespace"],
            severity=Severity(fields["severity"]),
            labels=cls._parse_json_dict(fields.get("labels", "{}")),
            payload=cls._parse_json_dict(fields.get("payload", "{}")),
            correlation_id=UUID(fields["correlation_id"]) if fields.get("correlation_id") else None,
            incident_id=UUID(fields["incident_id"]) if fields.get("incident_id") else None,
            trace_id=fields.get("trace_id") or None,
        )


class PodEvent(BaseEvent):
    event_type: EventType = EventType.POD


class MetricEvent(BaseEvent):
    event_type: EventType = EventType.METRIC


class AnomalyEvent(BaseEvent):
    event_type: EventType = EventType.ANOMALY


class CorrelationEvent(BaseEvent):
    event_type: EventType = EventType.CORRELATION


class IncidentEvent(BaseEvent):
    event_type: EventType = EventType.INCIDENT


class TopologyEvent(BaseEvent):
    event_type: EventType = EventType.TOPOLOGY


class AIResultEvent(BaseEvent):
    event_type: EventType = EventType.AI_RESULT
