from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent
from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.engines.rca import RCAEngine


class RCAAgent(BaseAgent):
    agent_type = "rca"

    def __init__(self) -> None:
        self._ollama = OllamaClient()
        self._rca_engine = RCAEngine()

    async def analyze(self, context: AgentContext) -> AgentResult:
        deterministic = self._rca_engine.analyze(context.events)
        findings = [
            f"Deterministic RCA: {deterministic.root_cause}",
            f"Root service: {deterministic.root_service}",
            f"Confidence: {deterministic.confidence:.2f}",
            *deterministic.evidence,
        ]

        prompt = self._build_prompt(context) + f"\nDeterministic RCA: {deterministic.root_cause}"
        ai_enrichment = await self._ollama.generate(prompt)
        findings.append(f"AI enrichment: {ai_enrichment[:600]}")

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings,
            confidence=deterministic.confidence,
            raw_response=ai_enrichment,
        )
