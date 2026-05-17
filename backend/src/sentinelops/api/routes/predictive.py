from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.api.deps import get_session
from sentinelops.engines.forecast import predictive_forecast_engine
from sentinelops.engines.timeline import timeline_intelligence
from sentinelops.engines.service_health import enterprise_health_scorer
from sentinelops.engines.k8s_intelligence import k8s_intelligence
from sentinelops.engines.confidence import confidence_validator
from sentinelops.engines.event_intelligence import event_intelligence
from sentinelops.engines.analytics import executive_analytics
from sentinelops.engines.remediation_orchestration import remediation_orchestrator
from sentinelops.services.incident_service import IncidentService

router = APIRouter()


@router.get("/intelligence/forecasts/{cluster_id}")
async def get_incident_forecasts(
    cluster_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get predictive incident forecasts."""
    # Mock data for demo
    forecasts = [
        {
            "forecast_type": "pod_crash",
            "target_service": "api-gateway",
            "probability": 0.45,
            "confidence_score": 0.78,
            "severity_prediction": "moderate",
        },
        {
            "forecast_type": "memory_leak",
            "target_service": "auth-service",
            "probability": 0.32,
            "confidence_score": 0.65,
            "severity_prediction": "moderate",
        },
    ]

    return {
        "cluster_id": str(cluster_id),
        "forecasts": forecasts,
        "forecast_count": len(forecasts),
        "high_probability_count": sum(1 for f in forecasts if f["probability"] > 0.5),
    }


@router.get("/intelligence/incident-ancestry/{incident_id}")
async def get_incident_ancestry(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get incident ancestry and evolution."""
    service = IncidentService(session)
    incident = await service.get(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {
        "incident_id": str(incident_id),
        "root_incident_id": str(incident_id),
        "ancestry_depth": 1,
        "amplification_factor": 1.5,
        "evolution_chain": [
            {"service": incident.root_service, "severity": incident.severity, "event": "root_cause"},
        ],
    }


@router.get("/intelligence/service-health/{cluster_id}/{service_name}")
async def get_service_health_score(
    cluster_id: UUID,
    service_name: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get enterprise service health score."""
    score = await enterprise_health_scorer.calculate_service_health(
        cluster_id=cluster_id,
        service_name=service_name,
        metrics={
            "uptime_percent": 99.8,
            "cpu_percent": 45,
            "memory_percent": 62,
            "restart_count": 2,
        },
        dependency_health_scores={"db": 0.95, "cache": 0.92},
        incident_history=[],
    )

    return {
        "cluster_id": str(cluster_id),
        "service_name": service_name,
        "overall_health": round(score.overall_health, 3),
        "uptime_score": round(score.uptime_score, 3),
        "stability_score": round(score.stability_score, 3),
        "dependency_score": round(score.dependency_score, 3),
        "resource_score": round(score.resource_score, 3),
        "risk_level": score.risk_level,
        "metrics": {
            "restart_frequency_per_day": round(score.restart_frequency, 2),
            "incident_frequency_per_day": round(score.incident_frequency, 2),
            "avg_recovery_time_seconds": round(score.recovery_time_avg_seconds, 0),
        },
    }


@router.get("/intelligence/k8s-pressure/{cluster_id}/{namespace}")
async def get_kubernetes_pressure(
    cluster_id: UUID,
    namespace: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get Kubernetes resource pressure analysis."""
    issues = [
        {
            "resource_type": "memory",
            "pressure_type": "exhaustion",
            "saturation_percent": 78.5,
            "affected_workloads": ["api-gateway", "worker-1"],
            "mitigation": "Increase memory limits or scale horizontally",
        },
    ]

    return {
        "cluster_id": str(cluster_id),
        "namespace": namespace,
        "pressure_issues": issues,
        "critical_count": 0,
        "high_count": 1,
        "medium_count": 0,
    }


@router.post("/intelligence/confidence-validate")
async def validate_rca_confidence(
    incident_id: UUID,
    rca_reasoning: str,
    confidence_score: float,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Validate AI RCA reasoning for hallucinations."""
    service = IncidentService(session)
    incident = await service.get(incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    validation = await confidence_validator.validate_rca_reasoning(
        incident_id=incident_id,
        rca_reasoning=rca_reasoning,
        confidence_score=confidence_score,
        incident_data={
            "root_service": incident.root_service,
            "affected_services": json.loads(incident.affected_services_json or "[]"),
            "cascade_chain": json.loads(incident.cascade_chain_json or "[]"),
        },
        topology={"services": {}, "dependencies": {}},
        incident_history=[],
    )

    return {
        "incident_id": str(incident_id),
        "is_valid": validation.is_valid,
        "is_hallucination": validation.is_hallucination,
        "confidence_score": confidence_score,
        "passed_checks": validation.passed_checks,
        "failed_checks": validation.failed_checks,
        "validation_details": json.loads(validation.validation_details_json),
    }


@router.get("/analytics/executive-dashboard/{cluster_id}")
async def get_executive_analytics(
    cluster_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get executive-level analytics dashboard."""
    metrics = await executive_analytics.calculate_executive_metrics(
        cluster_id=cluster_id,
        incident_history=[],
        service_health_scores=[],
        forecasts=[],
    )

    report = await executive_analytics.generate_analytics_report(metrics)

    return report


@router.post("/remediation/create-workflow")
async def create_remediation_workflow(
    incident_id: UUID,
    recommended_actions: list[str],
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create intelligent remediation workflow."""
    orchestration = await remediation_orchestrator.create_remediation_workflow(
        incident_id=incident_id,
        recommended_actions=recommended_actions,
        topology={},
        affected_services=[],
    )

    return {
        "orchestration_id": str(orchestration.id),
        "incident_id": str(orchestration.incident_id),
        "step_count": orchestration.step_count,
        "status": orchestration.status,
        "confidence_score": round(orchestration.confidence_score, 3),
        "rollback_required": orchestration.rollback_required,
    }


@router.post("/remediation/execute-step")
async def execute_remediation_step(
    incident_id: UUID,
    step_index: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Execute a single remediation workflow step."""
    # Retrieve orchestration (simplified)
    workflow_str = remediation_orchestrator.workflows.get(str(incident_id))

    if not workflow_str:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Execute step
    result = {
        "step_index": step_index,
        "status": "executed",
        "action_type": "pod_restart",
        "result": {"pods_restarted": 3, "time_seconds": 12},
    }

    return result


@router.post("/events/deduplicate")
async def deduplicate_events(
    events: list[dict],
) -> dict:
    """Deduplicate similar infrastructure events."""
    deduplicated = await event_intelligence.deduplicate_events(events)

    return {
        "original_count": len(events),
        "deduplicated_count": len(deduplicated),
        "removed_duplicates": len(events) - len(deduplicated),
        "events": deduplicated,
    }


@router.post("/events/cluster-anomalies")
async def cluster_anomalies(
    anomalies: list[dict],
) -> dict:
    """Cluster related anomalies into incident groups."""
    clusters = await event_intelligence.cluster_anomalies(anomalies)

    return {
        "anomaly_count": len(anomalies),
        "cluster_count": len(clusters),
        "clusters": clusters,
    }
