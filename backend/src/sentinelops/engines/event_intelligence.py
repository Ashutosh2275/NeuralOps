import json
from datetime import datetime, timedelta
from uuid import UUID, uuid4


class EventIntelligenceEngine:
    """Deduplicates and clusters infrastructure events."""

    def __init__(self):
        self.event_similarity_threshold = 0.85

    async def deduplicate_events(
        self,
        events: list[dict],
        time_window_seconds: int = 300,
    ) -> list[dict]:
        """Deduplicate similar events within time window."""
        if not events:
            return events

        deduplicated = []
        processed = set()

        for idx, event in enumerate(events):
            if idx in processed:
                continue

            event_group = [event]

            # Find similar events within time window
            event_time = event.get("timestamp")
            if isinstance(event_time, str):
                event_time = datetime.fromisoformat(event_time)

            for other_idx in range(idx + 1, len(events)):
                if other_idx in processed:
                    continue

                other = events[other_idx]
                other_time = other.get("timestamp")

                if isinstance(other_time, str):
                    other_time = datetime.fromisoformat(other_time)

                # Check if within window
                if (other_time - event_time).total_seconds() > time_window_seconds:
                    continue

                # Check similarity
                similarity = self._calculate_event_similarity(event, other)
                if similarity > self.event_similarity_threshold:
                    event_group.append(other)
                    processed.add(other_idx)

            # Create deduplicated event
            if len(event_group) > 1:
                deduplicated_event = {
                    "type": event.get("type"),
                    "source": event.get("source"),
                    "affected_entities": self._merge_affected_entities(event_group),
                    "occurrence_count": len(event_group),
                    "first_occurrence": event.get("timestamp"),
                    "last_occurrence": event_group[-1].get("timestamp"),
                    "is_deduplicated": True,
                }
                deduplicated.append(deduplicated_event)
            else:
                deduplicated.append(event)

            processed.add(idx)

        return deduplicated

    async def cluster_anomalies(
        self,
        anomalies: list[dict],
    ) -> list[dict]:
        """Cluster related anomalies into incident groups."""
        if not anomalies:
            return []

        clusters = []
        processed = set()

        for idx, anomaly in enumerate(anomalies):
            if idx in processed:
                continue

            cluster = {
                "id": str(uuid4()),
                "anomalies": [anomaly],
                "cluster_type": self._determine_cluster_type([anomaly]),
                "severity": anomaly.get("severity", "unknown"),
            }

            # Find related anomalies
            for other_idx in range(idx + 1, len(anomalies)):
                if other_idx in processed:
                    continue

                other = anomalies[other_idx]
                relatedness = self._calculate_anomaly_relatedness(anomaly, other)

                if relatedness > 0.75:
                    cluster["anomalies"].append(other)
                    processed.add(other_idx)

            cluster["anomaly_count"] = len(cluster["anomalies"])
            cluster["total_severity"] = self._calculate_cluster_severity(cluster["anomalies"])

            clusters.append(cluster)
            processed.add(idx)

        return clusters

    async def compress_incidents(
        self,
        incidents: list[dict],
        time_window_hours: int = 6,
    ) -> list[dict]:
        """Compress related incidents into meta-incidents."""
        if not incidents:
            return []

        compressed = []
        processed = set()

        for idx, incident in enumerate(incidents):
            if idx in processed:
                continue

            incident_group = [incident]
            incident_time = incident.get("started_at")

            if isinstance(incident_time, str):
                incident_time = datetime.fromisoformat(incident_time)

            # Find related incidents
            for other_idx in range(idx + 1, len(incidents)):
                if other_idx in processed:
                    continue

                other = incidents[other_idx]
                other_time = other.get("started_at")

                if isinstance(other_time, str):
                    other_time = datetime.fromisoformat(other_time)

                # Check if within window
                if (other_time - incident_time).total_seconds() > time_window_hours * 3600:
                    continue

                # Check if related (same service or cascade)
                root_service = incident.get("root_service")
                other_root = other.get("root_service")

                if root_service == other_root:
                    incident_group.append(other)
                    processed.add(other_idx)

            # Create compressed incident
            if len(incident_group) > 1:
                compressed_incident = {
                    "meta_incident_id": str(uuid4()),
                    "original_incidents": [i.get("id") for i in incident_group],
                    "incident_count": len(incident_group),
                    "root_service": incident.get("root_service"),
                    "severity": incident.get("severity"),
                    "first_started": incident.get("started_at"),
                    "last_started": incident_group[-1].get("started_at"),
                    "pattern": self._identify_incident_pattern(incident_group),
                    "is_compressed": True,
                }
                compressed.append(compressed_incident)
            else:
                compressed.append(incident)

            processed.add(idx)

        return compressed

    def _calculate_event_similarity(self, event1: dict, event2: dict) -> float:
        """Calculate similarity between two events (0-1)."""
        similarity = 0.0

        # Same event type: 0.3
        if event1.get("type") == event2.get("type"):
            similarity += 0.3

        # Same source: 0.3
        if event1.get("source") == event2.get("source"):
            similarity += 0.3

        # Same affected entity: 0.4
        entities1 = set(event1.get("affected_entities", []))
        entities2 = set(event2.get("affected_entities", []))
        if entities1 & entities2:
            similarity += 0.4

        return min(1.0, similarity)

    def _merge_affected_entities(self, events: list[dict]) -> list[str]:
        """Merge affected entities from multiple events."""
        merged = set()
        for event in events:
            entities = event.get("affected_entities", [])
            if isinstance(entities, list):
                merged.update(entities)

        return list(merged)

    def _calculate_anomaly_relatedness(self, anomaly1: dict, anomaly2: dict) -> float:
        """Calculate relatedness between two anomalies (0-1)."""
        relatedness = 0.0

        # Same metric type: 0.4
        if anomaly1.get("metric_type") == anomaly2.get("metric_type"):
            relatedness += 0.4

        # Same service: 0.6
        if anomaly1.get("service") == anomaly2.get("service"):
            relatedness += 0.6

        return min(1.0, relatedness)

    def _determine_cluster_type(self, anomalies: list[dict]) -> str:
        """Determine the type of cluster."""
        if not anomalies:
            return "unknown"

        metric_types = set(a.get("metric_type") for a in anomalies)

        if len(metric_types) == 1:
            return f"{list(metric_types)[0]}_spike"
        else:
            return "multi_metric"

    def _calculate_cluster_severity(self, anomalies: list[dict]) -> str:
        """Calculate overall severity of a cluster."""
        if not anomalies:
            return "unknown"

        severities = [a.get("severity", "low") for a in anomalies]
        severity_score = {
            "critical": 3,
            "high": 2,
            "medium": 1,
            "low": 0,
        }

        avg_score = sum(severity_score.get(s, 0) for s in severities) / len(severities)

        if avg_score > 2.5:
            return "critical"
        elif avg_score > 1.5:
            return "high"
        elif avg_score > 0.5:
            return "medium"
        else:
            return "low"

    def _identify_incident_pattern(self, incidents: list[dict]) -> str:
        """Identify pattern in related incidents."""
        if not incidents:
            return "unknown"

        # Check if recurring pattern
        service = incidents[0].get("root_service")

        # Get timestamps
        timestamps = []
        for incident in incidents:
            ts = incident.get("started_at")
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            timestamps.append(ts)

        timestamps.sort()

        # Calculate intervals
        if len(timestamps) > 2:
            intervals = [
                (timestamps[i + 1] - timestamps[i]).total_seconds()
                for i in range(len(timestamps) - 1)
            ]

            avg_interval = sum(intervals) / len(intervals)
            variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)

            # If low variance, it's recurring
            if variance < avg_interval * 0.1:
                return "recurring"

        return "sporadic"


event_intelligence = EventIntelligenceEngine()
