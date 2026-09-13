"""
Data Retention and Privacy Management for SentinelOps AI.
Enforces configurable time-to-live (TTL) policies on historical investigations,
audit logs, and diagnostic snapshots with safety guards against accidental data loss.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


@dataclass
class RetentionPolicy:
    investigation_retention_days: int = 30
    audit_retention_days: int = 90
    max_investigation_records: int = 10_000
    max_audit_records: int = 50_000


@dataclass
class CleanupReport:
    category: str
    scanned_count: int
    expired_count: int
    deleted_count: int
    dry_run: bool
    details: list[str]


class RetentionManager:
    """Automates and enforces data retention policies across file and memory storage."""

    def __init__(
        self,
        policy: Optional[RetentionPolicy] = None,
        investigations_dir: str = "data/investigations",
        audit_file: str = "data/audit/audit_trail.jsonl",
    ) -> None:
        self.policy = policy or RetentionPolicy()
        self.investigations_dir = Path(investigations_dir)
        self.audit_file = Path(audit_file)

    def cleanup_investigations(self, dry_run: bool = False) -> CleanupReport:
        """
        Delete completed investigations older than policy.investigation_retention_days.
        SAFETY GUARD: In-progress investigations (status != 'completed') are never deleted.
        """
        if not self.investigations_dir.exists():
            return CleanupReport("investigations", 0, 0, 0, dry_run, ["Directory does not exist"])

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.policy.investigation_retention_days)
        scanned = 0
        expired = 0
        deleted = 0
        details = []

        for json_file in self.investigations_dir.glob("*.json"):
            scanned += 1
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Check safety guard: status must be completed
                status = data.get("status", "")
                if status != "completed":
                    continue

                started_str = data.get("started_at")
                if not started_str:
                    continue

                # Parse ISO timestamp
                started_at = datetime.fromisoformat(started_str)
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)

                if started_at < cutoff:
                    expired += 1
                    if not dry_run:
                        json_file.unlink()
                        deleted += 1
                        details.append(f"Deleted expired investigation: {json_file.name}")
                    else:
                        details.append(f"Dry-run would delete: {json_file.name}")

            except Exception as e:
                log.warning(f"Error checking retention for {json_file.name}: {e}")

        return CleanupReport(
            category="investigations",
            scanned_count=scanned,
            expired_count=expired,
            deleted_count=deleted,
            dry_run=dry_run,
            details=details,
        )

    def cleanup_audit_trail(self, dry_run: bool = False) -> CleanupReport:
        """
        Prune audit log entries older than policy.audit_retention_days.
        """
        if not self.audit_file.exists():
            return CleanupReport("audit", 0, 0, 0, dry_run, ["Audit file does not exist"])

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.policy.audit_retention_days)
        scanned = 0
        expired = 0
        kept_lines: list[str] = []
        details = []

        try:
            with open(self.audit_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                scanned += 1
                try:
                    data = json.loads(line.strip())
                    ts_str = data.get("timestamp")
                    if ts_str:
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        if ts < cutoff:
                            expired += 1
                            continue
                except Exception:
                    pass
                kept_lines.append(line)

            deleted = expired if not dry_run else 0
            if not dry_run and expired > 0:
                with open(self.audit_file, "w", encoding="utf-8") as f:
                    f.writelines(kept_lines)
                details.append(f"Pruned {expired} audit log records older than {cutoff.isoformat()}")

        except Exception as e:
            log.warning(f"Error pruning audit trail: {e}")

        return CleanupReport(
            category="audit",
            scanned_count=scanned,
            expired_count=expired,
            deleted_count=deleted,
            dry_run=dry_run,
            details=details,
        )


# Global singleton
_retention_manager: RetentionManager | None = None


def get_retention_manager() -> RetentionManager:
    global _retention_manager
    if _retention_manager is None:
        _retention_manager = RetentionManager()
    return _retention_manager
