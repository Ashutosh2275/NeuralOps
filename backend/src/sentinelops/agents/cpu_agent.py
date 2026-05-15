from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent
from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.config import get_settings


class CPUAgent(BaseAgent):
    agent_type = "cpu"

    def __init__(self) -> None:
        self._ollama = OllamaClient()
        self._settings = get_settings()

    async def analyze(self, context: AgentContext) -> AgentResult:
        cpu_events = [
            e for e in context.events
            if e.payload.get("metric_name", "").startswith("cpu")
            or (e.payload.get("cpu_percent", 0) > self._settings.anomaly_cpu_threshold_percent)
        ]
        findings: list[str] = []
        recommendations: list[dict] = []

        for e in cpu_events:
            pct = e.payload.get("cpu_percent") or e.payload.get("value", 0)
            pod = e.payload.get("pod_name", "unknown")
            if pct > self._settings.anomaly_cpu_threshold_percent:
                findings.append(f"CPU saturation on {pod}: {pct}%")
                recommendations.append({
                    "title": f"Scale or throttle {pod}",
                    "action_type": "scale",
                    "kubectl_command": f"kubectl top pod {pod} -n {context.namespace}",
                    "priority": 1,
                })

        if self._settings.feature_ai_agents and findings:
            prompt = self._build_prompt(context)
            ai_response = await self._ollama.generate(prompt)
            findings.append(f"AI analysis: {ai_response[:500]}")

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No CPU anomalies detected"],
            recommendations=recommendations,
            confidence=0.8 if findings else 0.3,
        )
