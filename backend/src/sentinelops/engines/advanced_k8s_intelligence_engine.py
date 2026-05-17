"""Advanced Kubernetes Intelligence - Detects resource anomalies and pressure"""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class PressureIssue:
    """Represents a resource pressure issue"""
    resource_type: str  # cpu, memory, storage
    pressure_type: str  # exhaustion, imbalance, fragmentation
    saturation_percent: float
    affected_pods: list[str]
    mitigation_recommendation: str
    severity: str  # low, medium, high, critical


class AdvancedKubernetesIntelligence:
    """Analyzes Kubernetes resource pressure and anomalies"""

    async def analyze_namespace_pressure(
        self,
        cluster_id: UUID,
        namespace: str,
        pods: list[dict],
        nodes: list[dict],
    ) -> list[PressureIssue]:
        """Analyze resource pressure in namespace"""

        issues = []

        # Detect noisy neighbors
        noisy = await self.detect_noisy_neighbors(namespace, pods)
        for issue in noisy:
            issues.append(issue)

        # Detect resource imbalance
        imbalance = await self.detect_resource_imbalance(nodes)
        if imbalance:
            issues.append(imbalance)

        # Detect orphaned PVCs
        pvcs = [p for p in pods if p.get("has_pvc")]
        orphaned = await self.detect_orphaned_pvcs(namespace, pvcs, pods)
        for issue in orphaned:
            issues.append(issue)

        # Detect zombie workloads
        zombies = await self.detect_zombie_workloads(namespace, pods)
        for issue in zombies:
            issues.append(issue)

        # Detect cluster saturation
        saturation = await self.detect_cluster_saturation(nodes, pods)
        if saturation:
            issues.append(saturation)

        logger.info(f"Found {len(issues)} pressure issues in {namespace}")
        return issues

    async def detect_noisy_neighbors(
        self,
        namespace: str,
        pods: list[dict],
    ) -> list[PressureIssue]:
        """Detect pods using excessive resources (noisy neighbors)"""

        issues = []

        if not pods:
            return issues

        # Calculate percentiles
        cpu_values = [p.get("cpu_milli", 0) for p in pods]
        memory_values = [p.get("memory_mb", 0) for p in pods]

        cpu_p95 = self._percentile(cpu_values, 95)
        memory_p95 = self._percentile(memory_values, 95)

        cpu_threshold = cpu_p95 * 2  # 2x percentile
        memory_threshold = memory_p95 * 2

        for pod in pods:
            cpu = pod.get("cpu_milli", 0)
            memory = pod.get("memory_mb", 0)
            pod_name = pod.get("name", "unknown")

            if cpu > cpu_threshold:
                issues.append(
                    PressureIssue(
                        resource_type="cpu",
                        pressure_type="noisy_neighbor",
                        saturation_percent=(cpu / cpu_threshold) * 100,
                        affected_pods=[pod_name],
                        mitigation_recommendation=(
                            f"Pod {pod_name} is using {cpu}m CPU (2x percentile={cpu_threshold:.0f}m). "
                            "Apply QoS class change, node affinity rules, or request resource adjustment."
                        ),
                        severity="high" if cpu > cpu_threshold * 1.5 else "medium",
                    )
                )

            if memory > memory_threshold:
                issues.append(
                    PressureIssue(
                        resource_type="memory",
                        pressure_type="noisy_neighbor",
                        saturation_percent=(memory / memory_threshold) * 100,
                        affected_pods=[pod_name],
                        mitigation_recommendation=(
                            f"Pod {pod_name} is using {memory}MB memory (2x percentile={memory_threshold:.0f}MB). "
                            "Check for memory leak or increase resource requests."
                        ),
                        severity="high" if memory > memory_threshold * 1.5 else "medium",
                    )
                )

        return issues

    async def detect_resource_imbalance(
        self,
        nodes: list[dict],
    ) -> Optional[PressureIssue]:
        """Detect uneven resource distribution across nodes"""

        if not nodes:
            return None

        cpu_available = [n.get("available_cpu", 0) for n in nodes]
        memory_available = [n.get("available_memory", 0) for n in nodes]

        if not cpu_available or not memory_available:
            return None

        # Calculate coefficient of variation
        cpu_cv = self._coefficient_of_variation(cpu_available)
        memory_cv = self._coefficient_of_variation(memory_available)

        # Threshold: 40% imbalance
        if cpu_cv > 0.4 or memory_cv > 0.4:
            worst_node = min(nodes, key=lambda n: n.get("available_cpu", 0))
            best_node = max(nodes, key=lambda n: n.get("available_cpu", 0))

            return PressureIssue(
                resource_type="cpu" if cpu_cv > memory_cv else "memory",
                pressure_type="imbalance",
                saturation_percent=max(cpu_cv, memory_cv) * 100,
                affected_pods=[worst_node.get("name"), best_node.get("name")],
                mitigation_recommendation=(
                    f"Resource imbalance detected (variance={max(cpu_cv, memory_cv):.1%}). "
                    f"Node {worst_node.get('name')} has less resources than {best_node.get('name')}. "
                    "Rebalance workloads or add new nodes."
                ),
                severity="high",
            )

        return None

    async def detect_orphaned_pvcs(
        self,
        namespace: str,
        pvcs: list[dict],
        pods: list[dict],
    ) -> list[PressureIssue]:
        """Detect PVCs without mounted pods"""

        issues = []
        pod_pvcs = set()

        # Collect all mounted PVCs
        for pod in pods:
            mounted = pod.get("mounted_pvcs", [])
            pod_pvcs.update(mounted)

        # Find orphaned
        for pvc in pvcs:
            pvc_name = pvc.get("name", "unknown")
            if pvc_name not in pod_pvcs:
                age_days = pvc.get("age_days", 0)
                status = pvc.get("status", "unknown")

                if status != "Bound" or age_days > 30:
                    issues.append(
                        PressureIssue(
                            resource_type="storage",
                            pressure_type="orphaned_pvc",
                            saturation_percent=0.0,
                            affected_pods=[pvc_name],
                            mitigation_recommendation=(
                                f"PVC {pvc_name} is orphaned (status={status}, age={age_days}d). "
                                "Consider cleanup or troubleshoot mount issues."
                            ),
                            severity="low" if age_days < 30 else "medium",
                        )
                    )

        return issues

    async def detect_zombie_workloads(
        self,
        namespace: str,
        pods: list[dict],
    ) -> list[PressureIssue]:
        """Detect idle/crashed pods (zombies)"""

        issues = []

        for pod in pods:
            pod_name = pod.get("name", "unknown")
            cpu = pod.get("cpu_milli", 0)
            memory = pod.get("memory_mb", 0)
            rps = pod.get("requests_per_second", 0.0)
            age_hours = pod.get("age_hours", 0)
            status = pod.get("status", "unknown")

            # Idle pod: low resources + low traffic + old
            if (
                cpu < 50 and memory < 10 and rps < 0.1 and age_hours > 24 and
                status == "Running"
            ):
                issues.append(
                    PressureIssue(
                        resource_type="cpu",
                        pressure_type="zombie_workload",
                        saturation_percent=0.0,
                        affected_pods=[pod_name],
                        mitigation_recommendation=(
                            f"Pod {pod_name} appears idle (CPU={cpu}m, MEM={memory}MB, RPS={rps:.2f}). "
                            "Consider pod deletion or investigate why it's not receiving traffic."
                        ),
                        severity="low",
                    )
                )

            # Crashed pod
            if status == "CrashLoopBackOff":
                issues.append(
                    PressureIssue(
                        resource_type="cpu",
                        pressure_type="zombie_workload",
                        saturation_percent=0.0,
                        affected_pods=[pod_name],
                        mitigation_recommendation=(
                            f"Pod {pod_name} is in CrashLoopBackOff. "
                            "Check pod logs for startup errors and investigate configuration."
                        ),
                        severity="high",
                    )
                )

        return issues

    async def detect_cluster_saturation(
        self,
        nodes: list[dict],
        pods: list[dict],
    ) -> Optional[PressureIssue]:
        """Detect cluster-wide saturation"""

        if not nodes:
            return None

        # Calculate utilization
        total_cpu_available = sum(n.get("available_cpu", 0) for n in nodes)
        total_memory_available = sum(n.get("available_memory", 0) for n in nodes)
        total_cpu_requested = sum(p.get("cpu_milli", 0) for p in pods)
        total_memory_requested = sum(p.get("memory_mb", 0) for p in pods)

        if total_cpu_available > 0 and total_memory_available > 0:
            cpu_utilization = total_cpu_requested / total_cpu_available
            memory_utilization = total_memory_requested / total_memory_available

            if cpu_utilization > 0.9 or memory_utilization > 0.9:
                return PressureIssue(
                    resource_type="cpu" if cpu_utilization > memory_utilization else "memory",
                    pressure_type="exhaustion",
                    saturation_percent=max(cpu_utilization, memory_utilization) * 100,
                    affected_pods=[n.get("name") for n in nodes],
                    mitigation_recommendation=(
                        f"Cluster is saturated (CPU={cpu_utilization:.1%}, MEM={memory_utilization:.1%}). "
                        "Add new nodes or move workloads to other clusters."
                    ),
                    severity="critical" if max(cpu_utilization, memory_utilization) > 0.95 else "high",
                )

        return None

    def _percentile(self, values: list[float], p: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int((p / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _coefficient_of_variation(self, values: list[float]) -> float:
        """Calculate coefficient of variation (std dev / mean)"""
        if not values or all(v == 0 for v in values):
            return 0.0

        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0

        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        return std_dev / mean


# Singleton instance
advanced_k8s_intelligence = AdvancedKubernetesIntelligence()
