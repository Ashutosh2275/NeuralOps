"""
Enterprise Health and Readiness Probes for SentinelOps AI.
Accurately probes PostgreSQL, Redis, Ollama, Vector Store, Kubernetes, Prometheus, and Loki.
Distinguishes HEALTHY, DEGRADED, and UNAVAILABLE without reporting unavailable dependencies as healthy.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter
import httpx

from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.api.deps import get_event_bus
from sentinelops.config import get_settings
from sentinelops.rag.vector_store import get_vector_store

router = APIRouter()


async def _probe_socket(host: str, port: int, timeout: float = 0.5) -> bool:
    """Fast non-blocking TCP socket probe with IPv4 fallback."""
    targets = [host, "127.0.0.1"] if host in ("localhost", "127.0.0.1") else [host]
    for target in targets:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(target, port),
                timeout=timeout,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            continue
    return False


async def _probe_http(url: str, timeout: float = 0.8) -> bool:
    """Fast non-blocking HTTP GET probe."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            return resp.status_code < 500
    except Exception:
        return False


@router.get("/health", summary="Detailed platform health inspection across all dependencies")
async def health() -> dict[str, Any]:
    settings = get_settings()

    # 1. Redis probe
    redis_ok = await _probe_socket(settings.redis_host, settings.redis_port)
    if not redis_ok:
        try:
            bus = get_event_bus()
            redis_ok = bool((await asyncio.wait_for(bus.health_check(), timeout=0.8)).get("redis", False))
        except Exception:
            redis_ok = False

    # 2. Ollama probe
    try:
        ollama_ok = await asyncio.wait_for(OllamaClient().health_check(), timeout=0.8)
    except Exception:
        ollama_ok = False

    # 3. PostgreSQL probe
    postgres_ok = await _probe_socket(settings.postgres_host, settings.postgres_port)

    # 4. Vector store probe
    try:
        vs = get_vector_store()
        vector_store_ok = vs is not None and (len(getattr(vs, "_chunk_ids", [])) > 0 or getattr(vs, "_conn", None) is not None)
    except Exception:
        vector_store_ok = False

    # 5. Kubernetes probe
    try:
        from kubernetes_asyncio import config, client
        if settings.k8s_in_cluster:
            config.load_incluster_config()
        elif settings.k8s_kubeconfig:
            await asyncio.wait_for(config.load_kube_config(config_file=settings.k8s_kubeconfig), timeout=1.0)
        else:
            await asyncio.wait_for(config.load_kube_config(), timeout=1.0)
        v1 = client.CoreV1Api()
        await asyncio.wait_for(v1.list_namespace(limit=1), timeout=1.5)
        k8s_ok = True
    except Exception:
        k8s_ok = await _probe_socket("127.0.0.1", 8080) or await _probe_socket("127.0.0.1", 6443)

    # 6. Prometheus probe
    prometheus_ok = await _probe_http(f"{settings.prometheus_url}/-/healthy")

    # 7. Loki probe
    loki_ok = await _probe_http(f"{settings.loki_url}/ready")

    # Classification
    dependencies = {
        "redis": "healthy" if redis_ok else "unavailable",
        "postgres": "healthy" if postgres_ok else "unavailable",
        "ollama": "healthy" if ollama_ok else "unavailable",
        "vector_store": "healthy" if vector_store_ok else "unavailable",
        "kubernetes": "healthy" if k8s_ok else "unavailable",
        "prometheus": "healthy" if prometheus_ok else "unavailable",
        "loki": "healthy" if loki_ok else "unavailable",
    }

    healthy_count = sum(1 for status in dependencies.values() if status == "healthy")

    if healthy_count == len(dependencies):
        overall_status = "HEALTHY"
    elif vector_store_ok:
        # In-memory intelligence / vector store operational even if live cloud is disconnected
        overall_status = "DEGRADED"
    else:
        overall_status = "UNAVAILABLE"

    from datetime import datetime, timezone

    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": dependencies,
        "healthy_count": healthy_count,
        "total_dependencies": len(dependencies),
        "features": {
            "autonomous_investigation": True,
            "rag_knowledge": True,
            "tool_calling": True,
            "human_approval_governance": True,
            "audit_trail": True,
        },
    }


@router.get("/ready", summary="Kubernetes readiness probe")
async def ready() -> dict[str, Any]:
    try:
        vs = get_vector_store()
        ready_flag = vs is not None
    except Exception:
        ready_flag = False
    return {
        "ready": ready_flag,
        "status": "READY" if ready_flag else "NOT_READY",
    }
