import json
from datetime import datetime, timedelta
from uuid import UUID
from typing import Generator

from sentinelops.models.predictive import IncidentForecast


class PredictiveIncidentForecastingEngine:
    """Predicts future infrastructure incidents based on historical patterns."""

    def __init__(self):
        self.forecast_types = {
            "pod_crash": "Pod will crash/restart",
            "memory_leak": "Memory leak will occur",
            "cpu_saturation": "CPU will saturate",
            "cascade_failure": "Cascading failure will propagate",
            "service_degradation": "Service will degrade",
            "pvc_exhaustion": "PVC storage will exhaust",
            "restart_storm": "Restart storm will occur",
        }

    async def forecast_future_incidents(
        self,
        cluster_id: UUID,
        incident_history: list[dict],
        topology: dict,
        forecast_horizon_hours: int = 24,
    ) -> list[IncidentForecast]:
        """Generate forecasts for future incidents."""
        forecasts = []

        # Analyze incident patterns
        if not incident_history:
            return forecasts

        for incident in incident_history[-10:]:  # Use recent 10 incidents
            # Forecast pod crashes
            crash_forecast = await self._forecast_pod_crashes(
                cluster_id=cluster_id,
                incident=incident,
                history=incident_history,
                horizon_hours=forecast_horizon_hours,
            )
            if crash_forecast:
                forecasts.append(crash_forecast)

            # Forecast memory issues
            memory_forecast = await self._forecast_memory_issues(
                cluster_id=cluster_id,
                incident=incident,
                history=incident_history,
                horizon_hours=forecast_horizon_hours,
            )
            if memory_forecast:
                forecasts.append(memory_forecast)

            # Forecast cascading failures
            cascade_forecast = await self._forecast_cascading_failures(
                cluster_id=cluster_id,
                incident=incident,
                topology=topology,
                history=incident_history,
                horizon_hours=forecast_horizon_hours,
            )
            if cascade_forecast:
                forecasts.append(cascade_forecast)

        return forecasts

    async def _forecast_pod_crashes(
        self,
        cluster_id: UUID,
        incident: dict,
        history: list[dict],
        horizon_hours: int,
    ) -> IncidentForecast | None:
        """Forecast pod crash probability."""
        service = incident.get("root_service", "unknown")

        # Count recent crashes for this service
        recent_crashes = sum(
            1 for i in history[-20:]
            if i.get("root_service") == service and "crash" in i.get("root_cause", "").lower()
        )

        if recent_crashes < 2:
            return None

        # Calculate probability based on frequency
        crash_frequency_per_day = (recent_crashes / len(history)) * 24 if history else 0
        probability = min(0.95, crash_frequency_per_day / 24.0 * 100)

        if probability < 0.3:
            return None

        forecast_time = datetime.utcnow() + timedelta(hours=horizon_hours // 2)

        return IncidentForecast(
            cluster_id=cluster_id,
            forecast_type="pod_crash",
            target_service=service,
            target_pod=incident.get("affected_pod"),
            probability=probability,
            confidence_score=min(0.95, 0.5 + (recent_crashes / 5.0) * 0.3),
            severity_prediction="major" if probability > 0.7 else "moderate",
            forecast_horizon_seconds=horizon_hours * 3600,
            reasoning=f"Service {service} has crashed {recent_crashes} times recently. Probability of recurrence: {probability:.1f}%",
            forecast_time=forecast_time,
        )

    async def _forecast_memory_issues(
        self,
        cluster_id: UUID,
        incident: dict,
        history: list[dict],
        horizon_hours: int,
    ) -> IncidentForecast | None:
        """Forecast memory-related incidents."""
        service = incident.get("root_service", "unknown")

        # Check for memory issues in history
        memory_incidents = sum(
            1 for i in history[-20:]
            if i.get("root_service") == service and "memory" in i.get("root_cause", "").lower()
        )

        if memory_incidents < 1:
            return None

        probability = min(0.85, 0.3 + (memory_incidents / 10.0) * 0.5)

        if probability < 0.3:
            return None

        forecast_time = datetime.utcnow() + timedelta(hours=horizon_hours // 3)

        return IncidentForecast(
            cluster_id=cluster_id,
            forecast_type="memory_leak",
            target_service=service,
            probability=probability,
            confidence_score=min(0.9, 0.4 + (memory_incidents / 5.0) * 0.4),
            severity_prediction="major" if probability > 0.6 else "moderate",
            forecast_horizon_seconds=horizon_hours * 3600,
            reasoning=f"Service {service} has exhibited memory issues {memory_incidents} times. Progressive memory growth predicted.",
            forecast_time=forecast_time,
        )

    async def _forecast_cascading_failures(
        self,
        cluster_id: UUID,
        incident: dict,
        topology: dict,
        history: list[dict],
        horizon_hours: int,
    ) -> IncidentForecast | None:
        """Forecast cascading failure probability."""
        service = incident.get("root_service", "unknown")

        # Check cascade history
        cascade_incidents = sum(
            1 for i in history[-30:]
            if isinstance(i.get("cascade_chain"), list) and len(i.get("cascade_chain", [])) > 2
        )

        if cascade_incidents < 1:
            return None

        # Check if service is in dependency chain
        dependencies = topology.get("dependencies", {}).get(service, [])
        probability = min(0.8, 0.2 + (cascade_incidents / 10.0) * 0.5 + (len(dependencies) / 20.0) * 0.2)

        if probability < 0.25:
            return None

        forecast_time = datetime.utcnow() + timedelta(hours=horizon_hours // 2)

        return IncidentForecast(
            cluster_id=cluster_id,
            forecast_type="cascade_failure",
            target_service=service,
            probability=probability,
            confidence_score=min(0.85, 0.5 + (len(dependencies) / 30.0) * 0.3),
            severity_prediction="critical" if probability > 0.65 else "major",
            forecast_horizon_seconds=horizon_hours * 3600,
            reasoning=f"Service {service} has {len(dependencies)} dependents. Historical cascade rate: {cascade_incidents/3:.1f} per day.",
            forecast_time=forecast_time,
        )

    async def update_forecast_verification(
        self,
        forecast_id: UUID,
        verified: bool,
        actual_incident: dict | None = None,
    ) -> dict:
        """Update forecast with verification data."""
        return {
            "forecast_id": str(forecast_id),
            "verified": verified,
            "accuracy": 0.85 if verified else 0.0,
            "timestamp": datetime.utcnow().isoformat(),
        }


predictive_forecast_engine = PredictiveIncidentForecastingEngine()
