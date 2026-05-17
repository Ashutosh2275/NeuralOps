import json
from datetime import datetime, timedelta
from uuid import UUID

from sentinelops.models.predictive import ExecutiveMetrics


class ExecutiveAnalyticsDashboard:
    """Calculates executive-level infrastructure KPIs and analytics."""

    async def calculate_executive_metrics(
        self,
        cluster_id: UUID,
        incident_history: list[dict],
        service_health_scores: list,
        forecasts: list,
        time_period_days: int = 7,
    ) -> ExecutiveMetrics:
        """Calculate comprehensive executive metrics."""

        # Calculate MTTR (Mean Time To Recovery)
        mttr = self._calculate_mttr(incident_history, time_period_days)

        # Calculate MTTD (Mean Time To Detection)
        mttd = self._calculate_mttd(incident_history, time_period_days)

        # Calculate incident frequency
        incident_frequency = self._calculate_incident_frequency(incident_history, time_period_days)

        # Calculate uptime
        uptime_percent = self._calculate_uptime(incident_history, time_period_days)

        # Calculate SLA compliance
        sla_compliance = self._calculate_sla_compliance(uptime_percent)

        # Predict metrics for next 24 hours
        predicted_uptime_24h = self._predict_uptime_24h(forecasts, service_health_scores)
        predicted_incidents_24h = self._predict_incidents_24h(forecasts)

        # Calculate reliability score
        reliability_score = self._calculate_reliability_score(
            uptime_percent,
            mttr,
            incident_frequency,
        )

        # Calculate operational efficiency
        efficiency_score = self._calculate_operational_efficiency(
            service_health_scores,
            mttr,
        )

        return ExecutiveMetrics(
            cluster_id=cluster_id,
            mttr_seconds=mttr,
            mttd_seconds=mttd,
            incident_frequency_per_day=incident_frequency,
            uptime_percent=uptime_percent,
            sla_compliance_percent=sla_compliance,
            predicted_uptime_24h=predicted_uptime_24h,
            predicted_incidents_24h=predicted_incidents_24h,
            reliability_score=reliability_score,
            operational_efficiency_score=efficiency_score,
        )

    def _calculate_mttr(
        self,
        incident_history: list[dict],
        time_period_days: int,
    ) -> float:
        """Calculate mean time to recovery."""
        if not incident_history:
            return 300.0  # Default 5 minutes

        resolved_incidents = [
            i for i in incident_history[-100:]
            if i.get("resolved_at") and i.get("started_at")
        ]

        if not resolved_incidents:
            return 300.0

        recovery_times = []
        for incident in resolved_incidents:
            started = incident.get("started_at")
            resolved = incident.get("resolved_at")

            if isinstance(started, str):
                started = datetime.fromisoformat(started)
            if isinstance(resolved, str):
                resolved = datetime.fromisoformat(resolved)

            recovery_time = (resolved - started).total_seconds()
            recovery_times.append(recovery_time)

        return sum(recovery_times) / len(recovery_times) if recovery_times else 300.0

    def _calculate_mttd(
        self,
        incident_history: list[dict],
        time_period_days: int,
    ) -> float:
        """Calculate mean time to detection."""
        # Estimate as 20% of MTTR (detection is faster than recovery)
        mttr = self._calculate_mttr(incident_history, time_period_days)
        return mttr * 0.2

    def _calculate_incident_frequency(
        self,
        incident_history: list[dict],
        time_period_days: int,
    ) -> float:
        """Calculate incidents per day."""
        cutoff_time = datetime.utcnow() - timedelta(days=time_period_days)

        recent_incidents = sum(
            1 for i in incident_history
            if isinstance(i.get("started_at"), (str, datetime)) and
            (datetime.fromisoformat(i.get("started_at")) if isinstance(i.get("started_at"), str) else i.get("started_at")) > cutoff_time
        )

        return recent_incidents / max(1, time_period_days)

    def _calculate_uptime(
        self,
        incident_history: list[dict],
        time_period_days: int,
    ) -> float:
        """Calculate cluster uptime percentage."""
        if not incident_history:
            return 99.9

        total_seconds = time_period_days * 86400
        downtime_seconds = 0

        for incident in incident_history[-100:]:
            started = incident.get("started_at")
            resolved = incident.get("resolved_at")

            if started and resolved:
                if isinstance(started, str):
                    started = datetime.fromisoformat(started)
                if isinstance(resolved, str):
                    resolved = datetime.fromisoformat(resolved)

                downtime_seconds += (resolved - started).total_seconds()

        uptime = max(0.0, 100.0 * (total_seconds - downtime_seconds) / total_seconds)
        return min(100.0, uptime)

    def _calculate_sla_compliance(self, uptime_percent: float) -> float:
        """Calculate SLA compliance."""
        # Standard SLA: 99.9% uptime
        if uptime_percent >= 99.9:
            return 100.0
        elif uptime_percent >= 99.5:
            return 95.0
        elif uptime_percent >= 99.0:
            return 85.0
        else:
            return max(0.0, uptime_percent * 0.8)

    def _predict_uptime_24h(
        self,
        forecasts: list,
        service_health_scores: list,
    ) -> float:
        """Predict uptime for next 24 hours."""
        if not forecasts and not service_health_scores:
            return 99.5

        # Calculate risk from forecasts
        forecast_risk = 0.0
        if forecasts:
            critical_forecasts = sum(1 for f in forecasts if f.get("severity_prediction") == "critical")
            forecast_risk = min(0.1, critical_forecasts * 0.02)

        # Calculate risk from health scores
        health_risk = 0.0
        if service_health_scores:
            avg_health = sum(s.overall_health for s in service_health_scores) / len(service_health_scores)
            health_risk = (1.0 - avg_health) * 0.1

        # Predicted uptime
        predicted = 100.0 - (forecast_risk * 100) - (health_risk * 100)
        return max(95.0, predicted)

    def _predict_incidents_24h(self, forecasts: list) -> int:
        """Predict number of incidents in next 24 hours."""
        if not forecasts:
            return 0

        # Count forecasts with high probability
        high_prob_forecasts = sum(
            1 for f in forecasts
            if f.get("probability", 0) > 0.6
        )

        return high_prob_forecasts

    def _calculate_reliability_score(
        self,
        uptime_percent: float,
        mttr_seconds: float,
        incident_frequency: float,
    ) -> float:
        """Calculate overall reliability score (0-1)."""
        # Uptime contribution: 50%
        uptime_score = uptime_percent / 100.0 * 0.5

        # MTTR contribution: 30% (lower is better)
        mttr_score = max(0.0, 1.0 - (mttr_seconds / 3600.0)) * 0.3

        # Incident frequency contribution: 20%
        incident_score = max(0.0, 1.0 - (incident_frequency / 5.0)) * 0.2

        return min(1.0, uptime_score + mttr_score + incident_score)

    def _calculate_operational_efficiency(
        self,
        service_health_scores: list,
        mttr_seconds: float,
    ) -> float:
        """Calculate operational efficiency score (0-1)."""
        # Service health: 60%
        if service_health_scores:
            avg_health = sum(s.overall_health for s in service_health_scores) / len(service_health_scores)
            health_efficiency = avg_health * 0.6
        else:
            health_efficiency = 0.5

        # Recovery speed: 40%
        recovery_efficiency = max(0.0, 1.0 - (mttr_seconds / 3600.0)) * 0.4

        return min(1.0, health_efficiency + recovery_efficiency)

    async def generate_analytics_report(
        self,
        metrics: ExecutiveMetrics,
    ) -> dict:
        """Generate executive analytics report."""
        return {
            "cluster_id": str(metrics.cluster_id),
            "report_generated_at": datetime.utcnow().isoformat(),
            "key_metrics": {
                "mttr_minutes": round(metrics.mttr_seconds / 60, 2),
                "mttd_minutes": round(metrics.mttd_seconds / 60, 2),
                "incidents_per_day": round(metrics.incident_frequency_per_day, 2),
                "uptime_percent": round(metrics.uptime_percent, 2),
                "sla_compliance_percent": round(metrics.sla_compliance_percent, 2),
            },
            "predictions_24h": {
                "predicted_uptime_percent": round(metrics.predicted_uptime_24h, 2),
                "predicted_incidents": metrics.predicted_incidents_24h,
            },
            "scores": {
                "reliability": round(metrics.reliability_score, 3),
                "operational_efficiency": round(metrics.operational_efficiency_score, 3),
            },
        }


executive_analytics = ExecutiveAnalyticsDashboard()
