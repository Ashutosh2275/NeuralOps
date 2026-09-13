from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent
from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.engines.rca import RCAEngine
from sentinelops.rag.engine import get_rag_engine


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

        # Multi-step investigation using tool calling engine
        inv_findings = []
        try:
            from sentinelops.investigation.engine import get_investigation_engine
            inv_engine = get_investigation_engine()
            target_pod = deterministic.origin_pod
            target_svc = deterministic.root_service if deterministic.root_service != "unknown" else None
            ns = context.events[0].namespace if context.events else "default"

            inv_state = await inv_engine.investigate(
                incident_id=getattr(context, "incident_id", None),
                target_service=target_svc,
                target_pod=target_pod,
                namespace=ns,
                trigger_reason=deterministic.root_cause,
                max_steps=5,
            )
            for e in inv_state.evidence:
                inv_findings.append(f"Tool Evidence [{e.source_tool}]: {e.summary}")
            if inv_state.final_root_cause:
                inv_findings.append(f"Autonomous Hypothesis: {inv_state.final_root_cause}")
        except Exception:
            pass

        findings.extend(inv_findings)

        # Retrieve relevant operational knowledge via RAG
        rag_evidence_text = ""
        try:
            rag = get_rag_engine()
            query = f"{deterministic.root_service} {deterministic.root_cause}"
            rag_context = await rag.retrieve_context(query, top_k=2)
            if rag_context.has_relevant_knowledge:
                rag_evidence_text = f"\nRelevant Operational Knowledge:\n{rag_context.context_text}"
                for c in rag_context.citations:
                    findings.append(f"Runbook Evidence: {c.title} ({c.section}) [score: {c.relevance_score:.2f}]")
        except Exception:
            pass

        prompt = (
            self._build_prompt(context)
            + f"\nDeterministic RCA: {deterministic.root_cause}"
            + rag_evidence_text
        )
        ai_enrichment = await self._ollama.generate(prompt)
        findings.append(f"AI enrichment: {ai_enrichment[:600]}")

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=findings,
            confidence=deterministic.confidence,
            raw_response=ai_enrichment,
        )
