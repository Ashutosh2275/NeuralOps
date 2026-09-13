"""
Investigation state models for SentinelOps AI Autonomous Investigation Engine.
Tracks evidence items, dynamic hypotheses, reasoning steps, tool audit records, and final conclusions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sentinelops.tools.base import ToolCallRecord


class EvidenceType(str, Enum):
    K8S_STATUS = "k8s_status"
    POD_LOGS = "pod_logs"
    K8S_EVENT = "k8s_event"
    METRIC_ANOMALY = "metric_anomaly"
    TOPOLOGY_IMPACT = "topology_impact"
    RUNBOOK_KNOWLEDGE = "runbook_knowledge"
    HISTORICAL_INCIDENT = "historical_incident"


class HypothesisStatus(str, Enum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


class InvestigationStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    HALTED = "halted"
    FAILED = "failed"



@dataclass
class EvidenceItem:
    """Individual piece of operational evidence gathered via tools."""
    id: str = field(default_factory=lambda: str(uuid4()))
    evidence_type: EvidenceType = EvidenceType.K8S_STATUS
    source_tool: str = ""
    summary: str = ""
    raw_data: Any = None
    confidence_contribution: float = 0.1
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def evidence_id(self) -> str:
        return self.id

    @property
    def description(self) -> str:
        return self.summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "evidence_type": self.evidence_type.value,
            "source_tool": self.source_tool,
            "summary": self.summary,
            "raw_data": self.raw_data,
            "confidence_contribution": round(self.confidence_contribution, 3),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceItem":
        ts = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc)
        ev_type = EvidenceType(data.get("evidence_type", EvidenceType.K8S_STATUS.value))
        return cls(
            id=data.get("id", str(uuid4())),
            evidence_type=ev_type,
            source_tool=data.get("source_tool", ""),
            summary=data.get("summary", ""),
            raw_data=data.get("raw_data"),
            confidence_contribution=data.get("confidence_contribution", 0.1),
            timestamp=ts,
        )


@dataclass
class Hypothesis:
    """Working theory of incident root cause tested against gathered evidence."""
    hypothesis_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = 0.0
    supporting_evidence_ids: list[str] = field(default_factory=list)
    refuting_evidence_ids: list[str] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "description": self.description,
            "status": self.status.value,
            "confidence": round(self.confidence, 3),
            "supporting_evidence_ids": self.supporting_evidence_ids,
            "refuting_evidence_ids": self.refuting_evidence_ids,
            "reasoning": self.reasoning,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Hypothesis":
        status_val = HypothesisStatus(data.get("status", HypothesisStatus.PROPOSED.value))
        return cls(
            hypothesis_id=data.get("hypothesis_id", str(uuid4())),
            description=data.get("description", ""),
            status=status_val,
            confidence=data.get("confidence", 0.0),
            supporting_evidence_ids=data.get("supporting_evidence_ids", []),
            refuting_evidence_ids=data.get("refuting_evidence_ids", []),
            reasoning=data.get("reasoning", ""),
        )


@dataclass
class InvestigationPlanStep:
    """A planned tool call action during investigation."""
    step_num: int
    tool_name: str
    arguments: dict[str, Any]
    rationale: str
    source: str = "heuristic_planner"  # 'llm_planner' or 'heuristic_planner'
    executed: bool = False
    skipped_reason: Optional[str] = None



@dataclass
class InvestigationState:
    """Comprehensive state tracking an autonomous investigation lifecycle."""
    investigation_id: str = field(default_factory=lambda: str(uuid4()))
    incident_id: Optional[str] = None
    target_service: Optional[str] = None
    target_pod: Optional[str] = None
    namespace: str = "default"
    initial_trigger: str = ""
    status: str = "running"  # running, completed, halted, failed
    max_steps: int = 10
    step_count: int = 0
    evidence: list[EvidenceItem] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    tool_history: list[ToolCallRecord] = field(default_factory=list)
    invoked_tool_signatures: set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    final_root_cause: Optional[str] = None
    final_recommendations: list[str] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    affected_services: list[str] = field(default_factory=list)
    propagation_path: list[str] = field(default_factory=list)
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    rag_sources: list[dict[str, Any]] = field(default_factory=list)
    epistemic_breakdown: dict[str, list[str]] = field(default_factory=lambda: {"facts": [], "inferences": [], "uncertainties": []})

    @property
    def final_rca(self) -> Optional[str]:
        return self.final_root_cause

    @final_rca.setter
    def final_rca(self, value: Optional[str]) -> None:
        self.final_root_cause = value

    def add_evidence(self, item: EvidenceItem) -> None:
        self.evidence.append(item)

    def record_tool_call(self, record: ToolCallRecord) -> None:
        self.tool_history.append(record)
        sig = f"{record.tool_name}:{sorted(record.arguments.items())}"
        self.invoked_tool_signatures.add(sig)

    def has_called(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        sig = f"{tool_name}:{sorted(arguments.items())}"
        return sig in self.invoked_tool_signatures

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "incident_id": self.incident_id,
            "target_service": self.target_service,
            "target_pod": self.target_pod,
            "namespace": self.namespace,
            "initial_trigger": self.initial_trigger,
            "status": self.status,
            "step_count": self.step_count,
            "max_steps": self.max_steps,
            "evidence_count": len(self.evidence),
            "evidence": [e.to_dict() for e in self.evidence],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "tool_history": [t.to_dict() for t in self.tool_history],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "final_root_cause": self.final_root_cause,
            "final_recommendations": self.final_recommendations,
            "citations": self.citations,
            "confidence": round(self.confidence, 3),
            "warnings": self.warnings,
            "affected_services": self.affected_services,
            "propagation_path": self.propagation_path,
            "supporting_evidence_ids": self.supporting_evidence_ids,
            "contradicting_evidence_ids": self.contradicting_evidence_ids,
            "rag_sources": self.rag_sources,
            "epistemic_breakdown": self.epistemic_breakdown,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvestigationState":
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(timezone.utc)
        completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        evidence = [EvidenceItem.from_dict(e) for e in data.get("evidence", [])]
        hypotheses = [Hypothesis.from_dict(h) for h in data.get("hypotheses", [])]
        tool_history = [ToolCallRecord.from_dict(t) for t in data.get("tool_history", [])]

        signatures = set()
        for rec in tool_history:
            sig = f"{rec.tool_name}:{sorted(rec.arguments.items())}"
            signatures.add(sig)

        return cls(
            investigation_id=data.get("investigation_id", str(uuid4())),
            incident_id=data.get("incident_id"),
            target_service=data.get("target_service"),
            target_pod=data.get("target_pod"),
            namespace=data.get("namespace", "default"),
            initial_trigger=data.get("initial_trigger", ""),
            status=data.get("status", "completed"),
            max_steps=data.get("max_steps", 10),
            step_count=data.get("step_count", len(tool_history)),
            evidence=evidence,
            hypotheses=hypotheses,
            tool_history=tool_history,
            invoked_tool_signatures=signatures,
            created_at=created_at,
            completed_at=completed_at,
            final_root_cause=data.get("final_root_cause"),
            final_recommendations=data.get("final_recommendations", []),
            citations=data.get("citations", []),
            confidence=data.get("confidence", 0.0),
            warnings=data.get("warnings", []),
            affected_services=data.get("affected_services", []),
            propagation_path=data.get("propagation_path", []),
            supporting_evidence_ids=data.get("supporting_evidence_ids", []),
            contradicting_evidence_ids=data.get("contradicting_evidence_ids", []),
            rag_sources=data.get("rag_sources", []),
            epistemic_breakdown=data.get("epistemic_breakdown", {"facts": [], "inferences": [], "uncertainties": []}),
        )
