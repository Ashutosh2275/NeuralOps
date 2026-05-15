from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sentinelops.pipeline.normalized_event import NormalizedEvent


class CorrelationMetadataLayer:
    """Attaches correlation_id and trace grouping across related events."""

    def __init__(self, window_seconds: int = 120) -> None:
        self._window = timedelta(seconds=window_seconds)
        self._groups: dict[str, list[tuple[datetime, UUID]]] = defaultdict(list)

    def _group_key(self, event: NormalizedEvent) -> str:
        return f"{event.cluster_id}:{event.namespace}:{event.service_name or event.pod_name or '*'}"

    def enrich(self, event: NormalizedEvent) -> NormalizedEvent:
        key = self._group_key(event)
        now = event.timestamp
        self._groups[key] = [(ts, cid) for ts, cid in self._groups[key] if now - ts <= self._window]

        if event.correlation_id:
            self._groups[key].append((now, event.correlation_id))
            return event

        if self._groups[key]:
            event.correlation_id = self._groups[key][-1][1]
        else:
            cid = uuid4()
            event.correlation_id = cid
            self._groups[key].append((now, cid))

        if not event.trace_id:
            event.trace_id = str(event.correlation_id)

        event.replay_metadata.setdefault("correlation_group", key)
        event.replay_metadata["correlated_at"] = now.isoformat()
        return event

    def enrich_batch(self, events: list[NormalizedEvent]) -> list[NormalizedEvent]:
        return [self.enrich(e) for e in events]
