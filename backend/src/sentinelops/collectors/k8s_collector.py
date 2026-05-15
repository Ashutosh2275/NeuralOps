from datetime import datetime
from typing import Any
from uuid import uuid4

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import EventType, PodEvent, Severity

log = get_logger(__name__)


class KubernetesCollector:
    """Collects pods, services, deployments, and topology from Kubernetes API."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._core_api: Any = None
        self._apps_api: Any = None

    async def _init_clients(self) -> bool:
        if self._core_api is not None:
            return True
        try:
            from kubernetes_asyncio import client, config

            if self._settings.k8s_in_cluster:
                config.load_incluster_config()
            elif self._settings.k8s_kubeconfig:
                await config.load_kube_config(config_file=self._settings.k8s_kubeconfig)
            else:
                await config.load_kube_config()
            self._core_api = client.CoreV1Api()
            self._apps_api = client.AppsV1Api()
            return True
        except Exception as e:
            log.warning("k8s_api_unavailable", error=str(e))
            return False

    async def collect_all(self, namespace: str | None = None) -> dict[str, list[dict[str, Any]]]:
        ns = namespace or self._settings.k8s_namespace
        if not await self._init_clients():
            return self._demo_all(ns)

        pods = await self._collect_pods_raw(ns)
        services = await self._collect_services_raw(ns)
        deployments = await self._collect_deployments_raw(ns)
        topology = self._build_topology_events(pods, services, deployments, ns)
        dependencies = self._build_dependency_events(pods, services, ns)

        return {
            "pods": pods,
            "services": services,
            "deployments": deployments,
            "topology": topology,
            "dependencies": dependencies,
        }

    async def collect_pods(self, namespace: str | None = None) -> list[PodEvent]:
        ns = namespace or self._settings.k8s_namespace
        raw = (await self.collect_all(ns))["pods"]
        return [
            PodEvent(
                event_id=uuid4(),
                source="k8s-collector",
                cluster_id="default",
                namespace=r["namespace"],
                severity=Severity(r.get("severity", "info")),
                payload=r,
                labels=r.get("labels", {}),
            )
            for r in raw
        ]

    async def _collect_pods_raw(self, namespace: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        try:
            if namespace == "*":
                pod_list = await self._core_api.list_pod_for_all_namespaces()
            else:
                pod_list = await self._core_api.list_namespaced_pod(namespace=namespace)

            for pod in pod_list.items:
                restart_count = sum(
                    (c.restart_count or 0) for c in (pod.status.container_statuses or [])
                )
                reason = self._extract_reason(pod)
                severity = "info"
                if pod.status.phase == "Failed" or "CrashLoop" in reason:
                    severity = "critical"
                elif restart_count >= self._settings.anomaly_restart_burst_count:
                    severity = "critical"
                elif restart_count > 0:
                    severity = "warning"

                owner_refs = [
                    {"kind": r.kind, "name": r.name}
                    for r in (pod.metadata.owner_references or [])
                ]
                events.append({
                    "namespace": pod.metadata.namespace or "default",
                    "pod_name": pod.metadata.name,
                    "node_name": pod.spec.node_name,
                    "phase": pod.status.phase,
                    "reason": reason,
                    "restart_count": restart_count,
                    "severity": severity,
                    "owner_refs": owner_refs,
                    "labels": dict(pod.metadata.labels or {}),
                    "containers": [
                        {
                            "name": c.name,
                            "image": c.image,
                            "ready": c.ready,
                            "restart_count": c.restart_count,
                        }
                        for c in (pod.status.container_statuses or [])
                    ],
                    "timestamp": datetime.utcnow(),
                })
        except Exception as e:
            log.error("k8s_pods_failed", error=str(e))
            return self._demo_all(namespace)["pods"]
        return events

    async def _collect_services_raw(self, namespace: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        try:
            if namespace == "*":
                svc_list = await self._core_api.list_service_for_all_namespaces()
            else:
                svc_list = await self._core_api.list_namespaced_service(namespace=namespace)

            for svc in svc_list.items:
                selector = dict(svc.spec.selector or {})
                events.append({
                    "namespace": svc.metadata.namespace,
                    "service_name": svc.metadata.name,
                    "service_type": svc.spec.type,
                    "selector": selector,
                    "ports": [
                        {"port": p.port, "protocol": p.protocol}
                        for p in (svc.spec.ports or [])
                    ],
                    "labels": dict(svc.metadata.labels or {}),
                    "timestamp": datetime.utcnow(),
                })
        except Exception as e:
            log.error("k8s_services_failed", error=str(e))
        return events

    async def _collect_deployments_raw(self, namespace: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        try:
            if namespace == "*":
                dep_list = await self._apps_api.list_deployment_for_all_namespaces()
            else:
                dep_list = await self._apps_api.list_namespaced_deployment(namespace=namespace)

            for dep in dep_list.items:
                spec_replicas = dep.spec.replicas or 0
                ready = dep.status.ready_replicas or 0
                events.append({
                    "namespace": dep.metadata.namespace,
                    "deployment_name": dep.metadata.name,
                    "replicas": spec_replicas,
                    "ready_replicas": ready,
                    "scaling_event": ready != spec_replicas,
                    "labels": dict(dep.metadata.labels or {}),
                    "timestamp": datetime.utcnow(),
                })
        except Exception as e:
            log.error("k8s_deployments_failed", error=str(e))
        return events

    def _build_topology_events(
        self,
        pods: list[dict[str, Any]],
        services: list[dict[str, Any]],
        deployments: list[dict[str, Any]],
        namespace: str,
    ) -> list[dict[str, Any]]:
        nodes = []
        edges = []
        for pod in pods:
            nodes.append({
                "id": f"{pod['namespace']}/Pod/{pod['pod_name']}",
                "kind": "Pod",
                "name": pod["pod_name"],
                "namespace": pod["namespace"],
                "phase": pod.get("phase"),
            })
        for svc in services:
            sid = f"{svc['namespace']}/Service/{svc['service_name']}"
            nodes.append({"id": sid, "kind": "Service", "name": svc["service_name"], "namespace": svc["namespace"]})
            selector_app = svc.get("selector", {}).get("app")
            if selector_app:
                for pod in pods:
                    if pod.get("labels", {}).get("app") == selector_app:
                        edges.append({
                            "source": f"{pod['namespace']}/Pod/{pod['pod_name']}",
                            "target": sid,
                            "edge_type": "routes_to",
                            "confidence": 0.9,
                        })
        for dep in deployments:
            nodes.append({
                "id": f"{dep['namespace']}/Deployment/{dep['deployment_name']}",
                "kind": "Deployment",
                "name": dep["deployment_name"],
            })
        return [{
            "namespace": namespace,
            "topology_context": {"nodes": nodes, "edges": edges},
            "node_count": len(nodes),
            "edge_count": len(edges),
            "timestamp": datetime.utcnow(),
        }]

    def _build_dependency_events(
        self,
        pods: list[dict[str, Any]],
        services: list[dict[str, Any]],
        namespace: str,
    ) -> list[dict[str, Any]]:
        deps = []
        for svc in services:
            selector_app = svc.get("selector", {}).get("app")
            for pod in pods:
                if selector_app and pod.get("labels", {}).get("app") == selector_app:
                    deps.append({
                        "namespace": namespace,
                        "source_name": pod["pod_name"],
                        "source_kind": "Pod",
                        "target_name": svc["service_name"],
                        "target_kind": "Service",
                        "edge_type": "depends_on",
                        "discovery_method": "label_selector",
                        "dependency_context": {"selector_app": selector_app},
                        "timestamp": datetime.utcnow(),
                    })
        return deps

    def _extract_reason(self, pod: Any) -> str:
        if pod.status.container_statuses:
            for cs in pod.status.container_statuses:
                if cs.state and cs.state.waiting:
                    return cs.state.waiting.reason or "Waiting"
                if cs.state and cs.state.terminated:
                    return cs.state.terminated.reason or "Terminated"
        return pod.status.phase or "Unknown"

    def _demo_all(self, namespace: str) -> dict[str, list[dict[str, Any]]]:
        pods = [
            {"namespace": namespace, "pod_name": "order-service", "phase": "Running", "reason": "Running", "restart_count": 0, "severity": "info", "labels": {"app": "order"}, "timestamp": datetime.utcnow()},
            {"namespace": namespace, "pod_name": "payment-service", "phase": "Running", "reason": "Running", "restart_count": 1, "severity": "warning", "labels": {"app": "payment"}, "timestamp": datetime.utcnow()},
            {"namespace": namespace, "pod_name": "inventory-service", "phase": "Failed", "reason": "CrashLoopBackOff", "restart_count": 5, "severity": "critical", "labels": {"app": "inventory"}, "timestamp": datetime.utcnow()},
            {"namespace": namespace, "pod_name": "postgres-0", "phase": "Running", "reason": "Running", "restart_count": 0, "severity": "info", "labels": {"app": "postgres"}, "timestamp": datetime.utcnow()},
        ]
        services = [
            {"namespace": namespace, "service_name": "order-service", "selector": {"app": "order"}, "timestamp": datetime.utcnow()},
            {"namespace": namespace, "service_name": "payment-service", "selector": {"app": "payment"}, "timestamp": datetime.utcnow()},
            {"namespace": namespace, "service_name": "inventory-service", "selector": {"app": "inventory"}, "timestamp": datetime.utcnow()},
        ]
        topology = self._build_topology_events(pods, services, [], namespace)
        dependencies = self._build_dependency_events(pods, services, namespace)
        return {"pods": pods, "services": services, "deployments": [], "topology": topology, "dependencies": dependencies}
