from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent
from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.config import get_settings


class MemoryAgent(BaseAgent):
    agent_type = "memory"

    def __init__(self) -> None:
        self._ollama = OllamaClient()
        self._settings = get_settings()

    async def analyze(self, context: AgentContext) -> AgentResult:
        mem_events = [
            e for e in context.events
            if "memory" in e.payload.get("metric_name", "").lower()
            or e.payload.get("memory_percent", 0) > self._settings.anomaly_memory_threshold_percent
        ]
        findings: list[str] = []
        recommendations: list[dict] = []

        for e in mem_events:
            pct = e.payload.get("memory_percent") or e.payload.get("value", 0)
            pod = e.payload.get("pod_name", "unknown")
            if pct > self._settings.anomaly_memory_threshold_percent:
                findings.append(f"Memory pressure on {pod}: {pct}%")
                recommendations.append({
                    "title": f"Investigate memory leak in {pod}",
                    "action_type": "investigate",
                    "kubectl_command": f"kubectl describe pod {pod} -n {context.namespace}",
                    "priority": 1,
                })

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No memory anomalies detected"],
            recommendations=recommendations,
            confidence=0.75 if findings else 0.3,
        )
