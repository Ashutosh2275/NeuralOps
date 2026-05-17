"""Infrastructure Memory Engine - Tracks incident lineage, topology evolution, patterns"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class MemoryRecord:
    """Represents a memory record about infrastructure"""

    def __init__(
        self,
        memory_type: str,
        key: str,
        value: dict[str, Any],
        source_incident_id: Optional[UUID] = None,
        confidence: float = 0.9,
    ):
        self.memory_type = memory_type
        self.key = key
        self.value = value
        self.source_incident_id = source_incident_id
        self.confidence = confidence
        self.created_at = datetime.utcnow()


class InfrastructureMemoryEngine:
    """Maintains infrastructure memory for historical reasoning"""

    # Memory types
    MEMORY_TYPES = {
        "incident_ancestry": "Historical incident chains and root causes",
        "topology_evolution": "Service topology changes over time",
        "dependency_patterns": "Common dependency failure patterns",
        "service_history": "Per-service launch dates and configurations",
        "cascade_patterns": "Recurring cascade propagation patterns",
        "seasonal_patterns": "Time-based incident patterns (day of week, hour, etc.)",
    }

    def __init__(self):
        self._memory: dict[str, list[MemoryRecord]] = {mtype: [] for mtype in self.MEMORY_TYPES}

    async def store_incident_ancestry(
        self,
        incident_id: UUID,
        root_cause_chain: list[str],
        affected_services: dict[str, str],
        timeline: list[dict],
        recovery_path: list[dict],
        blast_radius_evolution: list[dict],
    ) -> MemoryRecord:
        """Store incident ancestry for future reasoning"""

        value = {
            "incident_id": str(incident_id),
            "root_cause_chain": root_cause_chain,
            "affected_services": affected_services,
            "timeline": timeline,
            "recovery_path": recovery_path,
            "blast_radius_evolution": blast_radius_evolution,
            "stored_at": datetime.utcnow().isoformat(),
        }

        record = MemoryRecord(
            memory_type="incident_ancestry",
            key=f"incident:{incident_id}",
            value=value,
            source_incident_id=incident_id,
            confidence=0.95,
        )

        self._memory["incident_ancestry"].append(record)
        logger.info(f"Stored ancestry for incident {incident_id}")
        return record

    async def store_topology_snapshot(
        self,
        cluster_id: UUID,
        topology: dict,
        timestamp: Optional[datetime] = None,
    ) -> MemoryRecord:
        """Store topology snapshot for evolution tracking"""

        if not timestamp:
            timestamp = datetime.utcnow()

        value = {
            "cluster_id": str(cluster_id),
            "topology": topology,
            "snapshot_time": timestamp.isoformat(),
        }

        record = MemoryRecord(
            memory_type="topology_evolution",
            key=f"topology:{cluster_id}:{timestamp.isoformat()}",
            value=value,
            confidence=1.0,
        )

        self._memory["topology_evolution"].append(record)
        return record

    async def track_dependency_change(
        self,
        cluster_id: UUID,
        source_service: str,
        target_service: str,
        change_type: str,  # "added" or "removed"
        timestamp: Optional[datetime] = None,
    ) -> MemoryRecord:
        """Track changes to service dependencies"""

        if not timestamp:
            timestamp = datetime.utcnow()

        value = {
            "cluster_id": str(cluster_id),
            "source_service": source_service,
            "target_service": target_service,
            "change_type": change_type,
            "timestamp": timestamp.isoformat(),
        }

        record = MemoryRecord(
            memory_type="topology_evolution",
            key=f"dependency:{cluster_id}:{source_service}:{target_service}:{timestamp.isoformat()}",
            value=value,
            confidence=1.0,
        )

        self._memory["topology_evolution"].append(record)
        return record

    async def store_cascade_pattern(
        self,
        cluster_id: UUID,
        source_service: str,
        cascade_path: list[str],
        frequency: int,
        affected_service_count: int,
    ) -> MemoryRecord:
        """Store recurring cascade patterns"""

        value = {
            "cluster_id": str(cluster_id),
            "source_service": source_service,
            "cascade_path": cascade_path,
            "frequency": frequency,
            "affected_service_count": affected_service_count,
            "last_observed": datetime.utcnow().isoformat(),
        }

        record = MemoryRecord(
            memory_type="cascade_patterns",
            key=f"cascade:{cluster_id}:{source_service}",
            value=value,
            confidence=min(1.0, frequency * 0.1),
        )

        self._memory["cascade_patterns"].append(record)
        return record

    async def get_incident_ancestry(self, incident_id: UUID) -> Optional[dict]:
        """Retrieve incident ancestry from memory"""
        for record in self._memory.get("incident_ancestry", []):
            if str(incident_id) in record.value.get("incident_id", ""):
                return record.value
        return None

    async def get_service_history(self, cluster_id: UUID, service_name: str) -> Optional[dict]:
        """Get historical information about a service"""
        for record in self._memory.get("service_history", []):
            if cluster_id in record.value.values() and service_name in record.value.values():
                return record.value
        return None

    async def get_cascade_patterns(
        self, cluster_id: UUID, source_service: str
    ) -> list[dict]:
        """Get known cascade patterns from specific source"""
        patterns = []
        for record in self._memory.get("cascade_patterns", []):
            if (
                str(cluster_id) == record.value.get("cluster_id")
                and source_service == record.value.get("source_service")
            ):
                patterns.append(record.value)
        return sorted(patterns, key=lambda p: p.get("frequency", 0), reverse=True)

    async def get_seasonal_patterns(
        self, cluster_id: UUID
    ) -> dict[str, list[dict]]:
        """Get time-based incident patterns"""
        patterns = {}
        for record in self._memory.get("seasonal_patterns", []):
            if str(cluster_id) == record.value.get("cluster_id"):
                day_of_week = record.value.get("day_of_week")
                if day_of_week not in patterns:
                    patterns[day_of_week] = []
                patterns[day_of_week].append(record.value)
        return patterns

    async def get_topology_timeline(
        self, cluster_id: UUID, hours: int = 24
    ) -> list[dict]:
        """Get topology evolution over time"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        timeline = []

        for record in self._memory.get("topology_evolution", []):
            if str(cluster_id) == record.value.get("cluster_id"):
                snapshot_time = datetime.fromisoformat(record.value.get("snapshot_time", ""))
                if snapshot_time > cutoff:
                    timeline.append(record.value)

        return sorted(timeline, key=lambda t: t.get("snapshot_time", ""))

    def get_memory_stats(self) -> dict[str, int]:
        """Get statistics about stored memory"""
        return {
            mtype: len(records)
            for mtype, records in self._memory.items()
        }

    async def prune_old_memory(self, days: int = 30) -> int:
        """Remove memory older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        total_pruned = 0

        for mtype in self._memory:
            original_count = len(self._memory[mtype])
            self._memory[mtype] = [
                r for r in self._memory[mtype]
                if r.created_at > cutoff
            ]
            pruned = original_count - len(self._memory[mtype])
            total_pruned += pruned
            logger.info(f"Pruned {pruned} old {mtype} records")

        return total_pruned


# Singleton instance
infrastructure_memory_engine = InfrastructureMemoryEngine()
