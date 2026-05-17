"""
Synthetic Incident Generator — directly creates DB incidents from simulation triggers.
Bypasses the Redis->CORRELATION event chain to guarantee incidents appear in the UI.
"""
from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.core.database import async_session_factory
from sentinelops.core.logging import get_logger
from sentinelops.models.incident import Incident, IncidentTimeline
from sentinelops.websocket.hub import ws_hub

log = get_logger(__name__)

DEFAULT_CLUSTER_ID = UUID("00000000-0000-0000-0000-000000000001")

INCIDENT_TEMPLATES = {
    "cascading_failure": {
        "title": "Cascading Service Failure: Memory → Pod Restarts → Dependency",
        "severity": "critical",
        "root_cause": "Memory leak in payment-service triggered OOMKill cascade across checkout pipeline",
        "root_service": "payment-service",
        "confidence": 0.94,
        "services": ["payment-service", "api-gateway", "auth-service", "order-service"],
        "chain": [
            {"service": "payment-service", "order": 0, "failure_mode": "OOMKill", "influence": 1.0},
            {"service": "api-gateway", "order": 1, "failure_mode": "connection_refused", "influence": 0.87},
            {"service": "auth-service", "order": 2, "failure_mode": "timeout", "influence": 0.72},
            {"service": "order-service", "order": 3, "failure_mode": "circuit_breaker_open", "influence": 0.61},
        ],
    },
    "api_meltdown": {
        "title": "API Gateway Congestion + Network Latency Storm",
        "severity": "critical",
        "root_cause": "API gateway connection pool exhausted due to 10x traffic spike",
        "root_service": "api-gateway",
        "confidence": 0.91,
        "services": ["api-gateway", "load-balancer", "rate-limiter"],
        "chain": [
            {"service": "api-gateway", "order": 0, "failure_mode": "connection_pool_exhausted", "influence": 1.0},
            {"service": "load-balancer", "order": 1, "failure_mode": "health_check_fail", "influence": 0.78},
        ],
    },
    "ecommerce_checkout": {
        "title": "E-Commerce Checkout Failure: CPU Spike + Dependency Cascade",
        "severity": "high",
        "root_cause": "CPU spike on checkout-service blocked payment processing pipeline",
        "root_service": "checkout-service",
        "confidence": 0.88,
        "services": ["checkout-service", "payment-service", "inventory-service"],
        "chain": [
            {"service": "checkout-service", "order": 0, "failure_mode": "cpu_saturation", "influence": 1.0},
            {"service": "payment-service", "order": 1, "failure_mode": "dependency_failure", "influence": 0.83},
            {"service": "inventory-service", "order": 2, "failure_mode": "timeout", "influence": 0.65},
        ],
    },
    "database_saturation": {
        "title": "Database Connection Pool Exhaustion",
        "severity": "critical",
        "root_cause": "PostgreSQL max_connections limit reached due to connection leak",
        "root_service": "postgres-primary",
        "confidence": 0.96,
        "services": ["postgres-primary", "user-service", "order-service", "payment-service"],
        "chain": [
            {"service": "postgres-primary", "order": 0, "failure_mode": "connection_exhausted", "influence": 1.0},
            {"service": "user-service", "order": 1, "failure_mode": "db_timeout", "influence": 0.91},
        ],
    },
    "kubernetes_exhaustion": {
        "title": "Kubernetes Resource Exhaustion: PVC + Pod Restart Storm",
        "severity": "critical",
        "root_cause": "PVC storage saturation triggered pod evictions causing restart storm",
        "root_service": "logging-service",
        "confidence": 0.89,
        "services": ["logging-service", "metrics-collector", "alertmanager"],
        "chain": [
            {"service": "logging-service", "order": 0, "failure_mode": "pvc_full", "influence": 1.0},
            {"service": "metrics-collector", "order": 1, "failure_mode": "evicted", "influence": 0.77},
        ],
    },
}

TIMELINE_EVENTS = [
    ("Detection", "anomaly_detected", "Anomaly threshold exceeded — auto-detection triggered"),
    ("Triage", "ai_triage", "AI Orchestrator initiated multi-agent triage"),
    ("RCA", "rca_complete", "Root cause identified with {confidence:.0%} confidence"),
    ("Blast Radius", "blast_radius_mapped", "Blast radius mapped: {service_count} services affected"),
    ("Remediation", "remediation_started", "Autonomous remediation pipeline activated"),
    ("Mitigated", "mitigated", "Primary mitigation applied — monitoring recovery"),
]


async def create_incident_from_scenario(scenario_name: str) -> UUID | None:
    """
    Creates a real DB incident + timeline for a given demo scenario.
    Returns the incident UUID.
    """
    template = INCIDENT_TEMPLATES.get(scenario_name)
    if not template:
        log.warning("unknown_scenario", scenario=scenario_name)
        return None

    incident_id = uuid4()

    async with async_session_factory() as session:
        incident = Incident(
            id=incident_id,
            cluster_id=DEFAULT_CLUSTER_ID,
            title=template["title"],
            status="investigating",
            severity=template["severity"],
            root_cause=template["root_cause"],
            root_service=template["root_service"],
            confidence_score=template["confidence"],
            affected_services_json=json.dumps(template["services"]),
            cascade_chain_json=json.dumps(template["chain"]),
            started_at=datetime.utcnow(),
        )
        session.add(incident)

        # Build timeline
        now = datetime.utcnow()
        for i, (title, event_type, desc) in enumerate(TIMELINE_EVENTS):
            tl = IncidentTimeline(
                incident_id=incident_id,
                title=title,
                description=desc.format(
                    confidence=template["confidence"],
                    service_count=len(template["services"]),
                ),
                event_type=event_type,
                timestamp=datetime(
                    now.year, now.month, now.day, now.hour, now.minute, now.second
                ),
            )
            session.add(tl)

        await session.commit()

    # Broadcast incident via WebSocket
    await ws_hub.broadcast("incident", {
        "incident_id": str(incident_id),
        "title": template["title"],
        "severity": template["severity"],
        "root_cause": template["root_cause"],
        "confidence": template["confidence"],
        "services": template["services"],
    })

    # Broadcast cascading failure
    await ws_hub.broadcast("cascading_failure", {
        "origin": template["chain"][0]["service"],
        "affected_count": len(template["chain"]),
        "propagation_depth": len(template["chain"]),
        "escalation_factor": 1.0 + (len(template["chain"]) * 0.15),
        "chain": template["chain"],
    })

    # Broadcast health propagations
    await ws_hub.broadcast("health_propagation", {
        "source": template["root_service"],
        "propagations": [
            {
                "node_id": item["service"],
                "original": "healthy",
                "propagated": "critical" if item["order"] == 0 else "degraded",
                "influence": item["influence"],
            }
            for item in template["chain"]
        ],
    })

    log.info("incident_created", incident_id=str(incident_id), scenario=scenario_name)
    return incident_id
