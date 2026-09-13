"""
Workloads API endpoints for SentinelOps AI.
Exposes live Kubernetes workloads, pods, deployments, container logs, and Prometheus metrics.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query

from sentinelops.collectors.k8s_collector import KubernetesCollector
from sentinelops.collectors.loki_collector import LokiCollector
from sentinelops.collectors.prometheus_collector import PrometheusCollector
from sentinelops.config import get_settings

router = APIRouter(prefix="/workloads", tags=["workloads"])


@router.get("/overview", summary="High-level workload health and operational summary")
async def get_workloads_overview(namespace: Optional[str] = Query(None)) -> dict[str, Any]:
    settings = get_settings()
    ns = namespace or "sentinelops-e2e"
    k8s = KubernetesCollector()
    data = await k8s.collect_all(ns)

    pods = data.get("pods", [])
    deployments = data.get("deployments", [])

    running_pods = sum(1 for p in pods if p.get("phase") == "Running" and p.get("ready"))
    failing_pods = sum(1 for p in pods if p.get("restart_count", 0) > 0 or p.get("phase") in ("Failed", "CrashLoopBackOff"))
    total_restarts = sum(p.get("restart_count", 0) for p in pods)

    return {
        "namespace": ns,
        "total_pods": len(pods),
        "running_pods": running_pods,
        "failing_pods": failing_pods,
        "total_deployments": len(deployments),
        "total_restarts": total_restarts,
        "status": "CRITICAL" if failing_pods > 0 else "HEALTHY",
    }


@router.get("/pods", summary="List live Kubernetes pods with status and container metrics")
async def list_pods(namespace: Optional[str] = Query(None)) -> dict[str, Any]:
    settings = get_settings()
    ns = namespace or "sentinelops-e2e"
    k8s = KubernetesCollector()
    data = await k8s.collect_all(ns)
    pods = data.get("pods", [])

    return {
        "namespace": ns,
        "count": len(pods),
        "pods": pods,
    }


@router.get("/deployments", summary="List live Kubernetes deployments")
async def list_deployments(namespace: Optional[str] = Query(None)) -> dict[str, Any]:
    settings = get_settings()
    ns = namespace or "sentinelops-e2e"
    k8s = KubernetesCollector()
    data = await k8s.collect_all(ns)
    deployments = data.get("deployments", [])

    return {
        "namespace": ns,
        "count": len(deployments),
        "deployments": deployments,
    }


@router.get("/logs", summary="Fetch real container logs from Loki")
async def get_workload_logs(
    namespace: Optional[str] = Query(None),
    pod_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    settings = get_settings()
    ns = namespace or "sentinelops-e2e"
    loki = LokiCollector(settings)
    logs = await loki.collect(ns)

    if pod_name:
        logs = [l for l in logs if pod_name in l.get("pod_name", "")]

    return {
        "namespace": ns,
        "pod_name": pod_name,
        "count": len(logs[:limit]),
        "logs": logs[:limit],
    }


@router.get("/metrics", summary="Fetch live container telemetry from Prometheus")
async def get_workload_metrics(
    namespace: Optional[str] = Query(None),
    pod_name: Optional[str] = Query(None),
) -> dict[str, Any]:
    settings = get_settings()
    ns = namespace or "sentinelops-e2e"
    prom = PrometheusCollector(settings)
    metrics = await prom.collect(ns)

    if pod_name:
        metrics = [m for m in metrics if pod_name in str(m.get("pod_name") or m.get("service_name") or "")]

    return {
        "namespace": ns,
        "pod_name": pod_name,
        "count": len(metrics),
        "metrics": metrics,
    }


@router.get("/pods/{namespace}/{pod_name}", summary="Fetch single pod detailed status, container states, and telemetry")
async def get_pod_detail(namespace: str, pod_name: str) -> dict[str, Any]:
    from fastapi import HTTPException
    k8s = KubernetesCollector()
    data = await k8s.collect_all(namespace)
    pods = data.get("pods", [])
    pod = next((p for p in pods if p.get("pod_name") == pod_name or pod_name in p.get("pod_name", "")), None)
    if not pod:
        raise HTTPException(status_code=404, detail=f"Pod '{pod_name}' in namespace '{namespace}' not found")

    settings = get_settings()
    loki = LokiCollector(settings)
    logs = await loki.collect(namespace)
    pod_logs = [l for l in logs if pod.get("pod_name") in l.get("pod_name", "")][:50]

    prom = PrometheusCollector(settings)
    metrics = await prom.collect(namespace)
    pod_metrics = [m for m in metrics if pod.get("pod_name") in str(m.get("pod_name") or m.get("service_name") or "")]

    return {
        "pod": pod,
        "logs": pod_logs,
        "metrics": pod_metrics,
    }

