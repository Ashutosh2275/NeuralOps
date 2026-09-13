import json
from uuid import UUID

from sentinelops.models.predictive import K8sResourceIntelligence


class AdvancedKubernetesIntelligence:
    """Analyzes Kubernetes resource pressure and infrastructure issues."""

    def __init__(self):
        self.pressure_thresholds = {
            "cpu": 85.0,
            "memory": 80.0,
            "disk": 85.0,
            "network": 80.0,
        }

    async def analyze_namespace_pressure(
        self,
        cluster_id: UUID,
        namespace: str,
        pods: list[dict],
        nodes: list[dict],
    ) -> list[K8sResourceIntelligence]:
        """Analyze pressure in a namespace."""
        issues = []

        # Calculate namespace metrics
        total_cpu = sum(p.get("cpu_percent", 0) for p in pods)
        total_memory = sum(p.get("memory_percent", 0) for p in pods)
        pod_count = len(pods)

        # CPU pressure
        avg_cpu = total_cpu / pod_count if pod_count > 0 else 0
        if avg_cpu > self.pressure_thresholds["cpu"]:
            issue = K8sResourceIntelligence(
                cluster_id=cluster_id,
                namespace=namespace,
                resource_type="cpu",
                pressure_type="saturation",
                pressure_score=min(1.0, avg_cpu / 100.0),
                saturation_percent=avg_cpu,
                affected_workloads=json.dumps([p.get("name") for p in pods]),
                mitigation_json=json.dumps({
                    "recommendation": "Scale up pod replicas or migrate to nodes with more capacity",
                    "priority": "high" if avg_cpu > 95 else "medium",
                }),
            )
            issues.append(issue)

        # Memory pressure
        avg_memory = total_memory / pod_count if pod_count > 0 else 0
        if avg_memory > self.pressure_thresholds["memory"]:
            issue = K8sResourceIntelligence(
                cluster_id=cluster_id,
                namespace=namespace,
                resource_type="memory",
                pressure_type="exhaustion",
                pressure_score=min(1.0, avg_memory / 100.0),
                saturation_percent=avg_memory,
                affected_workloads=json.dumps([p.get("name") for p in pods]),
                mitigation_json=json.dumps({
                    "recommendation": "Increase memory limits or add node resources",
                    "priority": "critical" if avg_memory > 95 else "high",
                }),
            )
            issues.append(issue)

        # Pod density analysis
        high_density_issue = await self._analyze_pod_density(
            cluster_id=cluster_id,
            namespace=namespace,
            pod_count=pod_count,
            node_count=len(nodes),
        )
        if high_density_issue:
            issues.append(high_density_issue)

        return issues

    async def detect_noisy_neighbors(
        self,
        namespace: str,
        pods: list[dict],
    ) -> list[dict]:
        """Detect pods consuming excessive resources."""
        noisy_pods = []

        # Calculate resource percentiles
        cpu_values = [p.get("cpu_percent", p.get("cpu", 0)) for p in pods]
        memory_values = [p.get("memory_percent", p.get("memory", 0)) for p in pods]

        if not cpu_values or not memory_values:
            return noisy_pods

        # Use median if small sample, otherwise 90th percentile excluding extremes
        sorted_cpu = sorted(cpu_values)
        sorted_mem = sorted(memory_values)
        cpu_baseline = sorted_cpu[len(sorted_cpu) // 2] if len(sorted_cpu) <= 4 else sorted_cpu[int(len(sorted_cpu) * 0.75)]
        mem_baseline = sorted_mem[len(sorted_mem) // 2] if len(sorted_mem) <= 4 else sorted_mem[int(len(sorted_mem) * 0.75)]

        for pod in pods:
            cpu = pod.get("cpu_percent", pod.get("cpu", 0))
            memory = pod.get("memory_percent", pod.get("memory", 0))

            if (cpu > max(cpu_baseline * 2.0, 80)) or (memory > max(mem_baseline * 2.0, 80)) or (cpu > 1000):
                noisy_pods.append({
                    "name": pod.get("name"),
                    "pod_name": pod.get("name"),
                    "cpu_percent": cpu,
                    "memory_percent": memory,
                    "impact_score": min(1.0, (cpu / 100.0 + memory / 100.0) / 2.0),
                })

        return noisy_pods

    async def detect_resource_imbalance(
        self,
        nodes: list[dict],
    ) -> dict | None:
        """Detect uneven resource distribution across nodes."""
        if not nodes:
            return None

        # Check if nodes provide raw usage percentage or available capacity
        cpu_usage = [n.get("cpu_usage_percent", n.get("available_cpu", 0)) for n in nodes]
        memory_usage = [n.get("memory_usage_percent", n.get("available_memory", 0)) for n in nodes]

        cpu_max = max(cpu_usage) if cpu_usage else 0
        cpu_min = min(cpu_usage) if cpu_usage else 0
        cpu_variance = cpu_max - cpu_min

        # Normalized variance ratio between 0.0 and 1.0 (e.g. (max - min) / max)
        normalized_variance = (cpu_max - cpu_min) / cpu_max if cpu_max > 0 else 0.0

        memory_variance = max(memory_usage) - min(memory_usage) if memory_usage else 0

        # Flag if variance is large
        if cpu_variance > 40 or memory_variance > 40 or normalized_variance > 0.3:
            return {
                "issue_type": "resource_imbalance",
                "variance": round(normalized_variance, 3),
                "cpu_variance": cpu_variance,
                "memory_variance": memory_variance,
                "recommendation": "Rebalance pods across nodes using topology spread constraints",
                "severity": "high" if cpu_variance > 60 else "medium",
            }

        return None

    async def detect_orphaned_pvcs(
        self,
        namespace: str,
        pvcs: list[dict],
        pods: list[dict],
    ) -> list[dict]:
        """Detect PVCs that aren't mounted by any pod."""
        orphaned = []

        pod_pvcs = set()
        for pod in pods:
            volumes = pod.get("volumes", [])
            for vol in volumes:
                pvc_name = vol.get("pvc_name") if isinstance(vol, dict) else str(vol)
                if pvc_name:
                    pod_pvcs.add(pvc_name)

        for pvc in pvcs:
            name = pvc.get("name")
            status = pvc.get("status")
            if name not in pod_pvcs or status == "Unbound":
                orphaned.append({
                    "pvc_name": name,
                    "size_gb": pvc.get("size_gb", 0),
                    "age_days": pvc.get("age_days", 0),
                    "status": status,
                    "recommendation": "Delete orphaned PVC to reclaim storage",
                })

        return orphaned

    async def detect_zombie_workloads(
        self,
        namespace: str,
        pods: list[dict],
    ) -> list[dict]:
        """Detect pods that are not serving traffic or contributing to service."""
        zombies = []

        for pod in pods:
            cpu = pod.get("cpu_percent", pod.get("cpu", 0))
            memory = pod.get("memory_percent", pod.get("memory", 0))
            traffic = pod.get("traffic_requests_per_sec", pod.get("rps", 0))
            age_hours = pod.get("age_hours", pod.get("age_seconds", 0) / 3600.0)

            # Pod is zombie if it has low traffic and low resource usage for extended time (>24h)
            if traffic < 0.1 and cpu <= 5 and memory <= 10 and age_hours >= 24:
                zombies.append({
                    "name": pod.get("name"),
                    "pod_name": pod.get("name"),
                    "cpu_percent": cpu,
                    "memory_percent": memory,
                    "traffic_rps": traffic,
                    "age_hours": age_hours,
                    "recommendation": "Delete zombie pod or fix deployment to ensure proper pod lifecycle",
                })

        return zombies

    async def _analyze_pod_density(
        self,
        cluster_id: UUID,
        namespace: str,
        pod_count: int,
        node_count: int,
    ) -> K8sResourceIntelligence | None:
        """Analyze pod density (pods per node)."""
        if node_count == 0:
            return None

        pods_per_node = pod_count / node_count

        # High density threshold: > 30 pods per node
        if pods_per_node > 30:
            return K8sResourceIntelligence(
                cluster_id=cluster_id,
                namespace=namespace,
                resource_type="pod_density",
                pressure_type="density",
                pressure_score=min(1.0, pods_per_node / 50.0),
                saturation_percent=pods_per_node * 3.33,  # Convert to percentage
                affected_workloads=json.dumps([f"all_{pod_count}_pods"]),
                mitigation_json=json.dumps({
                    "recommendation": f"Reduce pod density: {pods_per_node:.1f} pods/node. Consider horizontal scaling.",
                    "priority": "high" if pods_per_node > 50 else "medium",
                }),
            )

        return None


k8s_intelligence = AdvancedKubernetesIntelligence()
