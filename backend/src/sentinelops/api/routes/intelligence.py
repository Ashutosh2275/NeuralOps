from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.api.deps import get_session
from sentinelops.services.intelligence_service import IntelligenceService
from sentinelops.services.recommendation_service import RecommendationService

router = APIRouter()
DEFAULT_CLUSTER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.get("/topology/graph")
async def get_live_topology(session: AsyncSession = Depends(get_session)) -> dict:
    svc = IntelligenceService(session)
    graph = svc.dependency_engine.to_snapshot_json()
    return {"nodes": graph["nodes"], "edges": graph["edges"], "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"])}


@router.get("/topology/versions")
async def list_topology_versions(session: AsyncSession = Depends(get_session)) -> list[dict]:
    from sqlalchemy import select
    from sentinelops.models.intelligence import TopologyVersion

    result = await session.execute(
        select(TopologyVersion)
        .where(TopologyVersion.cluster_id == DEFAULT_CLUSTER_ID)
        .order_by(TopologyVersion.version.desc())
        .limit(20)
    )
    return [
        {"version": v.version, "nodes": v.node_count, "edges": v.edge_count, "created_at": v.created_at.isoformat()}
        for v in result.scalars()
    ]


@router.get("/blast-radius/{namespace}/{pod_name}")
async def blast_radius(namespace: str, pod_name: str, session: AsyncSession = Depends(get_session)) -> dict:
    svc = IntelligenceService(session)
    return svc.blast_radius(namespace, pod_name)


@router.get("/incidents/{incident_id}/rca")
async def get_rca_report(incident_id: UUID, session: AsyncSession = Depends(get_session)) -> dict:
    from sentinelops.services.incident_service import IncidentService
    import json

    incident = await IncidentService(session).get(incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return {
        "incident_id": str(incident.id),
        "root_cause": incident.root_cause,
        "root_service": incident.root_service,
        "confidence": incident.confidence_score,
        "cascade_chain": json.loads(incident.cascade_chain_json or "[]"),
    }


@router.get("/incidents/{incident_id}/recommendations")
async def get_recommendations(incident_id: UUID, session: AsyncSession = Depends(get_session)) -> list[dict]:
    recs = await RecommendationService(session).list_for_incident(incident_id)
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "description": r.description,
            "action_type": r.action_type,
            "kubectl_command": r.kubectl_command,
            "priority": r.priority,
            "confidence": r.confidence,
            "agent_type": r.agent_type,
        }
        for r in recs
    ]


@router.get("/incidents/{incident_id}/insights")
async def get_ai_insights(incident_id: UUID, session: AsyncSession = Depends(get_session)) -> list[dict]:
    from sqlalchemy import select
    from sentinelops.models.intelligence import AIInsight

    result = await session.execute(
        select(AIInsight).where(AIInsight.incident_id == incident_id).order_by(AIInsight.created_at)
    )
    return [
        {"agent": i.agent_type, "title": i.title, "content": i.content, "confidence": i.confidence}
        for i in result.scalars()
    ]
