import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.api.deps import get_session
from sentinelops.api.schemas.incident import IncidentResponse, IncidentSummary
from sentinelops.engines.replay import ReplayEngine
from sentinelops.services.incident_service import IncidentService

router = APIRouter()


@router.get("", response_model=list[IncidentSummary])
async def list_incidents(
    session: AsyncSession = Depends(get_session),
) -> list[IncidentSummary]:
    service = IncidentService(session)
    incidents = await service.list_open()
    return [IncidentSummary.model_validate(i) for i in incidents]


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> IncidentResponse:
    service = IncidentService(session)
    incident = await service.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    try:
        affected_services = json.loads(incident.affected_services_json or "[]")
        cascade_chain = json.loads(incident.cascade_chain_json or "[]")
    except (json.JSONDecodeError, ValueError):
        affected_services = []
        cascade_chain = []

    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        status=incident.status,
        severity=incident.severity,
        root_service=incident.root_service,
        confidence_score=incident.confidence_score,
        started_at=incident.started_at,
        root_cause=incident.root_cause,
        affected_services=affected_services,
        cascade_chain=cascade_chain,
        timeline=[
            {"timestamp": t.timestamp.isoformat(), "title": t.title, "type": t.event_type}
            for t in (incident.timeline or [])
        ],
    )


@router.get("/{incident_id}/replay")
async def replay_incident(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    replay = ReplayEngine()
    db_data = await replay.load_from_db(session, incident_id)
    if db_data.get("frames"):
        return {"incident_id": str(incident_id), **db_data}
    return {
        "incident_id": str(incident_id),
        "timeline": replay.get_timeline(incident_id),
        "frames": replay.build_replay_frames(incident_id),
    }
