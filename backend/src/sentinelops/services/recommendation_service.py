import json
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.agents.base import AgentResult
from sentinelops.engines.rca import RCAResult
from sentinelops.models.recommendation import Recommendation


class RecommendationService:
    """Deterministic recommendations enhanced by AI agent output."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def generate_deterministic(self, rca: RCAResult, namespace: str) -> list[dict]:
        recs: list[dict] = []
        if rca.origin_pod:
            recs.append({
                "title": f"Investigate pod {rca.origin_pod}",
                "description": rca.root_cause,
                "action_type": "investigate",
                "kubectl_command": f"kubectl describe pod {rca.origin_pod} -n {namespace}",
                "priority": 1,
                "confidence": rca.confidence,
            })
        blast_count = rca.blast_radius.get("affected_count", 0) if isinstance(rca.blast_radius, dict) else 0
        if blast_count > 2:
            recs.append({
                "title": "Cascading failure detected — isolate blast radius",
                "description": f"{blast_count} downstream dependencies affected",
                "action_type": "mitigate",
                "kubectl_command": f"kubectl get pods -n {namespace} -o wide",
                "priority": 1,
                "confidence": 0.85,
            })
        if "memory" in rca.root_cause.lower() or "oom" in rca.root_cause.lower():
            recs.append({
                "title": "Increase memory limits or fix memory leak",
                "action_type": "scale",
                "kubectl_command": f"kubectl top pods -n {namespace}",
                "priority": 2,
                "confidence": 0.8,
            })
        if "cpu" in rca.root_cause.lower():
            recs.append({
                "title": "Scale workload or reduce CPU pressure",
                "action_type": "scale",
                "kubectl_command": f"kubectl autoscale deployment -n {namespace}",
                "priority": 2,
                "confidence": 0.75,
            })
        if "pvc" in rca.root_cause.lower() or "storage" in rca.root_cause.lower():
            recs.append({
                "title": "Check PVC capacity and expand if needed",
                "action_type": "inspect",
                "kubectl_command": f"kubectl get pvc -n {namespace}",
                "priority": 1,
                "confidence": 0.8,
            })
        if not recs:
            recs.append({
                "title": "Review cluster events and logs",
                "action_type": "investigate",
                "kubectl_command": f"kubectl get events -n {namespace} --sort-by=.lastTimestamp",
                "priority": 2,
                "confidence": 0.5,
            })
        return recs

    async def persist(
        self,
        incident_id: UUID,
        deterministic: list[dict],
        agent_results: list[AgentResult],
    ) -> list[Recommendation]:
        saved: list[Recommendation] = []
        for rec in deterministic:
            row = Recommendation(
                id=uuid4(),
                incident_id=incident_id,
                agent_type="deterministic",
                priority=rec.get("priority", 2),
                title=rec["title"],
                description=rec.get("description", rec["title"]),
                action_type=rec.get("action_type", "investigate"),
                kubectl_command=rec.get("kubectl_command"),
                confidence=rec.get("confidence", 0.7),
            )
            self._session.add(row)
            saved.append(row)

        for result in agent_results:
            for rec in result.recommendations:
                row = Recommendation(
                    id=uuid4(),
                    incident_id=incident_id,
                    agent_type=result.agent_type,
                    priority=rec.get("priority", 2),
                    title=rec.get("title", "AI recommendation"),
                    description=rec.get("description", rec.get("title", "")),
                    action_type=rec.get("action_type", "investigate"),
                    kubectl_command=rec.get("kubectl_command"),
                    confidence=result.confidence,
                )
                self._session.add(row)
                saved.append(row)

        await self._session.flush()
        return saved

    async def list_for_incident(self, incident_id: UUID) -> list[Recommendation]:
        result = await self._session.execute(
            select(Recommendation)
            .where(Recommendation.incident_id == incident_id)
            .order_by(Recommendation.priority)
        )
        return list(result.scalars().all())
