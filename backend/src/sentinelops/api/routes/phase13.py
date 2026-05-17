"""Phase 13 Predictive Operations API Routes"""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.api.deps import get_session
from sentinelops.engines.predictive_failure_engine import predictive_failure_engine
from sentinelops.engines.infrastructure_memory_engine import infrastructure_memory_engine
from sentinelops.engines.consensus_engine import consensus_engine, AgentVote
from sentinelops.engines.advanced_remediation_orchestrator import advanced_remediation_orchestrator
from sentinelops.engines.advanced_k8s_intelligence_engine import advanced_k8s_intelligence
from sentinelops.services.topology_service import topology_service
from sentinelops.services.incident_service import IncidentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/phase13", tags=["Phase 13: Predictive Operations"])


# ===== PREDICTIVE FAILURE ENDPOINTS =====

@router.get("/predictions/forecast/{cluster_id}")
async def forecast_failures(
    cluster_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Forecast infrastructure failures for next 24 hours"""
    try:
        incident_service = IncidentService(session)
        topology = await topology_service.get_topology_graph(cluster_id)

        # Get recent incident history
        incidents = await incident_service.get_recent_incidents(cluster_id, days=30)

        # Generate predictions
        predictions = await predictive_failure_engine.forecast_failures(
            cluster_id=cluster_id,
            incident_history=incidents,
            topology=topology,
            session=session,
        )

        return {
            "cluster_id": str(cluster_id),
            "forecast_count": len(predictions),
            "predictions": [
                {
                    "incident_type": p.incident_type,
                    "probability": p.probability,
                    "confidence": p.confidence,
                    "time_to_failure_hours": p.time_to_failure_hours,
                    "severity_forecast": p.severity_forecast,
                    "affected_services": p.affected_services,
                    "reasoning": p.reasoning,
                }
                for p in predictions
            ],
            "generated_at": "2026-05-17T10:30:00Z",
        }
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== MEMORY ENGINE ENDPOINTS =====

@router.get("/memory/incident-ancestry/{incident_id}")
async def get_incident_ancestry(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve incident ancestry from memory"""
    try:
        ancestry = await infrastructure_memory_engine.get_incident_ancestry(incident_id)

        if not ancestry:
            raise HTTPException(status_code=404, detail="Incident not in memory")

        return {
            "incident_id": str(incident_id),
            "ancestry": ancestry,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/service-history/{cluster_id}/{service_name}")
async def get_service_history(
    cluster_id: UUID,
    service_name: str,
    session: AsyncSession = Depends(get_session),
):
    """Get historical information about service"""
    try:
        history = await infrastructure_memory_engine.get_service_history(cluster_id, service_name)

        return {
            "cluster_id": str(cluster_id),
            "service_name": service_name,
            "history": history or {},
        }
    except Exception as e:
        logger.error(f"Service history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/cascade-patterns/{cluster_id}/{source_service}")
async def get_cascade_patterns(
    cluster_id: UUID,
    source_service: str,
):
    """Get known cascade patterns from service"""
    try:
        patterns = await infrastructure_memory_engine.get_cascade_patterns(
            cluster_id=cluster_id,
            source_service=source_service,
        )

        return {
            "cluster_id": str(cluster_id),
            "source_service": source_service,
            "pattern_count": len(patterns),
            "patterns": patterns,
        }
    except Exception as e:
        logger.error(f"Cascade patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/stats/{cluster_id}")
async def get_memory_stats(cluster_id: UUID):
    """Get infrastructure memory statistics"""
    try:
        stats = infrastructure_memory_engine.get_memory_stats()

        return {
            "cluster_id": str(cluster_id),
            "memory_stats": stats,
            "total_records": sum(stats.values()),
        }
    except Exception as e:
        logger.error(f"Memory stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== CONSENSUS ENGINE ENDPOINTS =====

@router.post("/consensus/vote/{incident_id}")
async def submit_consensus_vote(
    incident_id: UUID,
    vote_data: dict,  # {agent_name, root_cause, confidence, evidence}
    session: AsyncSession = Depends(get_session),
):
    """Submit agent vote for RCA"""
    try:
        vote = AgentVote(
            agent_name=vote_data.get("agent_name"),
            root_cause=vote_data.get("root_cause"),
            confidence=vote_data.get("confidence"),
            evidence=vote_data.get("evidence", []),
        )

        await consensus_engine.collect_votes(incident_id, [vote])

        return {
            "incident_id": str(incident_id),
            "status": "vote_recorded",
            "agent": vote.agent_name,
        }
    except Exception as e:
        logger.error(f"Vote submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consensus/compute/{incident_id}")
async def compute_consensus(
    incident_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Compute consensus from collected votes"""
    try:
        topology = await topology_service.get_topology_graph(UUID("00000000-0000-0000-0000-000000000000"))

        result = await consensus_engine.compute_consensus(
            incident_id=incident_id,
            topology=topology,
        )

        return {
            "incident_id": str(incident_id),
            "root_cause": result.root_cause,
            "confidence": result.confidence,
            "consensus_score": result.consensus_score,
            "supporting_votes": result.supporting_votes,
            "dissenting_votes": result.dissenting_votes,
            "is_hallucination": result.is_hallucination,
            "validation_checks": result.validation_checks,
        }
    except Exception as e:
        logger.error(f"Consensus computation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== REMEDIATION ORCHESTRATOR ENDPOINTS =====

@router.post("/remediation/workflow/create")
async def create_remediation_workflow(
    workflow_data: dict,  # {incident_id, root_cause, affected_services, cascade_chain}
    session: AsyncSession = Depends(get_session),
):
    """Create remediation workflow"""
    try:
        topology = await topology_service.get_topology_graph(
            UUID(workflow_data.get("cluster_id", "00000000-0000-0000-0000-000000000000"))
        )

        workflow = await advanced_remediation_orchestrator.create_workflow(
            incident_id=UUID(workflow_data.get("incident_id")),
            root_cause=workflow_data.get("root_cause"),
            affected_services=workflow_data.get("affected_services", []),
            cascade_chain=workflow_data.get("cascade_chain", []),
            topology=topology,
        )

        return {
            "workflow_id": str(workflow.id),
            "incident_id": str(workflow.incident_id),
            "status": workflow.status,
            "step_count": len(workflow.steps),
            "confidence": workflow.confidence,
            "rollback_required": workflow.rollback_required,
            "steps": [
                {
                    "index": s.step_index,
                    "action": s.action.value,
                    "target_services": s.target_services,
                    "estimated_duration": s.estimated_duration_seconds,
                }
                for s in workflow.steps
            ],
        }
    except Exception as e:
        logger.error(f"Workflow creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remediation/workflow/execute-step")
async def execute_workflow_step(
    execution_data: dict,  # {workflow_id, step_index}
):
    """Execute remediation workflow step"""
    try:
        # In production, retrieve workflow from database
        workflow_id = execution_data.get("workflow_id")
        step_index = execution_data.get("step_index")

        result = {
            "workflow_id": workflow_id,
            "step_index": step_index,
            "status": "executed",
            "message": "Step execution simulated",
        }

        return result
    except Exception as e:
        logger.error(f"Step execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== KUBERNETES INTELLIGENCE ENDPOINTS =====

@router.get("/k8s/pressure/{cluster_id}/{namespace}")
async def analyze_k8s_pressure(
    cluster_id: UUID,
    namespace: str,
    pods_data: dict | None = None,  # Mock data for demo
):
    """Analyze Kubernetes resource pressure"""
    try:
        # Mock data for demonstration
        pods = pods_data or [
            {"name": f"pod-{i}", "cpu_milli": 100 + i * 50, "memory_mb": 256 + i * 100}
            for i in range(5)
        ]
        nodes = [
            {"name": "node-1", "available_cpu": 4000, "available_memory": 8000},
            {"name": "node-2", "available_cpu": 2000, "available_memory": 16000},
        ]

        pressure_issues = await advanced_k8s_intelligence.analyze_namespace_pressure(
            cluster_id=cluster_id,
            namespace=namespace,
            pods=pods,
            nodes=nodes,
        )

        return {
            "cluster_id": str(cluster_id),
            "namespace": namespace,
            "issue_count": len(pressure_issues),
            "issues": [
                {
                    "resource_type": issue.resource_type,
                    "pressure_type": issue.pressure_type,
                    "saturation_percent": issue.saturation_percent,
                    "affected_pods": issue.affected_pods,
                    "mitigation": issue.mitigation_recommendation,
                    "severity": issue.severity,
                }
                for issue in pressure_issues
            ],
        }
    except Exception as e:
        logger.error(f"K8s pressure analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== HEALTH & STATUS ENDPOINTS =====

@router.get("/phase13/status")
async def get_phase13_status():
    """Get Phase 13 system status"""
    try:
        memory_stats = infrastructure_memory_engine.get_memory_stats()

        return {
            "status": "operational",
            "components": {
                "predictive_failure_engine": "active",
                "infrastructure_memory_engine": "active",
                "consensus_engine": "active",
                "remediation_orchestrator": "active",
                "k8s_intelligence": "active",
            },
            "memory_stats": memory_stats,
            "version": "phase_13_beta_1",
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phase13/health")
async def get_phase13_health():
    """Health check for Phase 13 systems"""
    return {"status": "healthy", "timestamp": "2026-05-17T10:30:00Z"}
