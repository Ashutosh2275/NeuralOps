import json
from datetime import datetime, timedelta
from uuid import UUID

from sentinelops.models.simulation import InfrastructureScore


class InfrastructureHealthEngine:
    """Calculate infrastructure-wide health scores."""

    def __init__(self):
        self.baseline_scores = {
            "cluster_health": 0.95,
            "namespace_health": 0.90,
            "service_health": 0.92,
            "dependency_health": 0.88,
            "incident_risk_score": 0.1,
            "recovery_readiness_score": 0.85,
            "ai_confidence_score": 0.92,
            "operational_stability_score": 0.90,
            "cascading_failure_probability": 0.05,
        }

    async def calculate_health_score(
        self,
        cluster_id: UUID,
        active_incidents: int = 0,
        active_remediations: int = 0,
        services: dict | None = None,
        namespaces: dict | None = None,
    ) -> InfrastructureScore:
        """Calculate comprehensive infrastructure health score."""

        services = services or {}
        namespaces = namespaces or {}

        # Base calculation
        cluster_health = self._calculate_cluster_health(active_incidents, active_remediations)
        namespace_health = self._calculate_namespace_health(namespaces)
        service_health = self._calculate_service_health(services)
        dependency_health = self._calculate_dependency_health(services)

        # Risk and recovery calculations
        incident_risk_score = self._calculate_incident_risk_score(active_incidents, cluster_health)
        recovery_readiness_score = self._calculate_recovery_readiness_score(
            active_remediations, cluster_health
        )
        ai_confidence_score = self._calculate_ai_confidence_score(cluster_health)
        operational_stability_score = self._calculate_operational_stability_score(
            cluster_health, service_health, dependency_health
        )
        cascading_failure_probability = self._calculate_cascading_failure_probability(
            cluster_health, dependency_health
        )

        # Overall health (weighted average)
        overall_health = (
            cluster_health * 0.30
            + namespace_health * 0.20
            + service_health * 0.25
            + dependency_health * 0.25
        )

        score = InfrastructureScore(
            cluster_id=cluster_id,
            cluster_health=cluster_health,
            namespace_health=namespace_health,
            service_health=service_health,
            dependency_health=dependency_health,
            incident_risk_score=incident_risk_score,
            recovery_readiness_score=recovery_readiness_score,
            ai_confidence_score=ai_confidence_score,
            operational_stability_score=operational_stability_score,
            cascading_failure_probability=cascading_failure_probability,
            overall_health=overall_health,
            namespace_scores_json=json.dumps(
                {ns: self._calculate_namespace_health({ns: v}) for ns, v in namespaces.items()}
            ),
            service_scores_json=json.dumps(
                {svc: self._calculate_service_health({svc: v}) for svc, v in services.items()}
            ),
        )

        return score

    def _calculate_cluster_health(self, active_incidents: int, active_remediations: int) -> float:
        """Calculate cluster health based on incidents and remediations."""
        health = self.baseline_scores["cluster_health"]

        # Incidents reduce health
        health -= active_incidents * 0.15
        # Remediations improve trajectory
        health += active_remediations * 0.05

        return max(0.0, min(1.0, health))

    def _calculate_namespace_health(self, namespaces: dict) -> float:
        """Calculate average namespace health."""
        if not namespaces:
            return self.baseline_scores["namespace_health"]

        health_scores = []
        for ns_name, ns_data in namespaces.items():
            pod_health = ns_data.get("pod_health", 0.9)
            service_count = ns_data.get("service_count", 1)
            healthy_services = ns_data.get("healthy_services", service_count)

            health = (pod_health * 0.6) + ((healthy_services / service_count) * 0.4) if service_count > 0 else pod_health
            health_scores.append(health)

        avg_health = sum(health_scores) / len(health_scores) if health_scores else self.baseline_scores["namespace_health"]
        return max(0.0, min(1.0, avg_health))

    def _calculate_service_health(self, services: dict) -> float:
        """Calculate average service health."""
        if not services:
            return self.baseline_scores["service_health"]

        health_scores = []
        for svc_name, svc_data in services.items():
            uptime = svc_data.get("uptime_percent", 99.9)
            response_time = svc_data.get("response_time_ms", 50)
            error_rate = svc_data.get("error_rate_percent", 0.1)

            # Uptime contribution (0-1)
            uptime_score = uptime / 100.0

            # Response time contribution (inverse, normalized to 5s baseline)
            response_time_score = max(0.0, 1.0 - (response_time / 5000.0))

            # Error rate contribution (inverse)
            error_rate_score = max(0.0, 1.0 - (error_rate / 100.0))

            health = (uptime_score * 0.5) + (response_time_score * 0.3) + (error_rate_score * 0.2)
            health_scores.append(health)

        avg_health = sum(health_scores) / len(health_scores) if health_scores else self.baseline_scores["service_health"]
        return max(0.0, min(1.0, avg_health))

    def _calculate_dependency_health(self, services: dict) -> float:
        """Calculate dependency chain health."""
        if not services:
            return self.baseline_scores["dependency_health"]

        # Count dependency failures
        total_dependencies = 0
        healthy_dependencies = 0

        for svc_name, svc_data in services.items():
            dependencies = svc_data.get("dependencies", [])
            if dependencies:
                total_dependencies += len(dependencies)
                # Assume 90% of dependencies are healthy
                healthy_dependencies += int(len(dependencies) * 0.9)

        if total_dependencies == 0:
            return self.baseline_scores["dependency_health"]

        health = healthy_dependencies / total_dependencies
        return max(0.0, min(1.0, health))

    def _calculate_incident_risk_score(self, active_incidents: int, cluster_health: float) -> float:
        """Calculate risk of future incidents."""
        # Base risk increases with degraded health
        base_risk = 1.0 - cluster_health

        # Active incidents increase risk
        incident_contribution = min(active_incidents * 0.1, 0.4)

        return min(1.0, base_risk + incident_contribution)

    def _calculate_recovery_readiness_score(self, active_remediations: int, cluster_health: float) -> float:
        """Calculate readiness to recover from incidents."""
        # Active remediations indicate readiness
        remediation_boost = min(active_remediations * 0.05, 0.3)

        # Better health = better recovery readiness
        base_readiness = cluster_health * 0.7 + 0.15

        return min(1.0, base_readiness + remediation_boost)

    def _calculate_ai_confidence_score(self, cluster_health: float) -> float:
        """Calculate AI model confidence in predictions."""
        # Higher health = more stable patterns = higher confidence
        confidence = 0.5 + (cluster_health * 0.5)
        return min(1.0, confidence)

    def _calculate_operational_stability_score(
        self, cluster_health: float, service_health: float, dependency_health: float
    ) -> float:
        """Calculate overall operational stability."""
        stability = (cluster_health * 0.4) + (service_health * 0.35) + (dependency_health * 0.25)
        return max(0.0, min(1.0, stability))

    def _calculate_cascading_failure_probability(self, cluster_health: float, dependency_health: float) -> float:
        """Calculate probability of cascading failures."""
        # Lower health = higher cascade risk
        cluster_risk = 1.0 - cluster_health

        # Weaker dependencies = higher cascade risk
        dependency_risk = 1.0 - dependency_health

        cascade_probability = (cluster_risk * 0.4) + (dependency_risk * 0.6)
        return min(1.0, cascade_probability)

    async def get_health_trend(
        self,
        cluster_id: UUID,
        scores: list[InfrastructureScore],
        hours: int = 24,
    ) -> dict:
        """Calculate health trend over time."""
        if not scores:
            return {"trend": "stable", "direction": "neutral", "change_percent": 0.0}

        recent_scores = [s for s in scores if (datetime.utcnow() - s.calculated_at).total_seconds() < hours * 3600]

        if len(recent_scores) < 2:
            return {"trend": "stable", "direction": "neutral", "change_percent": 0.0}

        first_score = recent_scores[0]
        last_score = recent_scores[-1]

        change = last_score.overall_health - first_score.overall_health
        change_percent = (change / first_score.overall_health) * 100 if first_score.overall_health > 0 else 0

        if change_percent > 5:
            trend = "improving"
            direction = "up"
        elif change_percent < -5:
            trend = "degrading"
            direction = "down"
        else:
            trend = "stable"
            direction = "neutral"

        return {
            "trend": trend,
            "direction": direction,
            "change_percent": round(change_percent, 2),
            "recent_score": last_score.overall_health,
            "baseline_score": first_score.overall_health,
        }


health_engine = InfrastructureHealthEngine()
