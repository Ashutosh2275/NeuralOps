import json
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Generator

from sentinelops.models.predictive import IncidentAncestry, InfrastructureTimeline


class InfrastructureTimelineIntelligence:
    """Tracks infrastructure event lineage and incident evolution."""

    def __init__(self):
        self.event_graph = {}

    async def build_incident_ancestry(
        self,
        current_incident: dict,
        incident_history: list[dict],
        timeline_events: list[dict],
    ) -> IncidentAncestry | None:
        """Build ancestry chain for an incident."""
        current_service = current_incident.get("root_service")
        if not current_service:
            return None

        # Find root incident (first in cascade chain)
        root_incident = self._find_root_incident(
            current_service=current_service,
            history=incident_history,
            current_time=current_incident.get("started_at", datetime.utcnow()),
            current_incident=current_incident,
        )

        if not root_incident:
            return None

        # Trace evolution chain
        evolution_chain = self._trace_evolution_chain(
            root_incident=root_incident,
            current_incident=current_incident,
            history=incident_history,
        )

        # Calculate amplification
        amplification = self._calculate_amplification(evolution_chain)

        inc_id = current_incident.get("id") or current_incident.get("incident_id") or uuid4()
        if isinstance(inc_id, str):
            inc_id = UUID(inc_id)

        root_id = root_incident.get("id") or root_incident.get("incident_id") or uuid4()
        if isinstance(root_id, str):
            root_id = UUID(root_id)

        return IncidentAncestry(
            incident_id=inc_id,
            root_incident_id=root_id,
            ancestry_depth=len(evolution_chain),
            amplification_factor=amplification,
            evolution_chain_json=json.dumps(evolution_chain, default=str),
        )

    def _find_root_incident(
        self,
        current_service: str,
        history: list[dict],
        current_time: datetime,
        current_incident: dict | None = None,
    ) -> dict | None:
        """Find the root cause incident."""
        lookback_window = timedelta(hours=6)

        # 1. First check if current incident explicitly points to root incident ID(s) in its cascade_chain
        if current_incident:
            cur_cascade = current_incident.get("cascade_chain", [])
            if isinstance(cur_cascade, str):
                try:
                    cur_cascade = json.loads(cur_cascade)
                except Exception:
                    cur_cascade = []
            if isinstance(cur_cascade, list):
                for item in cur_cascade:
                    target_id = str(item.get("id") if isinstance(item, dict) else item)
                    for inc in history:
                        if str(inc.get("id") or inc.get("incident_id")) == target_id:
                            return inc

        # 2. Look for prior incidents whose cascade chain reached current_service
        for incident in reversed(history):
            incident_time = incident.get("started_at")
            if isinstance(incident_time, str):
                incident_time = datetime.fromisoformat(incident_time)

            # Check if within window
            if current_time - incident_time > lookback_window:
                continue

            # Check if this could be root
            cascade_chain = incident.get("cascade_chain", [])
            if isinstance(cascade_chain, str):
                cascade_chain = json.loads(cascade_chain) if cascade_chain else []

            if current_service in [c.get("service") if isinstance(c, dict) else c for c in cascade_chain]:
                # Found potential root
                return incident

        # 3. Fallback: Return oldest prior incident in history window if available
        prior_incidents = [
            inc for inc in history
            if str(inc.get("id")) != str((current_incident or {}).get("id"))
        ]
        if prior_incidents:
            return prior_incidents[0]

        return None

    def _trace_evolution_chain(
        self,
        root_incident: dict,
        current_incident: dict,
        history: list[dict],
    ) -> list[dict]:
        """Trace how incident evolved from root to current."""
        chain = [
            {
                "service": root_incident.get("root_service"),
                "severity": root_incident.get("severity"),
                "timestamp": root_incident.get("started_at"),
                "event": "root_cause",
            }
        ]

        # Find intermediate incidents
        cascade = current_incident.get("cascade_chain", [])
        if isinstance(cascade, str):
            cascade = json.loads(cascade) if cascade else []

        for idx, service_info in enumerate(cascade):
            service_name = service_info.get("service") if isinstance(service_info, dict) else service_info
            chain.append({
                "service": service_name,
                "severity": current_incident.get("severity"),
                "depth": idx + 1,
                "event": "cascaded_to",
            })

        chain.append({
            "service": current_incident.get("root_service"),
            "severity": current_incident.get("severity"),
            "timestamp": current_incident.get("started_at"),
            "event": "current_incident",
        })

        return chain

    def _calculate_amplification(self, evolution_chain: list[dict]) -> float:
        """Calculate how much the incident amplified through the chain."""
        if not evolution_chain:
            return 1.0

        # Base amplification on cascade depth and severity progression
        cascade_depth = len(evolution_chain)
        return min(3.0, 1.0 + (cascade_depth / 10.0) * 2.0)

    async def track_timeline_event(
        self,
        cluster_id: UUID,
        event_type: str,
        source_entity: str,
        affected_entities: list[str],
        parent_event_id: UUID | None = None,
    ) -> InfrastructureTimeline:
        """Track an infrastructure event in the timeline."""
        event_id = uuid4()

        # Calculate causality score based on event type
        causality_score = self._calculate_causality_score(event_type)

        # Calculate lineage depth
        lineage_depth = 1
        if parent_event_id:
            lineage_depth += 1  # Would query parent in real system

        event = InfrastructureTimeline(
            cluster_id=cluster_id,
            event_id=event_id,
            parent_event_id=parent_event_id,
            event_type=event_type,
            source_entity=source_entity,
            affected_entities=json.dumps(affected_entities),
            causality_score=causality_score,
            lineage_depth=lineage_depth,
            metadata_json=json.dumps({
                "affected_count": len(affected_entities),
                "event_chain_depth": lineage_depth,
            }),
            timestamp=datetime.utcnow(),
        )

        return event

    def _calculate_causality_score(self, event_type: str) -> float:
        """Score how likely this event is to cause downstream issues."""
        causality_map = {
            "service_crash": 0.95,
            "memory_leak": 0.85,
            "cpu_spike": 0.75,
            "network_latency": 0.70,
            "pod_restart": 0.60,
            "dependency_failure": 0.90,
            "cascade_start": 0.98,
            "resource_exhaustion": 0.88,
        }
        return causality_map.get(event_type, 0.5)

    async def analyze_event_lineage(
        self,
        start_event_id: UUID,
        all_events: list[dict],
    ) -> dict:
        """Analyze the lineage of events leading to an incident."""
        lineage = {
            "root_event": None,
            "propagation_chain": [],
            "total_affected": 0,
            "affected_service_count": 0,
            "propagation_depth": 0,
        }

        # Find root event
        current_event_id = start_event_id
        visited = set()

        while current_event_id and str(current_event_id) not in visited:
            visited.add(str(current_event_id))

            # Find event in list
            event = next(
                (
                    e for e in all_events
                    if str(e.get("event_id") or e.get("id")) == str(current_event_id)
                ),
                None,
            )

            if not event:
                break

            lineage["propagation_chain"].insert(0, event)
            lineage["root_event"] = event

            # Move to parent
            current_event_id = event.get("parent_event_id")

        lineage["propagation_depth"] = len(lineage["propagation_chain"])

        total_affected = 0
        for e in lineage["propagation_chain"]:
            aff = e.get("affected_entities", [])
            if isinstance(aff, str):
                try:
                    aff = json.loads(aff)
                except Exception:
                    aff = []
            if isinstance(aff, list):
                total_affected += len(aff)

        lineage["total_affected"] = total_affected
        lineage["affected_service_count"] = total_affected

        return lineage


timeline_intelligence = InfrastructureTimelineIntelligence()
