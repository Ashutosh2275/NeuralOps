"""Advanced Remediation Orchestrator - Multi-step healing workflows with safety validation"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class RemediationAction(str, Enum):
    """Available remediation actions"""
    ISOLATE_WORKLOAD = "isolate_workload"
    RESTART_POD = "restart_pod"
    SCALE_REPLICAS = "scale_replicas"
    UPDATE_CONFIG = "update_config"
    ROUTE_TRAFFIC = "route_traffic"
    CHECK_DEPENDENCY = "check_dependency"
    MONITOR = "monitor"
    ROLLBACK = "rollback"


class RemediationStep:
    """Represents one step in remediation workflow"""

    def __init__(
        self,
        step_index: int,
        action: RemediationAction,
        target_services: list[str],
        validation_checks: list[str],
        rollback_plan: Optional[dict] = None,
        estimated_duration_seconds: int = 60,
    ):
        self.step_index = step_index
        self.action = action
        self.target_services = target_services
        self.validation_checks = validation_checks
        self.rollback_plan = rollback_plan or {}
        self.estimated_duration_seconds = estimated_duration_seconds
        self.status = "pending"
        self.started_at = None
        self.completed_at = None
        self.result = None


class RemediationWorkflow:
    """Multi-step remediation workflow"""

    def __init__(
        self,
        incident_id: UUID,
        root_cause: str,
        affected_services: list[str],
        cascade_chain: list[str],
    ):
        self.id = uuid4()
        self.incident_id = incident_id
        self.root_cause = root_cause
        self.affected_services = affected_services
        self.cascade_chain = cascade_chain
        self.steps: list[RemediationStep] = []
        self.status = "created"
        self.confidence = 0.0
        self.rollback_required = False
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None


class AdvancedRemediationOrchestrator:
    """Orchestrates multi-step remediation workflows"""

    # Action priority order
    ACTION_PRIORITY = {
        RemediationAction.ISOLATE_WORKLOAD: 1,       # First: prevent cascade
        RemediationAction.ROUTE_TRAFFIC: 2,          # Then: redirect traffic
        RemediationAction.CHECK_DEPENDENCY: 3,       # Then: verify dependencies
        RemediationAction.RESTART_POD: 4,            # Then: restart
        RemediationAction.SCALE_REPLICAS: 5,         # Then: scale
        RemediationAction.UPDATE_CONFIG: 6,          # Then: config changes
        RemediationAction.MONITOR: 7,                # Finally: monitor
    }

    # Action to validation checks mapping
    ACTION_VALIDATIONS = {
        RemediationAction.ISOLATE_WORKLOAD: [
            "pod_not_critical",
            "traffic_drainable",
            "no_single_replica",
        ],
        RemediationAction.RESTART_POD: [
            "pod_restartable",
            "grace_period_sufficient",
            "liveness_probe_ok",
        ],
        RemediationAction.SCALE_REPLICAS: [
            "cluster_has_capacity",
            "max_replicas_not_exceeded",
            "load_balancer_healthy",
        ],
        RemediationAction.ROUTE_TRAFFIC: [
            "backup_service_healthy",
            "traffic_rules_applicable",
            "dns_resolvable",
        ],
    }

    async def create_workflow(
        self,
        incident_id: UUID,
        root_cause: str,
        affected_services: list[str],
        cascade_chain: list[str],
        topology: dict,
    ) -> RemediationWorkflow:
        """Create remediation workflow"""

        workflow = RemediationWorkflow(
            incident_id=incident_id,
            root_cause=root_cause,
            affected_services=affected_services,
            cascade_chain=cascade_chain,
        )

        # Generate candidate actions
        candidate_actions = await self._generate_candidate_actions(root_cause)

        # Sequence actions by dependency
        sequenced_actions = self._sequence_actions(candidate_actions)

        # Create steps
        for step_index, action in enumerate(sequenced_actions):
            step = RemediationStep(
                step_index=step_index,
                action=action,
                target_services=affected_services,
                validation_checks=self.ACTION_VALIDATIONS.get(action, []),
                rollback_plan=await self._plan_rollback(action, affected_services),
                estimated_duration_seconds=self._estimate_duration(action),
            )
            workflow.steps.append(step)

        # Validate workflow safety
        safety = await self.validate_workflow_safety(workflow, topology)
        workflow.rollback_required = not safety["is_safe"]

        # Calculate confidence
        workflow.confidence = self._calculate_confidence(workflow, safety)

        logger.info(
            f"Created workflow for incident {incident_id}: {len(workflow.steps)} steps, "
            f"confidence={workflow.confidence:.2f}, rollback_required={workflow.rollback_required}"
        )

        return workflow

    async def _generate_candidate_actions(self, root_cause: str) -> list[RemediationAction]:
        """Generate candidate actions for root cause"""

        # Map root causes to actions
        cause_to_actions = {
            "pod_crash": [
                RemediationAction.RESTART_POD,
                RemediationAction.SCALE_REPLICAS,
            ],
            "memory_leak": [
                RemediationAction.RESTART_POD,
                RemediationAction.UPDATE_CONFIG,
            ],
            "cascading_failure": [
                RemediationAction.ISOLATE_WORKLOAD,
                RemediationAction.ROUTE_TRAFFIC,
                RemediationAction.RESTART_POD,
            ],
            "high_cpu": [
                RemediationAction.SCALE_REPLICAS,
                RemediationAction.UPDATE_CONFIG,
            ],
            "dependency_failure": [
                RemediationAction.CHECK_DEPENDENCY,
                RemediationAction.ROUTE_TRAFFIC,
            ],
        }

        # Find matching cause
        for cause_pattern, actions in cause_to_actions.items():
            if cause_pattern.lower() in root_cause.lower():
                return actions

        # Default: restart and monitor
        return [RemediationAction.RESTART_POD, RemediationAction.MONITOR]

    def _sequence_actions(self, actions: list[RemediationAction]) -> list[RemediationAction]:
        """Sequence actions by priority"""
        return sorted(
            actions,
            key=lambda a: self.ACTION_PRIORITY.get(a, 99),
        )

    async def _plan_rollback(
        self,
        action: RemediationAction,
        affected_services: list[str],
    ) -> dict:
        """Plan rollback for action"""

        rollback_plans = {
            RemediationAction.SCALE_REPLICAS: {
                "action": "scale_replicas",
                "params": {"scale_factor": 0.5},
            },
            RemediationAction.UPDATE_CONFIG: {
                "action": "restore_config",
                "params": {"restore_previous": True},
            },
            RemediationAction.ROUTE_TRAFFIC: {
                "action": "restore_traffic_rules",
                "params": {},
            },
        }

        return rollback_plans.get(action, {})

    def _estimate_duration(self, action: RemediationAction) -> int:
        """Estimate action duration in seconds"""

        durations = {
            RemediationAction.ISOLATE_WORKLOAD: 15,
            RemediationAction.RESTART_POD: 30,
            RemediationAction.SCALE_REPLICAS: 60,
            RemediationAction.UPDATE_CONFIG: 45,
            RemediationAction.ROUTE_TRAFFIC: 10,
            RemediationAction.CHECK_DEPENDENCY: 20,
            RemediationAction.MONITOR: 120,
            RemediationAction.ROLLBACK: 60,
        }

        return durations.get(action, 60)

    async def validate_workflow_safety(
        self,
        workflow: RemediationWorkflow,
        topology: dict,
    ) -> dict:
        """Validate workflow won't cause harm"""

        issues = []

        # Check for risky sequences
        for i in range(1, len(workflow.steps)):
            prev_action = workflow.steps[i - 1].action
            curr_action = workflow.steps[i].action

            # Restart followed by scale could cause thrashing
            if (
                prev_action == RemediationAction.RESTART_POD
                and curr_action == RemediationAction.SCALE_REPLICAS
            ):
                issues.append({
                    "step_index": i,
                    "issue": "Rapid scaling after restart could cause thrashing",
                    "recommendation": "Add delay or combine actions",
                    "severity": "warning",
                })

        # Check if affecting critical services
        critical_patterns = ["database", "auth", "gateway", "core"]
        for service in workflow.affected_services:
            if any(pattern in service.lower() for pattern in critical_patterns):
                issues.append({
                    "service": service,
                    "issue": f"Affecting critical service {service}",
                    "recommendation": "Ensure backup/failover is active",
                    "severity": "warning",
                })

        # Check dependencies
        dependencies = topology.get("dependencies", {})
        for service in workflow.affected_services:
            dependents = dependencies.get(service, [])
            if dependents:
                issues.append({
                    "service": service,
                    "dependents": dependents,
                    "issue": f"{service} has {len(dependents)} dependent services",
                    "recommendation": "Monitor dependent services during remediation",
                    "severity": "info",
                })

        is_safe = not any(i.get("severity") == "error" for i in issues)
        safety_score = max(0.0, 1.0 - (len(issues) * 0.1))

        return {
            "is_safe": is_safe,
            "issues": issues,
            "safety_score": safety_score,
        }

    def _calculate_confidence(self, workflow: RemediationWorkflow, safety: dict) -> float:
        """Calculate workflow success confidence"""

        # Base confidence
        confidence = 0.8

        # Reduce by number of steps
        confidence -= min(0.2, len(workflow.steps) * 0.05)

        # Reduce by safety issues
        confidence -= safety.get("issues", [])
        confidence *= safety.get("safety_score", 1.0)

        return max(0.3, confidence)

    async def execute_step(
        self,
        workflow: RemediationWorkflow,
        step_index: int,
    ) -> dict:
        """Execute workflow step"""

        if step_index >= len(workflow.steps):
            return {
                "status": "completed",
                "message": "All steps completed",
                "workflow_status": "completed",
            }

        step = workflow.steps[step_index]
        step.status = "executing"
        step.started_at = datetime.utcnow()

        try:
            # Simulate execution
            result = await self._execute_action(step.action, step.target_services)

            step.result = result
            step.status = "completed"
            step.completed_at = datetime.utcnow()

            # Update workflow progress
            completed = sum(1 for s in workflow.steps if s.status == "completed")
            if completed == len(workflow.steps):
                workflow.status = "completed"
                workflow.completed_at = datetime.utcnow()
            else:
                workflow.status = "in_progress"

            logger.info(f"Step {step_index} executed: {step.action}")

            return {
                "step_index": step_index,
                "status": "executed",
                "result": result,
                "workflow_progress": f"{completed}/{len(workflow.steps)}",
            }

        except Exception as e:
            step.status = "failed"
            logger.error(f"Step {step_index} failed: {e}")
            return {
                "step_index": step_index,
                "status": "failed",
                "error": str(e),
            }

    async def _execute_action(self, action: RemediationAction, services: list[str]) -> dict:
        """Execute action (simulated)"""

        execution_results = {
            RemediationAction.RESTART_POD: {
                "pods_restarted": len(services) * 3,
                "time_seconds": 12,
                "status": "success",
            },
            RemediationAction.SCALE_REPLICAS: {
                "new_replicas": len(services) * 5,
                "time_seconds": 45,
                "status": "success",
            },
            RemediationAction.ISOLATE_WORKLOAD: {
                "pods_isolated": len(services) * 2,
                "time_seconds": 8,
                "status": "success",
            },
            RemediationAction.ROUTE_TRAFFIC: {
                "routes_updated": len(services),
                "time_seconds": 3,
                "status": "success",
            },
            RemediationAction.MONITOR: {
                "monitoring_active": True,
                "time_seconds": 5,
                "status": "success",
            },
        }

        return execution_results.get(action, {"status": "executed"})


# Singleton instance
advanced_remediation_orchestrator = AdvancedRemediationOrchestrator()
