import asyncio
from uuid import UUID

from sentinelops.agents.base import AgentContext, AgentResult
from sentinelops.agents.registry import AgentRegistry
from sentinelops.agents.shared_context import SharedAgentMemory
from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger
from sentinelops.engines.rca import RCAResult
from sentinelops.events.schemas import BaseEvent, Severity

log = get_logger(__name__)

AGENT_PIPELINE = [
    ("correlation", 0),
    ("cpu", 1),
    ("memory", 1),
    ("storage", 1),
    ("log", 1),
    ("rca", 2),
    ("recommendation", 3),
]


class AgentOrchestrator:
    """Multi-agent coordination with shared memory, escalation, and reasoning chains."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def run_incident_analysis(
        self,
        incident_id: UUID,
        cluster_id: str,
        namespace: str,
        events: list[BaseEvent],
        agent_types: list[str] | None = None,
        topology: dict | None = None,
        logs: list[str] | None = None,
        rca_result: RCAResult | None = None,
    ) -> list[AgentResult]:
        memory = SharedAgentMemory(
            incident_id=incident_id,
            cluster_id=cluster_id,
            namespace=namespace,
            events=events,
            topology=topology or {},
            logs=logs or [],
            rca_result=rca_result,
            cascade_chain=rca_result.cascade_chain if rca_result else [],
            blast_radius=rca_result.blast_radius if rca_result else {},
        )

        types = agent_types or [t for t, _ in AGENT_PIPELINE]
        if not self._settings.feature_ai_agents:
            types = [t for t in types if t not in ("rca", "recommendation", "log")]

        results: list[AgentResult] = []
        semaphore = asyncio.Semaphore(self._settings.ai_agent_concurrency)

        async def run_stage(stage: int) -> None:
            stage_agents = [t for t in types if self._pipeline_stage(t) == stage]
            stage_results = await asyncio.gather(*[
                self._run_agent(agent_type, memory, semaphore) for agent_type in stage_agents
            ])
            for r in stage_results:
                memory.agent_results[r.agent_type] = r
                results.append(r)
                if r.severity_escalation:
                    memory.escalation_level += 1

        stages = sorted({self._pipeline_stage(t) for t in types})
        for stage in stages:
            await run_stage(stage)

        return results

    def _pipeline_stage(self, agent_type: str) -> int:
        for t, stage in AGENT_PIPELINE:
            if t == agent_type:
                return stage
        return 1

    async def _run_agent(
        self,
        agent_type: str,
        memory: SharedAgentMemory,
        semaphore: asyncio.Semaphore,
    ) -> AgentResult:
        async with semaphore:
            try:
                agent = AgentRegistry.get(agent_type)
                context = AgentContext(
                    incident_id=memory.incident_id,
                    cluster_id=memory.cluster_id,
                    namespace=memory.namespace,
                    events=memory.events,
                    metrics=self._extract_metrics(memory.events),
                    logs=memory.logs,
                    topology=memory.topology,
                    rca_summary=memory.rca_result.root_cause if memory.rca_result else None,
                    shared_memory=memory.to_prompt_context(),
                    cascade_chain=memory.cascade_chain,
                    blast_radius=memory.blast_radius,
                )
                result = await agent.analyze(context)
                result.severity_escalation = any(
                    e.severity == Severity.CRITICAL for e in memory.events
                ) and agent_type in ("rca", "correlation")
                log.info("agent_completed", agent=agent_type, incident_id=str(memory.incident_id))
                return result
            except Exception as e:
                log.error("agent_failed", agent=agent_type, error=str(e))
                return AgentResult(agent_type=agent_type, success=False, findings=[str(e)])

    def _extract_metrics(self, events: list[BaseEvent]) -> dict:
        metrics: dict = {}
        for e in events:
            if e.event_type.value == "metric":
                key = e.payload.get("metric_name", "unknown")
                metrics[key] = e.payload.get("value")
        return metrics
