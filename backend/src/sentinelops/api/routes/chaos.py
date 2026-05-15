import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.api.deps import get_session
from sentinelops.engines.blast_radius import blast_radius_engine
from sentinelops.engines.chaos import chaos_simulator
from sentinelops.engines.health import health_engine
from sentinelops.engines.healing import autonomous_healer
from sentinelops.models.cluster import Cluster
from sentinelops.models.incident import Incident
from sentinelops.models.simulation import RemediationAction, SimulatedIncident
from sentinelops.services.incident_service import IncidentService

router = APIRouter()


@router.post("/chaos/simulate/cpu-spike")
async def trigger_cpu_spike_storm(
    cluster_id: UUID,
    namespace: str,
    target_pods: list[str],
    duration_seconds: int = 300,
    severity: str = "moderate",
    session: AsyncSession = Depends(get_session),
):
    """Trigger CPU spike storm simulation."""
    cluster = await session.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    sim = await chaos_simulator.trigger_cpu_spike_storm(
        cluster_id=cluster_id,
        namespace=namespace,
        target_pods=target_pods,
        duration_seconds=duration_seconds,
        severity=severity,
    )

    session.add(sim)
    await session.commit()

    return {
        "simulation_id": str(sim.id),
        "type": "cpu_spike",
        "status": "active",
        "duration_seconds": duration_seconds,
    }


@router.post("/chaos/simulate/memory-leak")
async def trigger_memory_leak(
    cluster_id: UUID,
    namespace: str,
    target_pods: list[str],
    duration_seconds: int = 600,
    severity: str = "major",
    session: AsyncSession = Depends(get_session),
):
    """Trigger memory leak simulation."""
    cluster = await session.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    sim = await chaos_simulator.trigger_memory_leak(
        cluster_id=cluster_id,
        namespace=namespace,
        target_pods=target_pods,
        duration_seconds=duration_seconds,
        severity=severity,
    )

    session.add(sim)
    await session.commit()

    return {
        "simulation_id": str(sim.id),
        "type": "memory_leak",
        "status": "active",
    }


@router.post("/chaos/simulate/cascading-failure")
async def trigger_cascading_failure(
    cluster_id: UUID,
    namespace: str,
    service_chain: list[str],
    duration_seconds: int = 500,
    session: AsyncSession = Depends(get_session),
):
    """Trigger cascading multi-service failure."""
    cluster = await session.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    sim = await chaos_simulator.trigger_cascading_multi_service_failure(
        cluster_id=cluster_id,
        namespace=namespace,
        service_chain=service_chain,
        duration_seconds=duration_seconds,
        severity="critical",
    )

    session.add(sim)
    await session.commit()

    return {
        "simulation_id": str(sim.id),
        "type": "cascading_failure",
        "service_chain": service_chain,
        "status": "active",
    }


@router.post("/remediation/recommend")
async def get_remediation_recommendations(
    incident_id: UUID,
    ai_recommendation: str,
    session: AsyncSession = Depends(get_session),
):
    """Get AI-recommended remediation actions."""
    incident = await session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get any associated simulation
    simulation_id = None
    if incident.cascade_chain_json:
        cascade_data = json.loads(incident.cascade_chain_json)
        if isinstance(cascade_data, list) and cascade_data:
            # Assume first entry has simulation_id
            simulation_id = cascade_data[0].get("simulation_id")

    if not simulation_id:
        simulation_id = UUID(int=0)

    actions = await autonomous_healer.recommend_remediation(
        incident_id=incident_id,
        simulation_id=simulation_id,
        ai_recommendation=ai_recommendation,
    )

    for action in actions:
        session.add(action)

    await session.commit()

    return {
        "incident_id": str(incident_id),
        "recommended_actions": [
            {
                "id": str(a.id),
                "type": a.action_type,
                "status": a.status,
                "recommendation": a.ai_recommendation,
            }
            for a in actions
        ],
    }


@router.post("/remediation/{action_id}/execute")
async def execute_remediation_action(
    action_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Execute a remediation action."""
    action = await session.get(RemediationAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    result = await autonomous_healer.execute_remediation_action(action)

    await session.commit()

    return {
        "action_id": str(action.id),
        "status": action.status,
        "result": result,
    }


@router.get("/health/cluster/{cluster_id}")
async def get_cluster_health(
    cluster_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get cluster infrastructure health score."""
    cluster = await session.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Count active incidents and remediations
    incident_service = IncidentService(session)
    incidents = await incident_service.list_open()
    active_incidents = len(incidents)

    # Calculate health score
    score = await health_engine.calculate_health_score(
        cluster_id=cluster_id,
        active_incidents=active_incidents,
        services={
            "api-gateway": {"uptime_percent": 99.8, "response_time_ms": 45, "error_rate_percent": 0.05},
            "auth-service": {"uptime_percent": 99.9, "response_time_ms": 60, "error_rate_percent": 0.02},
        },
        namespaces={
            "production": {"pod_health": 0.92, "service_count": 8, "healthy_services": 7},
            "staging": {"pod_health": 0.88, "service_count": 5, "healthy_services": 5},
        },
    )

    return {
        "cluster_id": str(cluster_id),
        "overall_health": round(score.overall_health, 3),
        "cluster_health": round(score.cluster_health, 3),
        "namespace_health": round(score.namespace_health, 3),
        "service_health": round(score.service_health, 3),
        "dependency_health": round(score.dependency_health, 3),
        "incident_risk_score": round(score.incident_risk_score, 3),
        "recovery_readiness_score": round(score.recovery_readiness_score, 3),
        "ai_confidence_score": round(score.ai_confidence_score, 3),
        "operational_stability_score": round(score.operational_stability_score, 3),
        "cascading_failure_probability": round(score.cascading_failure_probability, 3),
    }


@router.get("/blast-radius/{simulation_id}")
async def get_blast_radius(
    simulation_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get blast radius analysis for a simulation."""
    simulation = await session.get(SimulatedIncident, simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    affected_services = json.loads(simulation.target_services or "[]")

    event = await blast_radius_engine.calculate_blast_radius(
        origin_pod=json.loads(simulation.target_pods)[0] if simulation.target_pods else "unknown-pod",
        origin_namespace=simulation.namespace,
        affected_services=affected_services or ["api-gateway", "auth-service"],
        simulation_id=simulation_id,
    )

    impact = await blast_radius_engine.estimate_impact(
        affected_services=affected_services or ["api-gateway"],
        severity=0.8 if simulation.severity == "critical" else 0.5,
    )

    return {
        "simulation_id": str(simulation_id),
        "propagation_depth": event.propagation_depth,
        "degradation_intensity": round(event.degradation_intensity, 2),
        "recovery_path": json.loads(event.recovery_path_json),
        "business_impact": impact,
    }


@router.post("/demo/trigger-incident")
async def trigger_demo_incident(
    cluster_id: UUID,
    incident_type: str = "cascading_failure",
    session: AsyncSession = Depends(get_session),
):
    """One-click incident trigger for demo mode."""
    cluster = await session.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Create demo incident
    incident = Incident(
        cluster_id=cluster_id,
        title=f"Demo {incident_type.replace('_', ' ').title()}",
        status="open",
        severity="critical",
        root_service="demo-service",
        confidence_score=0.95,
        affected_services_json=json.dumps(["api-gateway", "auth-service", "payment-service"]),
        cascade_chain_json=json.dumps([
            {"service": "api-gateway", "depth": 0},
            {"service": "auth-service", "depth": 1},
            {"service": "payment-service", "depth": 2},
        ]),
    )

    session.add(incident)
    await session.commit()

    return {
        "incident_id": str(incident.id),
        "type": incident_type,
        "status": "created",
        "auto_remediation_enabled": True,
    }
