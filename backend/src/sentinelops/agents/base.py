from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sentinelops.events.schemas import BaseEvent


@dataclass
class AgentContext:
    incident_id: UUID | None
    cluster_id: str
    namespace: str
    events: list[BaseEvent] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    topology: dict[str, Any] = field(default_factory=dict)
    rca_summary: str | None = None
    shared_memory: str | None = None
    cascade_chain: list[dict[str, Any]] = field(default_factory=list)
    blast_radius: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_type: str
    success: bool
    findings: list[str] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    raw_response: str | None = None
    severity_escalation: bool = False


class BaseAgent(ABC):
    agent_type: str = "base"

    @abstractmethod
    async def analyze(self, context: AgentContext) -> AgentResult:
        ...

    def _build_prompt(self, context: AgentContext) -> str:
        events_summary = "\n".join(
            f"- [{e.event_type}] {e.severity}: {e.payload}" for e in context.events[:20]
        )
        return f"""You are the {self.agent_type} agent for SentinelOps AI.
Analyze the following Kubernetes operational data and provide actionable findings.

Cluster: {context.cluster_id}
Namespace: {context.namespace}
RCA Summary: {context.rca_summary or 'N/A'}
Shared Context:
{context.shared_memory or 'N/A'}
Cascade: {context.cascade_chain[:3] if context.cascade_chain else 'none'}
Blast radius: {context.blast_radius.get('count', 0) if context.blast_radius else 0} nodes

Recent Events:
{events_summary}

Metrics: {context.metrics}
Topology nodes: {len(context.topology.get('nodes', []))}

Respond with:
1. Key findings (bullet points)
2. Root cause hypothesis
3. Recommended actions (with kubectl commands if applicable)
"""
