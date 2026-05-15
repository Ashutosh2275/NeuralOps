import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent, IncidentEvent, Severity
from sentinelops.models.incident import Incident, IncidentTimeline

log = get_logger(__name__)


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_from_event(self, event: IncidentEvent, cluster_id: UUID) -> Incident:
        incident = Incident(
            id=event.incident_id or uuid4(),
            cluster_id=cluster_id,
            title=event.payload.get("title", "Untitled incident"),
            status=event.payload.get("status", "open"),
            severity=event.severity.value,
            affected_services_json=json.dumps(event.payload.get("affected_services", [])),
            cascade_chain_json=json.dumps(event.payload.get("cascade_chain", [])),
            confidence_score=event.payload.get("confidence_score"),
            started_at=event.timestamp,
        )
        self._session.add(incident)
        await self._add_timeline(incident.id, "incident_created", event.payload.get("title", ""), event)
        await self._session.flush()
        log.info("incident_created", incident_id=str(incident.id))
        return incident

    async def get(self, incident_id: UUID) -> Incident | None:
        result = await self._session.execute(select(Incident).where(Incident.id == incident_id))
        return result.scalar_one_or_none()

    async def list_open(self, limit: int = 50) -> list[Incident]:
        result = await self._session.execute(
            select(Incident).where(Incident.status.in_(("open", "investigating"))).limit(limit)
        )
        return list(result.scalars().all())

    async def update_rca(
        self,
        incident_id: UUID,
        root_cause: str,
        root_service: str,
        confidence: float,
        cascade_chain: list[dict],
    ) -> Incident | None:
        incident = await self.get(incident_id)
        if not incident:
            return None
        incident.root_cause = root_cause
        incident.root_service = root_service
        incident.confidence_score = confidence
        incident.cascade_chain_json = json.dumps(cascade_chain)
        incident.status = "investigating"
        await self._add_timeline(incident_id, "rca_completed", root_cause, None, severity="info")
        await self._session.flush()
        return incident

    async def _add_timeline(
        self,
        incident_id: UUID,
        event_type: str,
        title: str,
        source_event: BaseEvent | None,
        severity: str = "info",
    ) -> None:
        entry = IncidentTimeline(
            id=uuid4(),
            incident_id=incident_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            title=title,
            description=source_event.payload.get("root_cause") if source_event else None,
            source=source_event.source if source_event else "system",
            severity=severity,
        )
        self._session.add(entry)
