"""
System Information & Configuration API endpoints for SentinelOps AI.
Provides platform environment details, connected daemon topologies, and RBAC metadata.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from sentinelops.config import get_settings
from sentinelops.security.auth import get_current_user, User

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/session", summary="Retrieve active authenticated operator session and RBAC role")
async def get_session_info(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
    }


@router.get("/info", summary="Retrieve verified platform configuration and environment topology")
async def get_system_info() -> dict[str, Any]:
    settings = get_settings()

    return {
        "platform": {
            "name": settings.app_name,
            "version": "1.0.0",
            "environment": settings.app_env,
            "cluster_id": "00000000-0000-0000-0000-000000000001",
            "namespace": settings.k8s_namespace,
        },
        "ai_engine": {
            "provider": "ollama",
            "llm_model": settings.ollama_model,
            "embedding_model": settings.ollama_embedding_model,
            "context_length": settings.ollama_max_tokens,
            "gpu_acceleration": "NVIDIA GeForce RTX 3050 Ti Laptop GPU (CUDA)",
            "temperature": 0.2,
        },
        "infrastructure": {
            "kubernetes_endpoint": "https://172.19.224.117:6443 (WSL2 K3s v1.31.5)",
            "prometheus_url": settings.prometheus_url,
            "loki_url": settings.loki_url,
            "redis_host": f"{settings.redis_host}:{settings.redis_port}",
            "postgres_host": f"{settings.postgres_host}:{settings.postgres_port}",
            "vector_store_path": "data/rag_store/vectors.db (SQLite)",
        },
        "governance": {
            "autonomous_mode": True,
            "zero_trust_enclave": True,
            "human_approval_required_for_remediation": True,
            "audit_trail_enabled": True,
            "rbac_roles": ["viewer", "operator", "admin"],
        },
    }
