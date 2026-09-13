"""
Autonomous Investigation and Governance API endpoints for SentinelOps AI.
Provides REST interfaces for investigation lifecycles, tool execution,
human approval governance, audit queries, and data retention management.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from sentinelops.investigation.engine import get_investigation_engine
from sentinelops.security.auth import (
    Role,
    User,
    get_current_user,
    require_admin,
    require_operator,
    require_viewer,
)
from sentinelops.security.approval import (
    ApprovalStatus,
    RiskLevel,
    get_approval_manager,
)
from sentinelops.security.audit import get_audit_trail
from sentinelops.security.redactor import get_secret_redactor
from sentinelops.security.retention import get_retention_manager
from sentinelops.tools.registry import get_tool_registry

router = APIRouter()


class TriggerInvestigationRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="Optional associated incident ID")
    service_name: Optional[str] = Field(None, description="Target service name (e.g. payment-service)")
    pod_name: Optional[str] = Field(None, description="Target pod name")
    namespace: str = Field("default", description="Kubernetes namespace")
    trigger_reason: str = Field("Manual diagnostic trigger", description="Operational symptom or trigger message")
    max_steps: int = Field(8, ge=1, le=20, description="Max tool execution steps")


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool invocation parameters")


class ProposeActionRequest(BaseModel):
    name: str = Field(..., description="Short title of proposed remediation")
    action_type: str = Field(..., description="Action category (e.g. restart_pod, rollback_deployment)")
    risk_level: RiskLevel = Field(RiskLevel.MEDIUM, description="Risk level classification")
    affected_resources: list[str] = Field(default_factory=list, description="Target k8s resources")
    justification: str = Field(..., description="Root cause reasoning justifying this action")
    evidence_ids: list[str] = Field(default_factory=list, description="Associated evidence IDs")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class RejectActionRequest(BaseModel):
    reason: str = Field(..., description="Justification for rejecting the remediation action")


# ============================================================================
# Investigation Endpoints
# ============================================================================


@router.post("", summary="Trigger an autonomous incident investigation")
@router.post("/start", summary="Trigger an autonomous incident investigation (alias)")
async def trigger_investigation(
    req: TriggerInvestigationRequest,
    current_user: User = Depends(require_operator),
) -> dict[str, Any]:
    engine = get_investigation_engine()
    state = await engine.investigate(
        incident_id=req.incident_id,
        target_service=req.service_name,
        target_pod=req.pod_name,
        namespace=req.namespace,
        trigger_reason=req.trigger_reason,
        max_steps=req.max_steps,
    )
    raw_dict = state.to_dict()
    redacted = get_secret_redactor().redact_data(raw_dict)
    return {
        "status": "success",
        "investigation": redacted,
    }


@router.get("", summary="List recent autonomous investigations")
async def list_investigations(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_viewer),
) -> dict[str, Any]:
    engine = get_investigation_engine()
    investigations = engine.list_investigations(limit=limit)
    redacted = get_secret_redactor().redact_data([inv.to_dict() for inv in investigations])
    return {
        "count": len(investigations),
        "investigations": redacted,
    }


@router.get("/tools", summary="List available read-only investigation tools")
@router.get("/tools/list", summary="List available read-only investigation tools (alias)")
async def list_tools(current_user: User = Depends(require_viewer)) -> dict[str, Any]:
    registry = get_tool_registry()
    return {
        "count": len(registry.list_tools()),
        "tools": registry.list_tools(),
    }


@router.post("/tools/execute", summary="Directly execute an authorized read-only tool")
async def execute_tool(
    req: ToolExecuteRequest,
    current_user: User = Depends(require_operator),
) -> dict[str, Any]:
    registry = get_tool_registry()
    record = await registry.execute(req.tool_name, req.arguments)
    redacted_record = get_secret_redactor().redact_data(record.to_dict())
    return {
        "call_record": redacted_record,
    }


@router.post("/tools/{tool_name}/execute", summary="Directly execute an authorized read-only tool by path")
async def execute_tool_by_path(
    tool_name: str,
    arguments: dict[str, Any],
    current_user: User = Depends(require_operator),
) -> dict[str, Any]:
    registry = get_tool_registry()
    record = await registry.execute(tool_name, arguments)
    redacted_record = get_secret_redactor().redact_data(record.to_dict())
    return {
        "call_record": redacted_record,
    }


@router.get("/{investigation_id}", summary="Retrieve full investigation details and audit trail")
async def get_investigation(
    investigation_id: str,
    current_user: User = Depends(require_viewer),
) -> dict[str, Any]:
    engine = get_investigation_engine()
    inv = engine.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation '{investigation_id}' not found")
    redacted = get_secret_redactor().redact_data(inv.to_dict())
    return {
        "investigation": redacted,
    }


# ============================================================================
# Human Approval Governance Endpoints (Phase 4: Non-Destructive)
# ============================================================================


@router.post("/approvals/propose", summary="Propose a human-governed remediation action")
async def propose_remediation_action(
    req: ProposeActionRequest,
    current_user: User = Depends(require_operator),
) -> dict[str, Any]:
    approval_mgr = get_approval_manager()
    action = approval_mgr.propose_action(
        name=req.name,
        action_type=req.action_type,
        risk_level=req.risk_level,
        requested_by=current_user.username,
        affected_resources=req.affected_resources,
        justification=req.justification,
        evidence_ids=req.evidence_ids,
        parameters=req.parameters,
    )
    return {"status": "success", "action": action.to_dict()}


@router.get("/approvals", summary="List proposed or reviewed remediation actions")
async def list_remediation_actions(
    status_filter: Optional[ApprovalStatus] = Query(None, alias="status"),
    current_user: User = Depends(require_viewer),
) -> dict[str, Any]:
    approval_mgr = get_approval_manager()
    actions = approval_mgr.list_actions(status=status_filter)
    return {"count": len(actions), "actions": [a.to_dict() for a in actions]}


@router.post("/approvals/{action_id}/submit", summary="Submit proposed action for human review")
async def submit_action_for_review(
    action_id: str,
    current_user: User = Depends(require_operator),
) -> dict[str, Any]:
    approval_mgr = get_approval_manager()
    try:
        action = approval_mgr.submit_for_approval(action_id)
        return {"status": "success", "action": action.to_dict()}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/{action_id}/approve", summary="Human review: Approve proposed action")
async def approve_remediation_action(
    action_id: str,
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    approval_mgr = get_approval_manager()
    try:
        action = approval_mgr.approve_action(action_id, approved_by=current_user.username)
        return {"status": "approved", "action": action.to_dict()}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/{action_id}/reject", summary="Human review: Reject proposed action")
async def reject_remediation_action(
    action_id: str,
    req: RejectActionRequest,
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    approval_mgr = get_approval_manager()
    try:
        action = approval_mgr.reject_action(action_id, rejected_by=current_user.username, reason=req.reason)
        return {"status": "rejected", "action": action.to_dict()}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/{action_id}/execute", summary="Execute approved action (Blocked in Phase 4)")
async def execute_remediation_action(
    action_id: str,
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    """
    STRICT NON-DESTRUCTIVE PHASE 4 ENFORCEMENT:
    Autonomous or manual write execution is strictly forbidden and rejected.
    """
    approval_mgr = get_approval_manager()
    try:
        approval_mgr.execute_action(action_id, actor=current_user.username)
        return {"status": "executed"}
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Audit Trail & Data Retention Endpoints
# ============================================================================


@router.get("/audit/events", summary="Query persistent structured audit trail")
async def get_audit_events(
    investigation_id: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_viewer),
) -> dict[str, Any]:
    audit = get_audit_trail()
    events = audit.query(investigation_id=investigation_id, actor=actor, execution_status=status_filter, limit=limit)
    return {"count": len(events), "events": [e.to_dict() for e in events]}


@router.post("/retention/cleanup", summary="Execute data retention cleanup policy")
async def run_retention_cleanup(
    dry_run: bool = Query(True),
    current_user: User = Depends(require_admin),
) -> dict[str, Any]:
    mgr = get_retention_manager()
    inv_report = mgr.cleanup_investigations(dry_run=dry_run)
    audit_report = mgr.cleanup_audit_trail(dry_run=dry_run)
    return {
        "dry_run": dry_run,
        "investigations": {
            "scanned": inv_report.scanned_count,
            "expired": inv_report.expired_count,
            "deleted": inv_report.deleted_count,
            "details": inv_report.details,
        },
        "audit_trail": {
            "scanned": audit_report.scanned_count,
            "expired": audit_report.expired_count,
            "deleted": audit_report.deleted_count,
            "details": audit_report.details,
        },
    }
