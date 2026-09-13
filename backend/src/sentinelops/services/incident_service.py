import json
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent, IncidentEvent, Severity
from sentinelops.models.incident import Incident, IncidentTimeline

log = get_logger(__name__)


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_from_event(self, event: IncidentEvent, cluster_id: UUID) -> Incident:
        title = event.payload.get("title", "Untitled incident")
        root_service = event.payload.get("root_service")

        # Deduplication: do not create redundant active incident if an open/investigating/acknowledged incident with same title exists
        existing_res = await self._session.execute(
            select(Incident)
            .where(
                Incident.cluster_id == cluster_id,
                Incident.status.in_(("open", "investigating", "acknowledged")),
                Incident.title == title,
            )
            .order_by(Incident.started_at.desc())
            .limit(1)
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            await self._add_timeline(existing.id, "telemetry_update", f"Correlated event update: {title}", event)
            await self._session.flush()
            log.info("incident_deduplicated", incident_id=str(existing.id), title=title)
            return existing

        incident = Incident(
            id=event.incident_id or uuid4(),
            cluster_id=cluster_id,
            title=title,
            status=event.payload.get("status", "open"),
            severity=event.severity.value,
            affected_services_json=json.dumps(event.payload.get("affected_services", [])),
            cascade_chain_json=json.dumps(event.payload.get("cascade_chain", [])),
            confidence_score=event.payload.get("confidence_score"),
            started_at=event.timestamp,
        )
        self._session.add(incident)
        await self._add_timeline(incident.id, "incident_created", title, event)
        await self._session.flush()
        log.info("incident_created", incident_id=str(incident.id))
        return incident

    async def get(self, incident_id: UUID) -> Incident | None:
        result = await self._session.execute(
            select(Incident)
            .options(selectinload(Incident.timeline))
            .where(Incident.id == incident_id)
        )
        return result.scalar_one_or_none()

    async def list_open(self, limit: int = 50) -> list[Incident]:
        result = await self._session.execute(
            select(Incident)
            .where(Incident.status.in_(("open", "investigating", "acknowledged")))
            .order_by(Incident.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def acknowledge(self, incident_id: UUID) -> Incident | None:
        incident = await self.get(incident_id)
        if not incident:
            return None
        incident.status = "acknowledged"
        await self._add_timeline(incident_id, "incident_acknowledged", "Incident acknowledged by operator", None)
        await self._session.flush()
        return incident

    async def resolve(self, incident_id: UUID) -> Incident | None:
        incident = await self.get(incident_id)
        if not incident:
            return None
        incident.status = "resolved"
        incident.resolved_at = datetime.utcnow()
        await self._add_timeline(incident_id, "incident_resolved", "Incident marked as resolved", None)
        await self._session.flush()
        return incident

    async def get_recent_incidents(self, cluster_id: UUID, days: int = 30) -> list[dict]:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self._session.execute(
            select(Incident)
            .where(Incident.cluster_id == cluster_id, Incident.started_at >= cutoff)
            .order_by(Incident.started_at.desc())
        )
        incidents = result.scalars().all()
        incident_list = []
        for inc in incidents:
            cascade = []
            if inc.cascade_chain_json:
                try:
                    cascade = json.loads(inc.cascade_chain_json)
                except Exception:
                    cascade = []
            incident_list.append({
                "id": str(inc.id),
                "incident_id": str(inc.id),
                "title": inc.title,
                "status": inc.status,
                "severity": inc.severity,
                "root_cause": inc.root_cause,
                "root_service": inc.root_service,
                "incident_type": inc.root_cause or "service_failure",
                "error_type": inc.root_cause or "service_failure",
                "confidence_score": inc.confidence_score,
                "cascade_chain": cascade,
                "started_at": inc.started_at.isoformat() if inc.started_at else datetime.utcnow().isoformat(),
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            })
        return incident_list

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
