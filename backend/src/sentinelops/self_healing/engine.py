import asyncio
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass
from typing import Optional

from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent
from sentinelops.simulator.incident_simulator import IncidentType

log = get_logger(__name__)


class RemediationType(str, Enum):
    POD_RESTART = "pod_restart"
    AUTO_SCALE = "auto_scale"
    RESOURCE_BOOST = "resource_boost"
    WORKLOAD_REDISTRIBUTION = "workload_redistribution"
    TRAFFIC_REROUTE = "traffic_reroute"
    DEPENDENCY_ISOLATION = "dependency_isolation"
    ROLLBACK = "rollback"
    DEGRADED_MODE = "degraded_mode"


@dataclass
class RemediationAction:
    action_id: str
    incident_id: UUID
    action_type: RemediationType
    target_pod: Optional[str] = None
    target_service: Optional[str] = None
    parameters: dict = None
    kubectl_command: str = ""
    estimated_recovery_time_seconds: int = 0
    risk_level: str = "low"  # low, medium, high
    rollback_possible: bool = True


class SelfHealingEngine:
    def __init__(self):
        self._healable_incidents = {
            IncidentType.CPU_SPIKE: self._remediate_cpu_spike,
            IncidentType.MEMORY_LEAK: self._remediate_memory_leak,
            IncidentType.POD_RESTART_STORM: self._remediate_pod_restart_storm,
            IncidentType.CRASHLOOP_BACKOFF: self._remediate_crashloop_backoff,
            IncidentType.PVC_SATURATION: self._remediate_pvc_saturation,
            IncidentType.NETWORK_LATENCY: self._remediate_network_latency,
            IncidentType.DEPENDENCY_FAILURE: self._remediate_dependency_failure,
            IncidentType.DATABASE_BOTTLENECK: self._remediate_database_bottleneck,
            IncidentType.API_GATEWAY_CONGESTION: self._remediate_api_gateway_congestion,
        }
        self._executed_actions: dict[str, RemediationAction] = {}

    async def analyze_remediation(self, incident_id: UUID, event: BaseEvent, rca_result: Optional[str] = None) -> list[RemediationAction]:
        anomaly_type = event.payload.get("anomaly_type", "unknown")

        for incident_type in IncidentType:
            if incident_type.value == anomaly_type:
                remediation_fn = self._healable_incidents.get(incident_type)
                if remediation_fn:
                    return await remediation_fn(incident_id, event)

        return []

    async def _remediate_cpu_spike(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        pod_name = event.payload.get("pod_name")
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.AUTO_SCALE,
                target_pod=pod_name,
                target_service=pod_name.rsplit("-", 1)[0] if "-" in pod_name else pod_name,
                parameters={"replicas": 3, "max_cpu": "500m"},
                kubectl_command=f"kubectl autoscale deployment {pod_name.rsplit('-', 1)[0]} --min=2 --max=5 -n {namespace}",
                estimated_recovery_time_seconds=30,
                risk_level="low",
            ),
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.RESOURCE_BOOST,
                target_pod=pod_name,
                parameters={"cpu_limit": "1000m", "cpu_request": "500m"},
                kubectl_command=f"kubectl set resources deployment {pod_name.rsplit('-', 1)[0]} --limits=cpu=1000m --requests=cpu=500m -n {namespace}",
                estimated_recovery_time_seconds=20,
                risk_level="low",
            ),
        ]
        return actions

    async def _remediate_memory_leak(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        pod_name = event.payload.get("pod_name")
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.POD_RESTART,
                target_pod=pod_name,
                parameters={"rollout": "restart"},
                kubectl_command=f"kubectl rollout restart deployment {pod_name.rsplit('-', 1)[0]} -n {namespace}",
                estimated_recovery_time_seconds=45,
                risk_level="medium",
                rollback_possible=True,
            ),
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.RESOURCE_BOOST,
                target_pod=pod_name,
                parameters={"memory_limit": "1024Mi", "memory_request": "512Mi"},
                kubectl_command=f"kubectl set resources deployment {pod_name.rsplit('-', 1)[0]} --limits=memory=1024Mi --requests=memory=512Mi -n {namespace}",
                estimated_recovery_time_seconds=30,
                risk_level="low",
            ),
        ]
        return actions

    async def _remediate_pod_restart_storm(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        service = event.payload.get("service")
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.WORKLOAD_REDISTRIBUTION,
                target_service=service,
                parameters={"node_selector": "stable=true"},
                kubectl_command=f"kubectl patch deployment {service} -p '{{\"spec\":{{\"template\":{{\"spec\":{{\"nodeSelector\":{{\"stable\":\"true\"}}}}}}}}}}' -n {namespace}",
                estimated_recovery_time_seconds=60,
                risk_level="medium",
            ),
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.DEGRADED_MODE,
                target_service=service,
                parameters={"replica_factor": 0.5},
                kubectl_command=f"kubectl scale deployment {service} --replicas=1 -n {namespace}",
                estimated_recovery_time_seconds=20,
                risk_level="medium",
            ),
        ]
        return actions

    async def _remediate_crashloop_backoff(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        pod_name = event.payload.get("pod_name")
        namespace = event.namespace
        deployment = pod_name.rsplit("-", 1)[0] if "-" in pod_name else pod_name

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.ROLLBACK,
                target_pod=pod_name,
                parameters={"revision": "previous"},
                kubectl_command=f"kubectl rollout undo deployment {deployment} -n {namespace}",
                estimated_recovery_time_seconds=60,
                risk_level="high",
                rollback_possible=True,
            ),
        ]
        return actions

    async def _remediate_pvc_saturation(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        pvc_name = event.payload.get("pvc_name")
        pod_name = event.payload.get("pod_name")
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.WORKLOAD_REDISTRIBUTION,
                target_pod=pod_name,
                parameters={"expand_storage": True, "size_increase_percent": 50},
                kubectl_command=f"kubectl patch pvc {pvc_name} -p '{{\"spec\":{{\"resources\":{{\"requests\":{{\"storage\":\"150Gi\"}}}}}}}}' -n {namespace}",
                estimated_recovery_time_seconds=30,
                risk_level="medium",
            ),
        ]
        return actions

    async def _remediate_network_latency(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        services = event.payload.get("affected_services", [])
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.TRAFFIC_REROUTE,
                target_service=services[0] if services else "service",
                parameters={"enable_local_traffic_policy": True},
                kubectl_command="kubectl apply -f - <<EOF\napiVersion: policy/v1\nkind: PodDisruptionBudget\nmetadata:\n  name: traffic-local\nspec:\n  minAvailable: 1\n  selector:\n    matchLabels:\n      app: " + (services[0] if services else "app") + "\nEOF",
                estimated_recovery_time_seconds=20,
                risk_level="low",
            ),
        ]
        return actions

    async def _remediate_dependency_failure(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        failed_service = event.payload.get("failed_service")
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.DEPENDENCY_ISOLATION,
                target_service=failed_service,
                parameters={"enable_circuit_breaker": True, "timeout_ms": 5000},
                kubectl_command=f"kubectl rollout restart deployment {failed_service} -n {namespace}",
                estimated_recovery_time_seconds=45,
                risk_level="low",
            ),
        ]
        return actions

    async def _remediate_database_bottleneck(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.AUTO_SCALE,
                target_service="database",
                parameters={"connection_pool_size": 100, "max_connections": 200},
                kubectl_command=f"kubectl set env deployment/database CONNECTION_POOL_SIZE=100 -n {namespace}",
                estimated_recovery_time_seconds=30,
                risk_level="low",
            ),
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.DEGRADED_MODE,
                target_service="database",
                parameters={"enable_read_replica": True},
                kubectl_command=f"kubectl scale deployment database-replica --replicas=2 -n {namespace}",
                estimated_recovery_time_seconds=60,
                risk_level="medium",
            ),
        ]
        return actions

    async def _remediate_api_gateway_congestion(self, incident_id: UUID, event: BaseEvent) -> list[RemediationAction]:
        namespace = event.namespace

        actions = [
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.AUTO_SCALE,
                target_service="api-gateway",
                parameters={"target_replicas": 5},
                kubectl_command=f"kubectl scale deployment api-gateway --replicas=5 -n {namespace}",
                estimated_recovery_time_seconds=45,
                risk_level="low",
            ),
            RemediationAction(
                action_id=str(uuid4()),
                incident_id=incident_id,
                action_type=RemediationType.DEGRADED_MODE,
                target_service="api-gateway",
                parameters={"enable_rate_limiting": True, "requests_per_second": 1000},
                kubectl_command=f"kubectl set env deployment/api-gateway RATE_LIMIT=1000 -n {namespace}",
                estimated_recovery_time_seconds=20,
                risk_level="low",
            ),
        ]
        return actions

    async def execute_action(self, action: RemediationAction) -> bool:
        try:
            log.info(
                f"remediation_action_executing_{action.action_type.value}",
                action_id=action.action_id,
                target=action.target_pod or action.target_service,
            )
            self._executed_actions[action.action_id] = action

            await asyncio.sleep(action.estimated_recovery_time_seconds * 0.1)

            log.info(
                f"remediation_action_completed_{action.action_type.value}",
                action_id=action.action_id,
            )
            return True
        except Exception as e:
            log.error(f"remediation_action_failed_{action.action_type.value}", error=str(e))
            return False

    def get_executed_actions(self) -> list[dict]:
        return [
            {
                "action_id": action.action_id,
                "incident_id": str(action.incident_id),
                "action_type": action.action_type.value,
                "target": action.target_pod or action.target_service,
                "status": "completed",
                "risk_level": action.risk_level,
            }
            for action in self._executed_actions.values()
        ]
