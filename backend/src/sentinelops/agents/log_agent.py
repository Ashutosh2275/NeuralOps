from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent
from sentinelops.agents.ollama_client import OllamaClient


class LogIntelligenceAgent(BaseAgent):
    agent_type = "log"

    def __init__(self) -> None:
        self._ollama = OllamaClient()

    async def analyze(self, context: AgentContext) -> AgentResult:
        findings: list[str] = []
        error_patterns = ("OOMKilled", "CrashLoopBackOff", "connection refused", "timeout", "panic")

        for line in context.logs[:100]:
            for pattern in error_patterns:
                if pattern.lower() in line.lower():
                    findings.append(f"Log pattern detected: {pattern} — {line[:120]}")
                    break

        if context.logs and len(findings) < 3:
            prompt = f"Summarize these K8s error logs and identify root cause:\n" + "\n".join(context.logs[:30])
            summary = await self._ollama.generate(prompt)
            findings.append(f"AI log summary: {summary[:400]}")

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings or ["No critical log patterns detected"],
            recommendations=[],
            confidence=0.65 if findings else 0.2,
        )
