from sentinelops.agents.base import AgentContext, AgentResult, BaseAgent
from sentinelops.agents.ollama_client import OllamaClient


class RecommendationAgent(BaseAgent):
    agent_type = "recommendation"

    def __init__(self) -> None:
        self._ollama = OllamaClient()

    async def analyze(self, context: AgentContext) -> AgentResult:
        prompt = f"""You are a Kubernetes SRE. Given this incident context, provide 3 prioritized remediation steps.

RCA: {context.rca_summary}
Namespace: {context.namespace}
Events: {len(context.events)}

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
