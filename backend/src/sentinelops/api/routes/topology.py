from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.api.deps import get_session
from sentinelops.api.schemas.topology import TopologyEdge, TopologyGraphResponse, TopologyNode
from sentinelops.services.topology_service import TopologyService

router = APIRouter()
DEFAULT_CLUSTER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.get("/graph", response_model=TopologyGraphResponse)
async def get_topology_graph(
    session: AsyncSession = Depends(get_session),
) -> TopologyGraphResponse:
    service = TopologyService(session)
    graph = await service.get_live_topology(DEFAULT_CLUSTER_ID)
    nodes = [TopologyNode(id=n["id"], **{k: v for k, v in n.items() if k != "id"}) for n in graph.get("nodes", [])]
    edges = [TopologyEdge(**e) for e in graph.get("edges", [])]
    return TopologyGraphResponse(
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
    )


@router.get("/versions")
async def list_topology_versions(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    """List recent topology versions."""
    service = TopologyService(session)
    return await service.list_topology_versions(DEFAULT_CLUSTER_ID, limit)


@router.post("/snapshot")
async def capture_topology_snapshot(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create a new topology snapshot."""
    service = TopologyService(session)
    snapshot = await service.capture_snapshot(DEFAULT_CLUSTER_ID)
    return {"snapshot_id": str(snapshot.id), "nodes": snapshot.node_count, "edges": snapshot.edge_count}


@router.get("/cascade/{namespace}/{pod_name}")
async def get_cascading_failure(
    namespace: str,
    pod_name: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get cascading failure analysis from a pod."""
    service = TopologyService(session)
    cascade_result = service.dependency_engine.detect_cascading_failure(
        service.dependency_engine.node_id(namespace, "Pod", pod_name)
    )
    health_propagations = service.dependency_engine.propagate_health(
        service.dependency_engine.node_id(namespace, "Pod", pod_name),
        "critical",
    )
    return {
        "cascade": {
            "origin": cascade_result.origin_node,
            "chain": cascade_result.cascade_chain,
            "affected_count": cascade_result.affected_count,
            "propagation_depth": cascade_result.propagation_depth,
            "escalation_factor": round(cascade_result.escalation_factor, 2),
        },
        "health_propagations": [
            {
                "node": hp.node_id,
                "original": hp.original_health,
                "propagated": hp.propagated_health,
                "influence": hp.influence_score,
                "path_length": len(hp.propagation_path),
                "path": hp.propagation_path,
            }
            for hp in health_propagations
        ],
    }


@router.get("/health-propagation/{namespace}/{pod_name}")
async def get_health_propagation(
    namespace: str,
    pod_name: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get health propagation from an unhealthy pod."""
    service = TopologyService(session)
    propagations = service.dependency_engine.propagate_health(
        service.dependency_engine.node_id(namespace, "Pod", pod_name),
        "warning",
    )
    return {
        "source_pod": f"{namespace}/{pod_name}",
        "propagations": [
            {
                "node_id": p.node_id,
                "original_health": p.original_health,
                "propagated_health": p.propagated_health,
                "influence_score": p.influence_score,
                "path": p.propagation_path,
            }
            for p in propagations
        ],
        "total_affected": len(propagations),
    }

