from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent


class StorageAgent(BaseAgent):
    agent_type = "storage"

    async def analyze(self, context: AgentContext) -> AgentResult:
        storage_events = [
            e for e in context.events
            if "pvc" in str(e.payload).lower() or "disk" in e.payload.get("metric_name", "").lower()
        ]
        findings: list[str] = []
        recommendations: list[dict] = []

        for e in storage_events:
            pod = e.payload.get("pod_name", "unknown")
            usage = e.payload.get("disk_usage_bytes") or e.payload.get("value")
            if usage:
                findings.append(f"Storage stress on {pod}: {usage} bytes used")
                recommendations.append({
                    "title": f"Check PVC capacity for {pod}",
                    "action_type": "inspect",
                    "kubectl_command": f"kubectl get pvc -n {context.namespace}",
                    "priority": 2,
                })

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No storage/PVC anomalies detected"],
            recommendations=recommendations,
            confidence=0.7 if findings else 0.3,
        )
