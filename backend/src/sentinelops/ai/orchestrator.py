import asyncio
from uuid import UUID

from sentinelops.ai.base import AIAgentContext, AIAgentResult
from sentinelops.ai.registry import AIAgentRegistry, AISafetyValidator
from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent

log = get_logger(__name__)


class AIOrchestrator:
    """Orchestrates multi-agent AI reasoning with scheduling and validation."""

    # Agent execution pipeline: stage -> [(agent_type, priority), ...]
    PIPELINE = [
        (0, [("cpu", 1), ("memory", 1), ("correlation", 2), ("storage", 1), ("network", 1), ("logs", 1)]),
        (1, [("rca", 1), ("npl_assistant", 2)]),
        (2, [("recommendation", 1)]),
        (3, [("summarization", 1)]),
    ]

    def __init__(self) -> None:
        self._settings = get_settings()
        self._registry = AIAgentRegistry()

    async def orchestrate(
        self,
        incident_id: UUID,
        cluster_id: str,
        namespace: str,
        events: list[BaseEvent],
        topology: dict | None = None,
        cascade_chain: list[dict] | None = None,
        rca_summary: str | None = None,
    ) -> dict:
        """Execute AI agents in orchestrated stages."""
        context = AIAgentContext(
            incident_id=incident_id,
            cluster_id=cluster_id,
            namespace=namespace,
            events=events,
            topology=topology or {},
            cascade_chain=cascade_chain or [],
            rca_summary=rca_summary,
            dependencies=self._extract_dependencies(topology or {}),
        )

        results = {}
        semaphore = asyncio.Semaphore(self._settings.ai_agent_concurrency)

        for stage_num, stage_agents in self.PIPELINE:
            stage_results = await asyncio.gather(*[
                self._execute_agent(agent_type, context, semaphore)
                for agent_type, _priority in stage_agents
                if self._settings.feature_ai_agents
            ])

            for result in stage_results:
                results[result.agent_type] = result

                # Validate response
                is_valid, error = AISafetyValidator.validate_response(
                    result.raw_response or "",
                    context.dependencies,
                    [e.payload.get("pod_name", "") for e in events],
                )
                if not is_valid:
                    log.warning(f"ai_response_validation_failed_{result.agent_type}", error=error)
                    result.confidence *= 0.8

        return results

    async def _execute_agent(
        self,
        agent_type: str,
        context: AIAgentContext,
        semaphore: asyncio.Semaphore,
    ) -> AIAgentResult:
        """Execute a single agent with semaphore control."""
        async with semaphore:
            try:
                agent = self._registry.get(agent_type)
                result = await agent.analyze(context)
                log.info(f"ai_agent_completed_{agent_type}", confidence=result.confidence)
                return result
            except Exception as e:
                log.error(f"ai_agent_failed_{agent_type}", error=str(e))
                return AIAgentResult(
                    agent_type=agent_type,
                    success=False,
                    findings=[f"Agent execution failed: {str(e)[:100]}"],
                    confidence=0.0,
                )

    def _extract_dependencies(self, topology: dict) -> list[str]:
        """Extract service names from topology."""
        dependencies = set()
        for node in topology.get("nodes", []):
            name = node.get("name", "")
            if name and not name.startswith("default"):
                dependencies.add(name)
        return list(dependencies)
