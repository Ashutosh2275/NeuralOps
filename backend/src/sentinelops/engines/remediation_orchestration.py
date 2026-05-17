import json
from datetime import datetime
from uuid import UUID

from sentinelops.models.predictive import RemediationOrchestration


class SmartRemediationOrchestrator:
    """Orchestrates multi-step remediation workflows intelligently."""

    def __init__(self):
        self.workflows = {}

    async def create_remediation_workflow(
        self,
        incident_id: UUID,
        recommended_actions: list[str],
        topology: dict,
        affected_services: list[str],
    ) -> RemediationOrchestration:
        """Create an orchestrated remediation workflow."""

        # Prioritize actions
        prioritized_actions = self._prioritize_actions(
            recommended_actions,
            topology,
            affected_services,
        )

        # Check for dependencies
        workflow_steps = self._build_workflow_steps(
            prioritized_actions,
            topology,
            affected_services,
        )

        # Assess rollback requirements
        rollback_needed = self._assess_rollback_requirement(prioritized_actions)

        # Calculate confidence
        confidence = self._calculate_workflow_confidence(
            workflow_steps,
            topology,
        )

        orchestration = RemediationOrchestration(
            incident_id=incident_id,
            workflow_json=json.dumps(workflow_steps),
            status="created",
            step_count=len(workflow_steps),
            completed_steps=0,
            rollback_required=rollback_needed,
            confidence_score=confidence,
            started_at=datetime.utcnow(),
        )

        self.workflows[str(incident_id)] = orchestration

        return orchestration

    async def execute_workflow_step(
        self,
        incident_id: UUID,
        step_index: int,
        workflow: RemediationOrchestration,
    ) -> dict:
        """Execute a single step in the workflow."""

        workflow_steps = json.loads(workflow.workflow_json)

        if step_index >= len(workflow_steps):
            return {
                "status": "completed",
                "message": "All steps completed",
            }

        step = workflow_steps[step_index]

        # Execute step (simulated)
        result = await self._execute_remediation_step(step)

        # Update workflow
        workflow.completed_steps += 1
        if workflow.completed_steps == workflow.step_count:
            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()
        else:
            workflow.status = "in_progress"

        return {
            "step_index": step_index,
            "step_type": step.get("action_type"),
            "status": "executed",
            "result": result,
            "workflow_progress": f"{workflow.completed_steps}/{workflow.step_count}",
        }

    async def validate_workflow_safety(
        self,
        workflow_steps: list[dict],
        topology: dict,
    ) -> dict:
        """Validate workflow won't cause additional harm."""

        issues = []

        # Check for risky action sequences
        for idx, step in enumerate(workflow_steps):
            action = step.get("action_type")

            # Restart followed by scale could cause thrashing
            if idx > 0:
                prev_action = workflow_steps[idx - 1].get("action_type")

                if prev_action == "pod_restart" and action == "replica_scaling":
                    issues.append({
                        "step_index": idx,
                        "issue": "Rapid scaling after restart could cause thrashing",
                        "recommendation": "Add delay or combine actions",
                    })

        # Check for dependency violations
        affected_services = set()
        for step in workflow_steps:
            target = step.get("target_service")
            if target:
                affected_services.add(target)

        # Check if we're affecting dependencies
        dependencies = topology.get("dependencies", {})
        for service in affected_services:
            dependents = dependencies.get(service, [])
            if dependents:
                issues.append({
                    "service": service,
                    "dependents": dependents,
                    "issue": f"{service} has {len(dependents)} dependents that will be affected",
                })

        is_safe = len(issues) == 0

        return {
            "is_safe": is_safe,
            "issues": issues,
            "safety_score": max(0.0, 1.0 - (len(issues) * 0.1)),
        }

    def _prioritize_actions(
        self,
        actions: list[str],
        topology: dict,
        affected_services: list[str],
    ) -> list[str]:
        """Prioritize remediation actions in safe order."""

        priority_map = {
            "isolate_workload": 1,  # First: isolate the problem
            "route_traffic": 2,      # Then: reroute traffic
            "pod_restart": 3,        # Then: restart pods
            "scale_replicas": 4,     # Then: scale up
            "monitor": 5,            # Finally: monitor
        }

        # Sort by priority
        sorted_actions = sorted(
            actions,
            key=lambda a: priority_map.get(a, 10),
        )

        return sorted_actions

    def _build_workflow_steps(
        self,
        actions: list[str],
        topology: dict,
        affected_services: list[str],
    ) -> list[dict]:
        """Build detailed workflow steps from actions."""

        steps = []

        for action in actions:
            step = {
                "action_type": action,
                "target_services": affected_services,
                "execution_order": len(steps),
            }

            # Add action-specific details
            if action == "isolate_workload":
                step["details"] = {
                    "strategy": "namespace",
                    "qos_class": "Guaranteed",
                }
            elif action == "route_traffic":
                step["details"] = {
                    "strategy": "round_robin",
                    "health_check_interval": 5,
                }
            elif action == "pod_restart":
                step["details"] = {
                    "grace_period": 30,
                    "max_retries": 3,
                }
            elif action == "scale_replicas":
                step["details"] = {
                    "scale_factor": 1.5,
                    "max_replicas": 10,
                }

            steps.append(step)

        return steps

    def _assess_rollback_requirement(self, actions: list[str]) -> bool:
        """Determine if rollback capability is needed."""

        # Rollback needed for scaling or configuration changes
        risky_actions = {"scale_replicas", "modify_config", "rollback_deployment"}

        return any(action in risky_actions for action in actions)

    def _calculate_workflow_confidence(
        self,
        workflow_steps: list[dict],
        topology: dict,
    ) -> float:
        """Calculate confidence in workflow success."""

        # Base confidence
        confidence = 0.8

        # More steps = lower confidence
        confidence -= min(0.2, len(workflow_steps) * 0.05)

        # Complex topologies = lower confidence
        dependency_count = sum(len(v) for v in topology.get("dependencies", {}).values())
        confidence -= min(0.1, dependency_count * 0.01)

        return max(0.3, confidence)

    async def _execute_remediation_step(self, step: dict) -> dict:
        """Execute a remediation step (simulated)."""

        action_type = step.get("action_type")

        # Simulate execution based on action type
        if action_type == "pod_restart":
            return {"pods_restarted": 3, "time_seconds": 12}
        elif action_type == "scale_replicas":
            return {"new_replicas": 5, "time_seconds": 45}
        elif action_type == "isolate_workload":
            return {"pods_isolated": 5, "time_seconds": 8}
        elif action_type == "route_traffic":
            return {"routes_updated": 4, "time_seconds": 3}

        return {"status": "executed"}


remediation_orchestrator = SmartRemediationOrchestrator()
