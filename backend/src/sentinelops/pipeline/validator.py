from sentinelops.core.logging import get_logger
from sentinelops.pipeline.normalized_event import NormalizedEvent

log = get_logger(__name__)

REQUIRED_FIELDS = ("event_id", "event_type", "source", "timestamp", "namespace", "severity")


class EventValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class EventValidationPipeline:
    """Validates normalized events before stream publish."""

    def validate(self, event: NormalizedEvent) -> NormalizedEvent:
        errors: list[str] = []
        if not event.source:
            errors.append("source is required")
        if not event.namespace:
            errors.append("namespace is required")
        if event.metric_name and event.metric_value is None and event.event_type.value == "metric":
            errors.append("metric_value required when metric_name is set")
        if event.event_type.value == "pod" and not event.pod_name:
            errors.append("pod_name required for pod events")
        if event.event_type.value == "log" and not event.payload.get("log_line"):
            errors.append("log_line required for log events")

        if errors:
            log.warning("event_validation_failed", event_id=str(event.event_id), errors=errors)
            raise EventValidationError(errors)
        return event

    def validate_batch(self, events: list[NormalizedEvent]) -> list[NormalizedEvent]:
        valid: list[NormalizedEvent] = []
        for event in events:
            try:
                valid.append(self.validate(event))
            except EventValidationError:
                continue
        return valid
