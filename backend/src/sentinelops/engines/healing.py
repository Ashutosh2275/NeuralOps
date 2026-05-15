import asyncio
import json
from datetime import datetime
from uuid import UUID

from sentinelops.models.simulation import RemediationAction


class AutonousSelfHealingEngine:
    """Deterministic remediation engine for incident recovery."""

    def __init__(self):
        self.active_remediations = {}
        self.event_handlers = []

    def on_event(self, handler):
        self.event_handlers.append(handler)
        return handler

    async def emit_event(self, event_type: str, payload: dict):
        """Emit remediation event to all listeners."""
        payload["timestamp"] = datetime.utcnow().isoformat()
        payload["event_type"] = event_type
        for handler in self.event_handlers:
            try:
                await handler(payload) if asyncio.iscoroutinefunction(handler) else handler(payload)
            except Exception as e:
                print(f"Event handler error: {e}")

    async def recommend_remediation(
        self,
        incident_id: UUID,
        simulation_id: UUID,
        ai_recommendation: str,
    ) -> list[RemediationAction]:
        """Parse AI recommendations and create safe remediation actions."""
        actions = []

        # Extract recommended actions from AI response
        recommendation_lower = ai_recommendation.lower()

        if "restart" in recommendation_lower and "pod" in recommendation_lower:
            actions.append(await self._create_pod_restart_action(
                incident_id=incident_id,
                simulation_id=simulation_id,
                ai_recommendation=ai_recommendation,
            ))

        if "scale" in recommendation_lower or "replica" in recommendation_lower:
            actions.append(await self._create_replica_scaling_action(
                incident_id=incident_id,
                simulation_id=simulation_id,
                ai_recommendation=ai_recommendation,
            ))

        if "isolate" in recommendation_lower or "degrade" in recommendation_lower:
            actions.append(await self._create_workload_isolation_action(
                incident_id=incident_id,
                simulation_id=simulation_id,
                ai_recommendation=ai_recommendation,
            ))

        if "reroute" in recommendation_lower or "route" in recommendation_lower:
            actions.append(await self._create_traffic_rerouting_action(
                incident_id=incident_id,
                simulation_id=simulation_id,
                ai_recommendation=ai_recommendation,
            ))

        if "rollback" in recommendation_lower:
            actions.append(await self._create_rollback_action(
                incident_id=incident_id,
                simulation_id=simulation_id,
                ai_recommendation=ai_recommendation,
            ))

        return actions

    async def execute_remediation_action(self, action: RemediationAction) -> dict:
        """Execute deterministic, safe remediation action."""
        action.status = "in_progress"
        action.started_at = datetime.utcnow()

        result = {}

        if action.action_type == "pod_restart":
            result = await self._execute_pod_restart(action)
        elif action.action_type == "replica_scaling":
            result = await self._execute_replica_scaling(action)
        elif action.action_type == "workload_isolation":
            result = await self._execute_workload_isolation(action)
        elif action.action_type == "traffic_rerouting":
            result = await self._execute_traffic_rerouting(action)
        elif action.action_type == "rollback":
            result = await self._execute_rollback(action)

        action.status = "completed"
        action.completed_at = datetime.utcnow()

        await self.emit_event("remediation_completed", {
            "action_id": str(action.id),
            "action_type": action.action_type,
            "status": "success",
            "result": result,
            "duration_seconds": (action.completed_at - action.started_at).total_seconds(),
        })

        return result

    async def _create_pod_restart_action(
        self,
        incident_id: UUID,
        simulation_id: UUID,
        ai_recommendation: str,
    ) -> RemediationAction:
        """Create safe pod restart action."""
        action = RemediationAction(
            simulation_id=simulation_id,
            incident_id=incident_id,
            action_type="pod_restart",
            target_namespace="default",
            status="pending",
            ai_recommendation=ai_recommendation,
            parameters_json=json.dumps({
                "grace_period_seconds": 30,
                "propagation_policy": "Foreground",
                "max_retries": 3,
            }),
        )
        await self.emit_event("remediation_planned", {
            "action_id": str(action.id),
            "type": "pod_restart",
            "reason": "AI recommended pod restart",
        })
        return action

    async def _create_replica_scaling_action(
        self,
        incident_id: UUID,
        simulation_id: UUID,
        ai_recommendation: str,
    ) -> RemediationAction:
        """Create replica auto-scaling action."""
        action = RemediationAction(
            simulation_id=simulation_id,
            incident_id=incident_id,
            action_type="replica_scaling",
            target_namespace="default",
            status="pending",
            ai_recommendation=ai_recommendation,
            parameters_json=json.dumps({
                "scale_up_factor": 1.5,
                "scale_down_factor": 0.75,
                "min_replicas": 2,
                "max_replicas": 10,
            }),
        )
        await self.emit_event("remediation_planned", {
            "action_id": str(action.id),
            "type": "replica_scaling",
            "reason": "AI recommended scaling to handle load",
        })
        return action

    async def _create_workload_isolation_action(
        self,
        incident_id: UUID,
        simulation_id: UUID,
        ai_recommendation: str,
    ) -> RemediationAction:
        """Create workload isolation action."""
        action = RemediationAction(
            simulation_id=simulation_id,
            incident_id=incident_id,
            action_type="workload_isolation",
            target_namespace="default",
            status="pending",
            ai_recommendation=ai_recommendation,
            parameters_json=json.dumps({
                "isolation_level": "namespace",
                "qos_class": "Guaranteed",
                "preserve_namespace_others": True,
            }),
        )
        await self.emit_event("remediation_planned", {
            "action_id": str(action.id),
            "type": "workload_isolation",
            "reason": "AI recommended isolating degraded workload",
        })
        return action

    async def _create_traffic_rerouting_action(
        self,
        incident_id: UUID,
        simulation_id: UUID,
        ai_recommendation: str,
    ) -> RemediationAction:
        """Create traffic rerouting action."""
        action = RemediationAction(
            simulation_id=simulation_id,
            incident_id=incident_id,
            action_type="traffic_rerouting",
            target_namespace="default",
            status="pending",
            ai_recommendation=ai_recommendation,
            parameters_json=json.dumps({
                "rerouting_strategy": "round_robin",
                "health_check_interval_seconds": 5,
                "failure_threshold": 3,
            }),
        )
        await self.emit_event("remediation_planned", {
            "action_id": str(action.id),
            "type": "traffic_rerouting",
            "reason": "AI recommended traffic rerouting",
        })
        return action

    async def _create_rollback_action(
        self,
        incident_id: UUID,
        simulation_id: UUID,
        ai_recommendation: str,
    ) -> RemediationAction:
        """Create rollback action."""
        action = RemediationAction(
            simulation_id=simulation_id,
            incident_id=incident_id,
            action_type="rollback",
            target_namespace="default",
            status="pending",
            ai_recommendation=ai_recommendation,
            parameters_json=json.dumps({
                "rollback_depth": 1,
                "preserve_pvcs": True,
                "wait_for_readiness": True,
            }),
        )
        await self.emit_event("remediation_planned", {
            "action_id": str(action.id),
            "type": "rollback",
            "reason": "AI recommended deployment rollback",
        })
        return action

    async def _execute_pod_restart(self, action: RemediationAction) -> dict:
        """Simulate pod restart remediation."""
        await asyncio.sleep(0.5)
        return {
            "pods_restarted": 3,
            "restart_time_seconds": 12,
            "status": "healthy",
        }

    async def _execute_replica_scaling(self, action: RemediationAction) -> dict:
        """Simulate replica scaling."""
        await asyncio.sleep(1.0)
        return {
            "previous_replicas": 3,
            "new_replicas": 5,
            "scaling_time_seconds": 45,
            "readiness": True,
        }

    async def _execute_workload_isolation(self, action: RemediationAction) -> dict:
        """Simulate workload isolation."""
        await asyncio.sleep(0.3)
        return {
            "isolated_pods": 5,
            "isolation_status": "active",
            "resource_limits_applied": True,
        }

    async def _execute_traffic_rerouting(self, action: RemediationAction) -> dict:
        """Simulate traffic rerouting."""
        await asyncio.sleep(0.8)
        return {
            "routes_updated": 4,
            "health_checks_active": True,
            "traffic_rerouted_percent": 85,
        }

    async def _execute_rollback(self, action: RemediationAction) -> dict:
        """Simulate deployment rollback."""
        await asyncio.sleep(2.0)
        return {
            "rollback_depth": 1,
            "previous_replicas_restored": 3,
            "readiness": True,
            "rollback_time_seconds": 30,
        }

    async def verify_recovery(
        self,
        incident_id: UUID,
        baseline_health: float,
    ) -> bool:
        """Verify that infrastructure has recovered."""
        await asyncio.sleep(1.0)

        # Simulated recovery verification
        current_health = baseline_health + (0.2 * (1 - baseline_health))
        is_recovered = current_health > 0.85

        await self.emit_event("recovery_verified", {
            "incident_id": str(incident_id),
            "baseline_health": baseline_health,
            "current_health": current_health,
            "recovered": is_recovered,
        })

        return is_recovered


autonomous_healer = AutonousSelfHealingEngine()
