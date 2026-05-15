from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent


class CorrelationAgent(BaseAgent):
    agent_type = "correlation"

    async def analyze(self, context: AgentContext) -> AgentResult:
        by_type: dict[str, int] = {}
        for e in context.events:
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1

        findings = [
            f"Event distribution: {by_type}",
            f"Total correlated events: {len(context.events)}",
        ]
        if len(by_type) >= 3:
            findings.append("Multi-signal correlation detected — likely cascading failure")

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings,
            confidence=0.6,
        )
