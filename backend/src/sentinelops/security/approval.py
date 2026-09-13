"""
Human Approval Governance Architecture for SentinelOps AI.
Strict non-destructive governance: allows proposing and reviewing remediation actions,
but explicitly forbids autonomous execution in Phase 4.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sentinelops.core.logging import get_logger

log = get_logger(__name__)



class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApprovalStatus(str, Enum):
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ExecutionStatus(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    EXECUTION_BLOCKED_IN_PHASE_4 = "EXECUTION_BLOCKED_IN_PHASE_4"


@dataclass
class ProposedAction:
    action_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    action_type: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM
    requested_by: str = ""
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    affected_resources: list[str] = field(default_factory=list)
    justification: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    approval_status: ApprovalStatus = ApprovalStatus.PROPOSED
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    execution_status: ExecutionStatus = ExecutionStatus.NOT_EXECUTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "name": self.name,
            "action_type": self.action_type,
            "risk_level": self.risk_level.value,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
            "affected_resources": self.affected_resources,
            "justification": self.justification,
            "evidence_ids": self.evidence_ids,
            "parameters": self.parameters,
            "approval_status": self.approval_status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "execution_status": self.execution_status.value,
        }


class ApprovalManager:
    """Manages lifecycle of proposed operational actions with strict governance gates."""

    def __init__(self, default_ttl_hours: int = 24) -> None:
        self._actions: dict[str, ProposedAction] = {}
        self._default_ttl = timedelta(hours=default_ttl_hours)

    def propose_action(
        self,
        name: str,
        action_type: str,
        risk_level: RiskLevel,
        requested_by: str,
        affected_resources: list[str],
        justification: str,
        evidence_ids: Optional[list[str]] = None,
        parameters: Optional[dict[str, Any]] = None,
        expires_in_hours: Optional[int] = None,
    ) -> ProposedAction:
        """Create a new proposed action in PROPOSED status."""
        ttl = timedelta(hours=expires_in_hours) if expires_in_hours else self._default_ttl
        now = datetime.now(timezone.utc)
        action = ProposedAction(
            name=name,
            action_type=action_type,
            risk_level=risk_level,
            requested_by=requested_by,
            requested_at=now,
            affected_resources=affected_resources,
            justification=justification,
            evidence_ids=evidence_ids or [],
            parameters=parameters or {},
            approval_status=ApprovalStatus.PROPOSED,
            expires_at=now + ttl,
        )
        self._actions[action.action_id] = action
        log.info(
            "remediation_action_proposed",
            action_id=action.action_id,
            name=name,
            risk=risk_level.value,
            requested_by=requested_by,
        )
        return action

    def submit_for_approval(self, action_id: str) -> ProposedAction:
        """Transition PROPOSED -> PENDING_APPROVAL."""
        action = self._get_valid_action(action_id)
        if action.approval_status != ApprovalStatus.PROPOSED:
            raise ValueError(f"Cannot submit action in state '{action.approval_status.value}' for approval")
        action.approval_status = ApprovalStatus.PENDING_APPROVAL
        return action

    def approve_action(self, action_id: str, approved_by: str) -> ProposedAction:
        """Transition PENDING_APPROVAL -> APPROVED. Requires human operator/admin."""
        action = self._get_valid_action(action_id)
        if action.approval_status != ApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot approve action in state '{action.approval_status.value}' (must be PENDING_APPROVAL)")

        action.approval_status = ApprovalStatus.APPROVED
        action.approved_by = approved_by
        action.approved_at = datetime.now(timezone.utc)
        log.info("remediation_action_approved", action_id=action.action_id, approved_by=approved_by)
        return action

    def reject_action(self, action_id: str, rejected_by: str, reason: str) -> ProposedAction:
        """Transition PENDING_APPROVAL -> REJECTED."""
        action = self._get_valid_action(action_id)
        if action.approval_status not in (ApprovalStatus.PROPOSED, ApprovalStatus.PENDING_APPROVAL):
            raise ValueError(f"Cannot reject action in state '{action.approval_status.value}'")

        action.approval_status = ApprovalStatus.REJECTED
        action.approved_by = rejected_by
        action.rejection_reason = reason
        action.approved_at = datetime.now(timezone.utc)
        log.info("remediation_action_rejected", action_id=action.action_id, rejected_by=rejected_by, reason=reason)
        return action

    def cancel_action(self, action_id: str, user: str) -> ProposedAction:
        """Cancel an action before execution."""
        action = self._get_valid_action(action_id)
        if action.approval_status in (ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED, ApprovalStatus.CANCELLED):
            raise ValueError(f"Action already finalized in state '{action.approval_status.value}'")

        action.approval_status = ApprovalStatus.CANCELLED
        log.info("remediation_action_cancelled", action_id=action.action_id, user=user)
        return action

    def execute_action(self, action_id: str, actor: str) -> None:
        """
        STRICT NON-DESTRUCTIVE PHASE 4 INVARIANT:
        Autonomous execution is disabled and blocked by design.
        """
        action = self._get_valid_action(action_id)
        action.execution_status = ExecutionStatus.EXECUTION_BLOCKED_IN_PHASE_4
        log.warning(
            "remediation_execution_blocked_phase_4",
            action_id=action.action_id,
            actor=actor,
        )
        raise PermissionError(
            "Autonomous remediation execution is strictly BLOCKED in Phase 4. "
            "SentinelOps AI is configured in read-only investigation and governance mode."
        )

    def _get_valid_action(self, action_id: str) -> ProposedAction:
        action = self._actions.get(action_id)
        if not action:
            raise KeyError(f"Proposed action '{action_id}' not found")
        # Check expiration
        now = datetime.now(timezone.utc)
        if action.expires_at and now > action.expires_at and action.approval_status in (ApprovalStatus.PROPOSED, ApprovalStatus.PENDING_APPROVAL):
            action.approval_status = ApprovalStatus.EXPIRED
        return action

    def get_action(self, action_id: str) -> Optional[ProposedAction]:
        return self._actions.get(action_id)

    def list_actions(self, status: Optional[ApprovalStatus] = None) -> list[ProposedAction]:
        now = datetime.now(timezone.utc)
        # Update expired
        for act in self._actions.values():
            if act.expires_at and now > act.expires_at and act.approval_status in (ApprovalStatus.PROPOSED, ApprovalStatus.PENDING_APPROVAL):
                act.approval_status = ApprovalStatus.EXPIRED

        if status:
            return [act for act in self._actions.values() if act.approval_status == status]
        return list(self._actions.values())


# Global approval manager singleton
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
