"""Predictive Failure Engine - Forecasts infrastructure failures 24h in advance"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FailurePrediction:
    """Represents a predicted failure"""

    def __init__(
        self,
        incident_type: str,
        probability: float,
        confidence: float,
        time_to_failure_hours: int,
        severity_forecast: str,
        affected_services: list[str],
        reasoning: str,
    ):
        self.incident_type = incident_type
        self.probability = probability
        self.confidence = confidence
        self.time_to_failure_hours = time_to_failure_hours
        self.severity_forecast = severity_forecast
        self.affected_services = affected_services
        self.reasoning = reasoning


class PredictiveFailureEngine:
    """Forecasts infrastructure failures based on historical patterns"""

    # Incident types we predict
    PREDICTABLE_TYPES = [
        "pod_crash",
        "memory_leak",
        "cascading_failure",
        "restart_storm",
        "pvc_exhaustion",
        "service_saturation",
        "high_latency",
    ]

    async def forecast_failures(
        self,
        cluster_id: UUID,
        incident_history: list[dict],
        topology: dict,
        session: Optional[AsyncSession] = None,
    ) -> list[FailurePrediction]:
        """Forecast failures for next 24 hours"""
        predictions = []

        for incident_type in self.PREDICTABLE_TYPES:
            prediction = await self._predict_incident_type(
                incident_type=incident_type,
                cluster_id=cluster_id,
                incident_history=incident_history,
                topology=topology,
            )

            if prediction and prediction.probability > 0.1:  # Only include likely predictions
                predictions.append(prediction)

        return sorted(predictions, key=lambda p: p.probability, reverse=True)

    async def _predict_incident_type(
        self,
        incident_type: str,
        cluster_id: UUID,
        incident_history: list[dict],
        topology: dict,
    ) -> Optional[FailurePrediction]:
        """Predict specific incident type"""

        # Filter recent similar incidents
        similar_incidents = [
            i
            for i in incident_history[-100:]
            if i.get("incident_type") == incident_type or i.get("error_type") == incident_type
        ]

        if not similar_incidents:
            return None

        # Analyze incident frequency
        now = datetime.utcnow()
        cutoff_7d = now - timedelta(days=7)
        cutoff_30d = now - timedelta(days=30)

        recent_7d = sum(
            1
            for i in similar_incidents
            if self._parse_datetime(i.get("started_at")) > cutoff_7d
        )
        recent_30d = sum(
            1
            for i in similar_incidents
            if self._parse_datetime(i.get("started_at")) > cutoff_30d
        )

        # Calculate inter-incident times (hours)
        sorted_incidents = sorted(
            similar_incidents,
            key=lambda x: self._parse_datetime(x.get("started_at", datetime.utcnow())),
        )

        inter_incident_times = []
        for i in range(1, len(sorted_incidents)):
            prev_time = self._parse_datetime(sorted_incidents[i - 1].get("started_at"))
            curr_time = self._parse_datetime(sorted_incidents[i].get("started_at"))
            delta_hours = (curr_time - prev_time).total_seconds() / 3600
            inter_incident_times.append(delta_hours)

        if not inter_incident_times:
            return None

        # Forecast time-to-failure
        avg_interval_hours = sum(inter_incident_times) / len(inter_incident_times)
        time_to_failure = max(1, min(24, int(avg_interval_hours)))

        # Calculate probability
        # Higher recent frequency = higher probability
        base_probability = min(0.95, recent_7d * 0.15 + recent_30d * 0.05)

        # Adjust by cascade depth if applicable
        cascade_factor = 1.0
        if incident_type in ["cascading_failure", "restart_storm"]:
            cascade_paths = self._count_cascade_paths(topology)
            cascade_factor = min(1.5, 1.0 + cascade_paths * 0.1)

        probability = base_probability * cascade_factor

        # Severity forecast
        severity_scores = [self._parse_severity(i.get("severity")) for i in similar_incidents[-10:]]
        avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 0.5
        severity_forecast = self._score_to_severity(avg_severity)

        # Confidence based on data recency and pattern strength
        data_recency_score = 1.0 if recent_7d > 0 else 0.5
        pattern_strength = len(similar_incidents) / 100  # Normalized to 100 incidents
        confidence = min(0.99, data_recency_score * pattern_strength * 0.9 + 0.1)

        # Get affected services
        affected_services = list(set(
            i.get("root_service") for i in similar_incidents[-5:] if i.get("root_service")
        ))

        # Generate reasoning
        reasoning = self._generate_reasoning(
            incident_type=incident_type,
            probability=probability,
            recent_7d=recent_7d,
            avg_interval_hours=avg_interval_hours,
            severity_forecast=severity_forecast,
        )

        return FailurePrediction(
            incident_type=incident_type,
            probability=probability,
            confidence=confidence,
            time_to_failure_hours=time_to_failure,
            severity_forecast=severity_forecast,
            affected_services=affected_services,
            reasoning=reasoning,
        )

    def _parse_datetime(self, value) -> datetime:
        """Parse datetime from various formats"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return datetime.utcnow()
        return datetime.utcnow()

    def _parse_severity(self, severity: str) -> float:
        """Convert severity string to score 0-1"""
        severity_map = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2, "info": 0.1}
        return severity_map.get(severity.lower() if severity else "medium", 0.5)

    def _score_to_severity(self, score: float) -> str:
        """Convert score back to severity level"""
        if score > 0.8:
            return "critical"
        if score > 0.6:
            return "high"
        if score > 0.4:
            return "medium"
        return "low"

    def _count_cascade_paths(self, topology: dict) -> int:
        """Count potential cascade paths in topology"""
        dependencies = topology.get("dependencies", {})
        return sum(len(v) for v in dependencies.values())

    def _generate_reasoning(
        self,
        incident_type: str,
        probability: float,
        recent_7d: int,
        avg_interval_hours: float,
        severity_forecast: str,
    ) -> str:
        """Generate human-readable reasoning"""
        return (
            f"Predicted {incident_type} based on {recent_7d} similar incidents in past 7 days. "
            f"Average interval between incidents is {avg_interval_hours:.1f} hours. "
            f"Expected severity: {severity_forecast}. "
            f"Confidence: {probability:.1%}"
        )


# Singleton instance
predictive_failure_engine = PredictiveFailureEngine()
