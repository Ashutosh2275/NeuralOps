import json
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.config import Settings, get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent
from sentinelops.models.intelligence import ReplayEvent, ReplayFrame

log = get_logger(__name__)


class ReplayEngine:
    """Incident replay with in-memory buffer and PostgreSQL persistence."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._buffer: dict[UUID, list[BaseEvent]] = {}
        self._topology_states: dict[UUID, list[dict]] = {}

    def buffer_event(self, incident_id: UUID, event: BaseEvent, topology_state: dict | None = None) -> None:
        if incident_id not in self._buffer:
            self._buffer[incident_id] = []
        events = self._buffer[incident_id]
        events.append(event)
        max_events = self._settings.replay_max_events_per_incident
        if len(events) > max_events:
            self._buffer[incident_id] = events[-max_events:]
        if topology_state:
            if incident_id not in self._topology_states:
                self._topology_states[incident_id] = []
            self._topology_states[incident_id].append(topology_state)

    async def persist_replay(
        self,
        session: AsyncSession,
        incident_id: UUID,
        topology_graph: dict | None = None,
    ) -> list[ReplayFrame]:
        events = self._buffer.get(incident_id, [])
        if not events:
            return []

        frames_data = self.build_replay_frames(incident_id)
        persisted: list[ReplayFrame] = []

        for idx, frame_data in enumerate(frames_data):
            topo = topology_graph if idx == len(frames_data) - 1 else None
            frame = ReplayFrame(
                id=UUID(frame_data["frame_id"]) if "frame_id" in frame_data else uuid4(),
                incident_id=incident_id,
                frame_index=idx,
                timestamp=datetime.fromisoformat(frame_data["timestamp"]),
                event_count=frame_data["event_count"],
                topology_state_json=json.dumps(topo) if topo else None,
                events_json=json.dumps(frame_data.get("events", [])),
            )
            session.add(frame)
            persisted.append(frame)

            for ev_data in frame_data.get("events", []):
                replay_ev = ReplayEvent(
                    id=uuid4(),
                    incident_id=incident_id,
                    frame_id=frame.id,
                    event_id=uuid4(),
                    event_type=ev_data.get("type", "unknown"),
                    severity=ev_data.get("severity", "info"),
                    source="replay",
                    payload_json=json.dumps(ev_data.get("payload", {})),
                    timestamp=frame.timestamp,
                )
                session.add(replay_ev)

        await session.flush()
        return persisted

    def get_timeline(
        self,
        incident_id: UUID,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict]:
        events = self._buffer.get(incident_id, [])
        if start:
            events = [e for e in events if e.timestamp >= start]
        if end:
            events = [e for e in events if e.timestamp <= end]
        events.sort(key=lambda e: e.timestamp)
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type.value,
                "severity": e.severity.value,
                "source": e.source,
                "namespace": e.namespace,
                "payload": e.payload,
                "event_id": str(e.event_id),
            }
            for e in events
        ]

    def build_replay_frames(
        self,
        incident_id: UUID,
        interval_seconds: int | None = None,
    ) -> list[dict]:
        interval = interval_seconds or self._settings.replay_snapshot_interval_seconds
        events = self._buffer.get(incident_id, [])
        if not events:
            return await_db_frames_placeholder(incident_id)

        events.sort(key=lambda e: e.timestamp)
        start = events[0].timestamp
        end = events[-1].timestamp
        frames: list[dict] = []
        current = start
        idx = 0
        topo_states = self._topology_states.get(incident_id, [])

        while current <= end:
            frame_events = []
            while idx < len(events) and events[idx].timestamp <= current:
                frame_events.append(events[idx])
                idx += 1
            topo_idx = min(len(topo_states) - 1, len(frames)) if topo_states else -1
            frames.append({
                "frame_id": str(uuid4()),
                "frame_index": len(frames),
                "timestamp": current.isoformat(),
                "event_count": len(frame_events),
                "topology_state": topo_states[topo_idx] if topo_idx >= 0 else None,
                "events": [
                    {
                        "type": e.event_type.value,
                        "severity": e.severity.value,
                        "source": e.source,
                        "payload": e.payload,
                    }
                    for e in frame_events
                ],
            })
            current += timedelta(seconds=interval)
        return frames

    async def load_from_db(self, session: AsyncSession, incident_id: UUID) -> dict:
        result = await session.execute(
            select(ReplayFrame)
            .where(ReplayFrame.incident_id == incident_id)
            .order_by(ReplayFrame.frame_index)
        )
        frames = result.scalars().all()
        timeline_result = await session.execute(
            select(ReplayEvent)
            .where(ReplayEvent.incident_id == incident_id)
            .order_by(ReplayEvent.timestamp)
        )
        events = timeline_result.scalars().all()
        return {
            "frames": [
                {
                    "frame_id": str(f.id),
                    "frame_index": f.frame_index,
                    "timestamp": f.timestamp.isoformat(),
                    "event_count": f.event_count,
                    "topology_state": json.loads(f.topology_state_json) if f.topology_state_json else None,
                    "events": json.loads(f.events_json) if f.events_json else [],
                }
                for f in frames
            ],
            "timeline": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "payload": json.loads(e.payload_json) if e.payload_json else {},
                }
                for e in events
            ],
        }


def await_db_frames_placeholder(incident_id: UUID) -> list[dict]:
    return []
