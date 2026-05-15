import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from sentinelops.ai.ollama_client import OllamaClient
from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent

log = get_logger(__name__)


@dataclass
class AIAgentContext:
    """Context passed to all AI agents."""

    incident_id: UUID
    cluster_id: str
    namespace: str
    events: list[BaseEvent] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    topology: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    rca_summary: str | None = None
    cascade_chain: list[dict] = field(default_factory=list)
    blast_radius: dict[str, Any] = field(default_factory=dict)
    infrastructure_memory: dict[str, Any] = field(default_factory=dict)
    previous_incidents: list[dict] = field(default_factory=list)


@dataclass
class AIAgentResult:
    """Result from AI agent execution."""

    agent_type: str
    success: bool
    findings: list[str] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.5
    raw_response: str | None = None
    tokens_used: int = 0
    latency_ms: int = 0
    model_used: str = ""


class AIAgent(ABC):
    """Base class for all AI agents."""

    agent_type: str = "base"
    description: str = "Base AI Agent"

    def __init__(self) -> None:
        self._ollama = OllamaClient()
        self._settings = get_settings()

    @abstractmethod
    async def analyze(self, context: AIAgentContext) -> AIAgentResult:
        """Analyze infrastructure data and return findings."""
        ...

    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent."""
        return f"""You are the {self.agent_type} agent for SentinelOps AI.
You are a specialist in infrastructure operations and analysis.
Provide concise, actionable insights based on operational data.
Always explain your reasoning.
Be conservative with confidence scores - only report high confidence if evidence is strong."""

    def _build_prompt(self, context: AIAgentContext) -> str:
        """Build the analysis prompt. Override in subclasses."""
        events_summary = "\n".join(
            f"- [{e.event_type.value}] {e.severity.value}: {e.payload.get('reason', str(e.payload)[:80])}"
            for e in context.events[:10]
        )

        return f"""Analyze this infrastructure incident:

Cluster: {context.cluster_id}
Namespace: {context.namespace}

Recent Events:
{events_summary}

Metrics: {json.dumps(context.metrics, indent=2)[:500]}

Topology Nodes: {len(context.topology.get('nodes', []))}
Dependencies: {', '.join(context.dependencies[:5])}

Previous Similar Incidents: {len(context.previous_incidents)}

Provide:
1. Key findings
2. Root cause hypothesis
3. Confidence (0.0-1.0)
4. Recommended actions"""

    async def _query_ollama(
        self, prompt: str, system: str | None = None, max_tokens: int = 1024
    ) -> tuple[str, dict]:
        """Query Ollama with safety checks."""
        system = system or self._build_system_prompt()
        response, metadata = await self._ollama.generate(
            prompt, system, max_tokens=max_tokens, temperature=0.3
        )
        return response, metadata

    def _parse_confidence(self, response: str) -> float:
        """Extract confidence score from response."""
        import re

        patterns = [
            r"confidence[:\s]+(\d+\.?\d*)",
            r"(\d+\.?\d*)%?\s+(?:confidence|confident)",
            r"score[:\s]+(\d+\.?\d*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, response.lower())
            if match:
                try:
                    conf = float(match.group(1))
                    return min(1.0, max(0.0, conf / 100 if conf > 1 else conf))
                except ValueError:
                    continue

        return 0.5

    def _extract_recommendations(self, response: str) -> list[dict[str, Any]]:
        """Extract recommendations from response."""
        recommendations = []
        lines = response.split("\n")

        for i, line in enumerate(lines):
            if "recommend" in line.lower() or "action" in line.lower():
                rec = {"title": line.strip(), "priority": 2}
                if i + 1 < len(lines):
                    rec["description"] = lines[i + 1].strip()
                recommendations.append(rec)

        return recommendations[:5]
