"""
Durable, Structured Audit Trail Engine for SentinelOps AI.
Records security events, tool invocations, and investigation lifecycles with
strict secret redaction, structured schema, and persistent disk logging.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from sentinelops.security.redactor import get_secret_redactor

log = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    investigation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str = "system"
    role: str = "system"
    action: str = ""
    request_path: str = ""
    selected_tools: list[str] = field(default_factory=list)
    sanitized_arguments: dict[str, Any] = field(default_factory=dict)
    execution_status: str = "success"  # success, failed, denied
    duration_ms: float = 0.0
    evidence_sources: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    final_rca: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "investigation_id": self.investigation_id,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "role": self.role,
            "action": self.action,
            "request_path": self.request_path,
            "selected_tools": self.selected_tools,
            "sanitized_arguments": self.sanitized_arguments,
            "execution_status": self.execution_status,
            "duration_ms": round(self.duration_ms, 2),
            "evidence_sources": self.evidence_sources,
            "citations": self.citations,
            "confidence": round(self.confidence, 4),
            "final_rca": self.final_rca,
            "warnings": self.warnings,
            "errors": self.errors,
        }


class AuditTrail:
    """Manages append-oriented audit records with centralized redaction and file persistence."""

    def __init__(self, storage_path: str = "data/audit/audit_trail.jsonl", max_in_memory: int = 5000) -> None:
        self.storage_path = Path(storage_path)
        self.max_in_memory = max_in_memory
        self._events: list[AuditEvent] = []
        self._redactor = get_secret_redactor()
        self._ensure_storage_dir()
        self._load_from_disk()

    def _ensure_storage_dir(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.warning(f"Could not create audit storage directory: {e}")

    def _load_from_disk(self) -> None:
        """Load persisted audit records from disk on startup."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        ts = datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat()))
                        event = AuditEvent(
                            event_id=data.get("event_id", str(uuid4())),
                            investigation_id=data.get("investigation_id"),
                            timestamp=ts,
                            actor=data.get("actor", "system"),
                            role=data.get("role", "system"),
                            action=data.get("action", ""),
                            request_path=data.get("request_path", ""),
                            selected_tools=data.get("selected_tools", []),
                            sanitized_arguments=data.get("sanitized_arguments", {}),
                            execution_status=data.get("execution_status", "success"),
                            duration_ms=data.get("duration_ms", 0.0),
                            evidence_sources=data.get("evidence_sources", []),
                            citations=data.get("citations", []),
                            confidence=data.get("confidence", 0.0),
                            final_rca=data.get("final_rca"),
                            warnings=data.get("warnings", []),
                            errors=data.get("errors", []),
                        )
                        self._events.append(event)
                    except Exception as err:
                        log.debug(f"Skipping malformed audit log entry: {err}")
            if len(self._events) > self.max_in_memory:
                self._events = self._events[-self.max_in_memory :]
        except Exception as e:
            log.warning(f"Failed to read audit log file: {e}")

    def log_event(
        self,
        action: str,
        actor: str = "system",
        role: str = "system",
        investigation_id: Optional[str] = None,
        request_path: str = "",
        selected_tools: Optional[list[str]] = None,
        arguments: Optional[dict[str, Any]] = None,
        execution_status: str = "success",
        duration_ms: float = 0.0,
        evidence_sources: Optional[list[str]] = None,
        citations: Optional[list[str]] = None,
        confidence: float = 0.0,
        final_rca: Optional[str] = None,
        warnings: Optional[list[str]] = None,
        errors: Optional[list[str]] = None,
    ) -> AuditEvent:
        """Create, sanitize, record, and persist an audit event."""
        # Redact secrets from all user inputs and final outputs
        sanitized_args = self._redactor.redact_data(arguments or {})
        sanitized_rca = self._redactor.redact_text(final_rca) if final_rca else None
        sanitized_errors = [self._redactor.redact_text(e) for e in (errors or [])]
        sanitized_warnings = [self._redactor.redact_text(w) for w in (warnings or [])]

        event = AuditEvent(
            investigation_id=investigation_id,
            actor=actor,
            role=role,
            action=action,
            request_path=request_path,
            selected_tools=selected_tools or [],
            sanitized_arguments=sanitized_args,
            execution_status=execution_status,
            duration_ms=duration_ms,
            evidence_sources=evidence_sources or [],
            citations=citations or [],
            confidence=confidence,
            final_rca=sanitized_rca,
            warnings=sanitized_warnings,
            errors=sanitized_errors,
        )

        self._events.append(event)
        if len(self._events) > self.max_in_memory:
            self._events = self._events[-self.max_in_memory :]

        self._persist_event(event)
        return event

    def _persist_event(self, event: AuditEvent) -> None:
        """Append event JSON line to audit file."""
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            log.error(f"Failed to persist audit event: {e}")

    def query(
        self,
        investigation_id: Optional[str] = None,
        actor: Optional[str] = None,
        execution_status: Optional[str] = None,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Query in-memory and historical audit events."""
        results = self._events
        if investigation_id:
            results = [e for e in results if e.investigation_id == investigation_id]
        if actor:
            results = [e for e in results if e.actor == actor]
        if execution_status:
            results = [e for e in results if e.execution_status == execution_status]
        return results[-limit:]


# Global singleton
_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail
