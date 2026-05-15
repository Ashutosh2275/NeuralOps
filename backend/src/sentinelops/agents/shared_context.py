from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sentinelops.agents.base import AgentResult
from sentinelops.engines.rca import RCAResult
from sentinelops.events.schemas import BaseEvent


@dataclass
class SharedAgentMemory:
    """Shared context across all agents in an incident analysis run."""

    incident_id: UUID
    cluster_id: str
    namespace: str
    events: list[BaseEvent] = field(default_factory=list)
    topology: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    rca_result: RCAResult | None = None
    blast_radius: dict[str, Any] = field(default_factory=dict)
    cascade_chain: list[dict[str, Any]] = field(default_factory=list)
    agent_results: dict[str, AgentResult] = field(default_factory=dict)
    escalation_level: int = 0

    def to_prompt_context(self) -> str:
        lines = [
            f"Incident: {self.incident_id}",
            f"Namespace: {self.namespace}",
            f"Events: {len(self.events)}",
        ]
        if self.rca_result:
            lines.append(f"RCA: {self.rca_result.root_cause}")
            lines.append(f"Root service: {self.rca_result.root_service}")
            lines.append(f"Confidence: {self.rca_result.confidence:.2f}")
        if self.cascade_chain:
            lines.append(f"Cascade: {' -> '.join(c.get('service', '') for c in self.cascade_chain[:5])}")
        if self.blast_radius:
            lines.append(f"Blast radius: {self.blast_radius.get('count', 0)} nodes")
        if self.topology.get("nodes"):
            lines.append(f"Topology nodes: {len(self.topology['nodes'])}")
        return "\n".join(lines)
