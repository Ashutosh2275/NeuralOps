import json
from typing import Generator
from uuid import UUID

from sentinelops.models.simulation import BlastRadiusEvent


class BlastRadiusIntelligence:
    """Calculate and track blast radius of incidents."""

    def __init__(self):
        self.service_dependency_graph = {}

    def set_dependency_graph(self, graph: dict):
        """Set the service dependency graph for traversal."""
        self.service_dependency_graph = graph

    async def calculate_blast_radius(
        self,
        origin_pod: str,
        origin_namespace: str,
        affected_services: list[str],
        simulation_id: UUID,
    ) -> BlastRadiusEvent:
        """Calculate blast radius for an incident."""

        propagation_depth = self._calculate_propagation_depth(
            origin_pod, affected_services
        )
        degradation_intensity = self._calculate_degradation_intensity(
            len(affected_services), propagation_depth
        )
        recovery_path = self._calculate_recovery_path(affected_services)

        event = BlastRadiusEvent(
            simulation_id=simulation_id,
            origin_pod=origin_pod,
            origin_namespace=origin_namespace,
            affected_services=json.dumps(affected_services),
            propagation_depth=propagation_depth,
            degradation_intensity=degradation_intensity,
            recovery_path_json=json.dumps(recovery_path),
        )

        return event

    async def propagate_degradation(
        self,
        origin_service: str,
        initial_severity: float,
    ) -> Generator[dict, None, None]:
        """Simulate degradation propagation through dependency tree."""

        visited = set()
        queue = [(origin_service, initial_severity, 0)]

        while queue:
            service, severity, depth = queue.pop(0)

            if service in visited or depth > 5:
                continue

            visited.add(service)

            yield {
                "service": service,
                "severity": severity,
                "depth": depth,
                "path": self._get_propagation_path(origin_service, service),
            }

            # Get dependent services
            if service in self.service_dependency_graph:
                for dependent in self.service_dependency_graph[service].get("dependents", []):
                    new_severity = severity * 0.8
                    queue.append((dependent, new_severity, depth + 1))

    def _calculate_propagation_depth(self, origin: str, affected_services: list[str]) -> int:
        """Calculate maximum propagation depth in dependency tree."""
        if not affected_services:
            return 0

        max_depth = 0
        for service in affected_services:
            depth = self._find_depth_in_graph(origin, service)
            max_depth = max(max_depth, depth)

        return max_depth

    def _calculate_degradation_intensity(self, service_count: int, propagation_depth: int) -> float:
        """Calculate average degradation intensity."""
        # More services = higher intensity
        service_factor = min(service_count / 10.0, 1.0)

        # Deeper propagation = higher intensity
        depth_factor = min(propagation_depth / 5.0, 1.0)

        intensity = (service_factor * 0.6) + (depth_factor * 0.4)
        return min(1.0, intensity)

    def _calculate_recovery_path(self, affected_services: list[str]) -> list[dict]:
        """Calculate optimal recovery path for affected services."""
        if not affected_services:
            return []

        # Sort by dependency order (most dependent first = recover last)
        recovery_order = []

        for service in affected_services:
            dependents = self._count_dependents(service)
            recovery_order.append({"service": service, "dependents": dependents})

        recovery_order.sort(key=lambda x: x["dependents"], reverse=True)

        return [
            {
                "step": idx + 1,
                "service": item["service"],
                "priority": "high" if item["dependents"] > 2 else "medium",
                "estimated_recovery_time_seconds": 30 + (idx * 10),
            }
            for idx, item in enumerate(recovery_order)
        ]

    def _find_depth_in_graph(self, origin: str, target: str, visited: set | None = None) -> int:
        """Find depth of target service from origin using BFS."""
        if visited is None:
            visited = set()

        if origin == target:
            return 0

        if origin in visited:
            return float("inf")

        visited.add(origin)

        if origin not in self.service_dependency_graph:
            return float("inf")

        min_depth = float("inf")
        for dependent in self.service_dependency_graph[origin].get("dependents", []):
            depth = self._find_depth_in_graph(dependent, target, visited.copy())
            min_depth = min(min_depth, 1 + depth)

        return min_depth

    def _get_propagation_path(self, origin: str, target: str) -> list[str]:
        """Find propagation path from origin to target."""
        if origin == target:
            return [origin]

        queue = [(origin, [origin])]

        while queue:
            service, path = queue.pop(0)

            if service not in self.service_dependency_graph:
                continue

            for dependent in self.service_dependency_graph[service].get("dependents", []):
                new_path = path + [dependent]

                if dependent == target:
                    return new_path

                queue.append((dependent, new_path))

        return []

    def _count_dependents(self, service: str, visited: set | None = None) -> int:
        """Count total dependents of a service recursively."""
        if visited is None:
            visited = set()

        if service in visited:
            return 0

        visited.add(service)

        if service not in self.service_dependency_graph:
            return 0

        count = len(self.service_dependency_graph[service].get("dependents", []))

        for dependent in self.service_dependency_graph[service].get("dependents", []):
            count += self._count_dependents(dependent, visited)

        return count

    async def estimate_impact(
        self,
        affected_services: list[str],
        severity: float,
    ) -> dict:
        """Estimate business impact of affected services."""

        critical_services = ["api-gateway", "auth-service", "payment-service"]
        critical_count = sum(1 for s in affected_services if s in critical_services)

        business_impact_score = (len(affected_services) / 10.0) * 0.7 + (critical_count / 3.0) * 0.3
        business_impact_score = min(1.0, business_impact_score)

        user_impact_percent = (affected_services.__len__() * 5) + (critical_count * 20)
        user_impact_percent = min(100, user_impact_percent)

        estimated_recovery_minutes = 5 + (len(affected_services) * 2) + (critical_count * 5)

        return {
            "affected_service_count": len(affected_services),
            "critical_services_affected": critical_count,
            "business_impact_score": round(business_impact_score, 2),
            "estimated_user_impact_percent": user_impact_percent,
            "estimated_recovery_minutes": estimated_recovery_minutes,
            "severity": severity,
        }


blast_radius_engine = BlastRadiusIntelligence()
