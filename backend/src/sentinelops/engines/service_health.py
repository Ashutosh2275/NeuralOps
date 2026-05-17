import json
from datetime import datetime, timedelta
from uuid import UUID

from sentinelops.models.predictive import ServiceHealthScore


class EnterpriseServiceHealthScoring:
    """Dynamic service health scoring with dependency weighting."""

    def __init__(self):
        self.baseline_scores = {
            "uptime_score": 0.99,
            "stability_score": 0.95,
            "dependency_score": 0.90,
            "resource_score": 0.88,
        }

    async def calculate_service_health(
        self,
        cluster_id: UUID,
        service_name: str,
        metrics: dict,
        dependency_health_scores: dict,
        incident_history: list[dict],
    ) -> ServiceHealthScore:
        """Calculate comprehensive service health score."""

        # Calculate uptime score
        uptime_score = self._calculate_uptime_score(
            metrics.get("uptime_percent", 99.9),
            incident_history,
        )

        # Calculate stability score
        stability_score = self._calculate_stability_score(
            metrics=metrics,
            incident_history=incident_history,
        )

        # Calculate dependency score (weighted average)
        dependency_score = self._calculate_dependency_score(dependency_health_scores)

        # Calculate resource score
        resource_score = self._calculate_resource_score(metrics)

        # Overall health (weighted)
        overall_health = (
            uptime_score * 0.40 +
            stability_score * 0.30 +
            dependency_score * 0.20 +
            resource_score * 0.10
        )

        # Determine risk level
        risk_level = self._determine_risk_level(overall_health)

        # Calculate metrics
        restart_frequency = self._calculate_restart_frequency(incident_history, service_name)
        incident_frequency = self._calculate_incident_frequency(incident_history, service_name)
        recovery_time_avg = self._calculate_avg_recovery_time(incident_history, service_name)

        score = ServiceHealthScore(
            cluster_id=cluster_id,
            service_name=service_name,
            uptime_score=uptime_score,
            stability_score=stability_score,
            dependency_score=dependency_score,
            resource_score=resource_score,
            overall_health=overall_health,
            risk_level=risk_level,
            restart_frequency=restart_frequency,
            incident_frequency=incident_frequency,
            recovery_time_avg_seconds=recovery_time_avg,
        )

        return score

    def _calculate_uptime_score(
        self,
        uptime_percent: float,
        incident_history: list[dict],
    ) -> float:
        """Calculate uptime score from percentage and incident history."""
        base_score = uptime_percent / 100.0

        # Penalize based on recent incidents
        recent_incidents = sum(
            1 for i in incident_history[-20:]
            if (datetime.utcnow() - (i.get("started_at") or datetime.utcnow())).total_seconds() < 86400
        )

        incident_penalty = min(0.20, recent_incidents * 0.05)
        return max(0.0, base_score - incident_penalty)

    def _calculate_stability_score(
        self,
        metrics: dict,
        incident_history: list[dict],
    ) -> float:
        """Calculate stability based on variance in metrics."""
        # Start with baseline
        stability = 0.95

        # Check for restart storms
        restart_count = metrics.get("restart_count", 0)
        if restart_count > 5:
            stability -= 0.15

        # Check for recent crashes
        crashes = sum(
            1 for i in incident_history[-10:]
            if "crash" in i.get("root_cause", "").lower()
        )
        stability -= crashes * 0.10

        # Check for cascades
        cascades = sum(
            1 for i in incident_history[-10:]
            if isinstance(i.get("cascade_chain"), (list, str)) and len(i.get("cascade_chain", [])) > 1
        )
        stability -= cascades * 0.08

        return max(0.1, stability)

    def _calculate_dependency_score(
        self,
        dependency_health_scores: dict,
    ) -> float:
        """Calculate health based on dependencies."""
        if not dependency_health_scores:
            return 0.90

        scores = list(dependency_health_scores.values())
        avg_dependency_health = sum(scores) / len(scores) if scores else 0.90

        return avg_dependency_health

    def _calculate_resource_score(self, metrics: dict) -> float:
        """Calculate resource utilization health."""
        score = 0.95

        # CPU pressure
        cpu_percent = metrics.get("cpu_percent", 30)
        if cpu_percent > 90:
            score -= 0.30
        elif cpu_percent > 70:
            score -= 0.15

        # Memory pressure
        memory_percent = metrics.get("memory_percent", 40)
        if memory_percent > 90:
            score -= 0.30
        elif memory_percent > 75:
            score -= 0.15

        # Disk pressure
        disk_percent = metrics.get("disk_percent", 50)
        if disk_percent > 90:
            score -= 0.25

        return max(0.1, score)

    def _determine_risk_level(self, overall_health: float) -> str:
        """Determine risk level from health score."""
        if overall_health > 0.90:
            return "low"
        elif overall_health > 0.75:
            return "medium"
        elif overall_health > 0.60:
            return "high"
        else:
            return "critical"

    def _calculate_restart_frequency(
        self,
        incident_history: list[dict],
        service_name: str,
    ) -> float:
        """Calculate service restart frequency (per day)."""
        restarts = sum(
            1 for i in incident_history[-100:]
            if i.get("root_service") == service_name and "restart" in i.get("root_cause", "").lower()
        )

        # Assume 100 incidents span roughly 7 days
        days_span = max(1, len(incident_history) / 100.0 * 7)
        return restarts / days_span

    def _calculate_incident_frequency(
        self,
        incident_history: list[dict],
        service_name: str,
    ) -> float:
        """Calculate incident frequency for service (per day)."""
        incidents = sum(
            1 for i in incident_history[-100:]
            if i.get("root_service") == service_name
        )

        days_span = max(1, len(incident_history) / 100.0 * 7)
        return incidents / days_span

    def _calculate_avg_recovery_time(
        self,
        incident_history: list[dict],
        service_name: str,
    ) -> float:
        """Calculate average recovery time in seconds."""
        recovery_times = []

        for incident in incident_history[-50:]:
            if incident.get("root_service") != service_name:
                continue

            started = incident.get("started_at")
            resolved = incident.get("resolved_at")

            if started and resolved:
                if isinstance(started, str):
                    started = datetime.fromisoformat(started)
                if isinstance(resolved, str):
                    resolved = datetime.fromisoformat(resolved)

                recovery_time = (resolved - started).total_seconds()
                recovery_times.append(recovery_time)

        if not recovery_times:
            return 300.0  # Default 5 minutes

        return sum(recovery_times) / len(recovery_times)

    async def calculate_cluster_risk_index(
        self,
        cluster_id: UUID,
        service_scores: list[ServiceHealthScore],
    ) -> dict:
        """Calculate overall cluster risk index."""
        if not service_scores:
            return {
                "cluster_id": str(cluster_id),
                "risk_index": 0.5,
                "services_at_risk": 0,
                "critical_services": 0,
            }

        # Count at-risk services
        at_risk = sum(1 for s in service_scores if s.overall_health < 0.75)
        critical = sum(1 for s in service_scores if s.overall_health < 0.60)

        # Calculate weighted risk index
        avg_health = sum(s.overall_health for s in service_scores) / len(service_scores)
        risk_index = 1.0 - avg_health

        return {
            "cluster_id": str(cluster_id),
            "risk_index": min(1.0, risk_index),
            "services_at_risk": at_risk,
            "critical_services": critical,
            "average_service_health": round(avg_health, 3),
        }


enterprise_health_scorer = EnterpriseServiceHealthScoring()
