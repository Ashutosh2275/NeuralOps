from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent
from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.rag.engine import get_rag_engine


class RecommendationAgent(BaseAgent):
    agent_type = "recommendation"

    def __init__(self) -> None:
        self._ollama = OllamaClient()

    async def analyze(self, context: AgentContext) -> AgentResult:
        rag_evidence_text = ""
        try:
            rag = get_rag_engine()
            query = f"Remediation steps for {context.rca_summary or 'Kubernetes pod failure'}"
            rag_context = await rag.retrieve_context(query, top_k=2)
            if rag_context.has_relevant_knowledge:
                rag_evidence_text = f"\nVerified Operational Runbooks:\n{rag_context.context_text}"
        except Exception:
            pass

        prompt = f"""You are a Kubernetes SRE. Given this incident context and verified operational runbooks, provide 3 prioritized remediation steps.

RCA: {context.rca_summary}
Namespace: {context.namespace}
Events: {len(context.events)}
{rag_evidence_text}

Format each recommendation as:
- TITLE: <short title>
- ACTION: <action_type>
- KUBECTL: <command or N/A>
- PRIORITY: <1-3>
"""
        response = await self._ollama.generate(prompt)
        recommendations = self._parse_recommendations(response)

        return AgentResult(
            agent_type=self.agent_type,
            success=True,
            findings=[f"Generated {len(recommendations)} recommendations"],
            recommendations=recommendations,
            confidence=0.7,
            raw_response=response,
        )

    def _parse_recommendations(self, text: str) -> list[dict]:
        recs: list[dict] = []
        current: dict = {}
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- TITLE:"):
                if current:
                    recs.append(current)
                current = {"title": line.replace("- TITLE:", "").strip()}
            elif line.startswith("- ACTION:"):
                current["action_type"] = line.replace("- ACTION:", "").strip()
            elif line.startswith("- KUBECTL:"):
                cmd = line.replace("- KUBECTL:", "").strip()
                current["kubectl_command"] = cmd if cmd != "N/A" else None
            elif line.startswith("- PRIORITY:"):
                try:
                    current["priority"] = int(line.replace("- PRIORITY:", "").strip())
                except ValueError:
                    current["priority"] = 2
        if current:
            recs.append(current)
        if not recs:
            recs.append({
                "title": "Review pod events and logs",
                "action_type": "investigate",
                "kubectl_command": "kubectl get events --all-namespaces",
                "priority": 1,
            })
        return recs
