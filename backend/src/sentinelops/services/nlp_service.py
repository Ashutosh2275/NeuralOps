import json
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.core.logging import get_logger
from sentinelops.models.incident import Incident
from sentinelops.models.intelligence import AIInsight
from sentinelops.models.recommendation import Recommendation

log = get_logger(__name__)

SYSTEM_PROMPT = """You are SentinelOps AI, a Kubernetes operational intelligence assistant.
Answer using incident data, RCA, topology, and dependency context provided.
Be concise. Include kubectl commands when actionable."""

INTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("why_failed", re.compile(r"why did .+ fail|what caused|root cause", re.I)),
    ("which_pod", re.compile(r"which pod caused|origin pod|triggered", re.I)),
    ("affected", re.compile(r"which services were affected|blast radius|downstream", re.I)),
    ("cpu_spike", re.compile(r"cpu spike|high cpu|cpu usage", re.I)),
    ("replay", re.compile(r"replay|show timeline|playback", re.I)),
    ("dependency", re.compile(r"dependency|restart loop|cascade", re.I)),
    ("remediation", re.compile(r"fix|recommend|remediat|what should", re.I)),
]


class NLPInfrastructureService:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._ollama = OllamaClient()
        self._session = session

    def _detect_intent(self, question: str) -> str:
        for intent, pattern in INTENT_PATTERNS:
            if pattern.search(question):
                return intent
        return "general"

    async def _build_context(self, question: str, namespace: str | None) -> dict:
        ctx: dict = {"namespace": namespace or "default", "intent": self._detect_intent(question)}
        if not self._session:
            return ctx

        incident_id_match = re.search(r"incident[:\s#]*([a-f0-9-]{36})", question, re.I)
        service_match = re.search(r"([\w-]+-service)", question, re.I)

        if incident_id_match:
            iid = UUID(incident_id_match.group(1))
            result = await self._session.execute(select(Incident).where(Incident.id == iid))
            incident = result.scalar_one_or_none()
            if incident:
                ctx["incident"] = {
                    "id": str(incident.id),
                    "title": incident.title,
                    "root_cause": incident.root_cause,
                    "root_service": incident.root_service,
                    "confidence": incident.confidence_score,
                    "cascade": json.loads(incident.cascade_chain_json or "[]"),
                }
            insights = await self._session.execute(
                select(AIInsight).where(AIInsight.incident_id == iid).limit(10)
            )
            ctx["insights"] = [{"agent": i.agent_type, "content": i.content} for i in insights.scalars()]
            recs = await self._session.execute(
                select(Recommendation).where(Recommendation.incident_id == iid).limit(5)
            )
            ctx["recommendations"] = [
                {"title": r.title, "command": r.kubectl_command} for r in recs.scalars()
            ]

        if service_match:
            ctx["service"] = service_match.group(1)

        open_incidents = await self._session.execute(
            select(Incident).where(Incident.status.in_(("open", "investigating"))).limit(5)
        )
        ctx["open_incidents"] = [
            {"id": str(i.id), "title": i.title, "severity": i.severity}
            for i in open_incidents.scalars()
        ]
        return ctx

    async def query(self, question: str, namespace: str | None = None) -> dict:
        context = await self._build_context(question, namespace)
        intent = context["intent"]

        if intent == "replay" and context.get("incident"):
            return {
                "question": question,
                "answer": f"Open replay at /replay/{context['incident']['id']} for incident timeline and topology playback.",
                "intent": intent,
                "incident_id": context["incident"]["id"],
                "sources": ["incident_db"],
            }

        prompt = f"""Question: {question}
Intent: {intent}
Context: {json.dumps(context, default=str)}

Provide: summary, root cause if known, affected services, and top 3 remediation steps."""
        answer = await self._ollama.generate(prompt, system=SYSTEM_PROMPT)
        log.info("nlp_query_answered", intent=intent)
        return {
            "question": question,
            "answer": answer,
            "intent": intent,
            "sources": ["ollama", "incident_db"] if context.get("incident") else ["ollama"],
            "context": context,
        }
