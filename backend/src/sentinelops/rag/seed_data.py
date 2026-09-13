"""
Seed operational knowledge corpus for SentinelOps AI.
Contains genuine production-grade Kubernetes runbooks, post-mortems, and architectural guides.
"""
from __future__ import annotations

from sentinelops.rag.chunker import DocumentMetadata

SEED_DOCUMENTS: list[tuple[DocumentMetadata, str]] = [
    (
        DocumentMetadata(
            document_id="runbook-crashloopbackoff",
            title="Kubernetes Pod CrashLoopBackOff Runbook",
            source="k8s-operations/runbooks/crashloopbackoff.md",
            document_type="runbook",
            service="all",
            namespace="all",
            tags=["crashloopbackoff", "pod", "restart", "liveness", "readiness"],
        ),
        """# Kubernetes Pod CrashLoopBackOff Troubleshooting Runbook

## Overview & Symptoms
A pod in `CrashLoopBackOff` indicates that the container repeatedly starts, fails, and restarts with exponential backoff delay. The status shows restarts climbing continuously.

## Common Root Causes
1. **Application Runtime Panic / Uncaught Exception**: Missing configuration, database connection failure at startup, unhandled promise rejection.
2. **Failed Liveness / Readiness Probes**: Probe timeout too aggressive (e.g. initialDelaySeconds too low for JVM/Node warm-up).
3. **Missing Environment Variables or Secrets**: Pod cannot resolve mandatory keys from ConfigMaps or Secrets.
4. **CGroup OOMKilled**: Memory limit reached during initialization before liveness check runs.
5. **Entrypoint or Command Mismatch**: Executable not found or exit code 127 in container image.

## Immediate Diagnostics Commands
```bash
# 1. Inspect exit codes and termination reason
kubectl describe pod <pod-name> -n <namespace>

# 2. Check previous container crash logs
kubectl logs <pod-name> -n <namespace> --previous --tail=100

# 3. Check for OOMKilled signal (Exit Code 137)
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'
```

## Remediation Steps
1. If termination reason is `OOMKilled` (Exit Code 137), increase container memory limits:
```bash
kubectl set resources deployment/<deployment-name> -n <namespace> --limits=memory=1Gi --requests=memory=512Mi
```
2. If termination reason is `Error` (Exit Code 1), verify configuration and database credentials in the relevant Secret.
3. If probe failure, adjust `initialDelaySeconds` and `periodSeconds` in deployment manifest.
""",
    ),
    (
        DocumentMetadata(
            document_id="runbook-oomkilled",
            title="Kubernetes CGroup OOMKilled Mitigation Runbook",
            source="k8s-operations/runbooks/oomkilled.md",
            document_type="runbook",
            service="all",
            namespace="all",
            tags=["oomkilled", "memory", "cgroup", "limits", "heap"],
        ),
        """# Kubernetes CGroup OOMKilled (Exit Code 137) Mitigation Runbook

## Symptoms
- Pod status displays `OOMKilled` or restarts increment without explicit application crash logs.
- Linux kernel `dmesg` reports `invoked oom-killer: gfp_mask=0x...` for container PID.

## Diagnostic Procedures
```bash
# Check memory usage trends
kubectl top pod <pod-name> -n <namespace> --containers

# Check event timeline for node or pod memory eviction
kubectl get events -n <namespace> --field-selector reason=Evicted --sort-by='.metadata.creationTimestamp'
```

## Remediation & Recovery
1. Immediately scale up memory limit if traffic is within normal thresholds:
```bash
kubectl patch deployment <deployment-name> -n <namespace> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```
2. For memory leaks (progressive linear growth over hours):
- Trigger heap dump / profiling.
- Rollout rolling restart to purge leaked memory while investigation is underway:
```bash
kubectl rollout restart deployment/<deployment-name> -n <namespace>
```
""",
    ),
    (
        DocumentMetadata(
            document_id="runbook-pvc-saturation",
            title="Kubernetes PVC Storage Saturation & IO Pressure Runbook",
            source="k8s-operations/runbooks/pvc_saturation.md",
            document_type="runbook",
            service="postgres-primary",
            namespace="default",
            tags=["pvc", "storage", "disk", "saturation", "io"],
        ),
        """# Kubernetes PVC Storage Saturation Runbook

## Overview
PersistentVolumeClaims (PVCs) reaching > 90% utilization risk filesystem corruption, database read-only failover, or pod crash loops due to no space left on device (`ENOSPC`).

## Diagnosis
```bash
# Check persistent volume claim status and capacity
kubectl get pvc -n <namespace>

# Execute df inside pod to verify filesystem usage
kubectl exec -it <pod-name> -n <namespace> -- df -h
```

## Remediation Workflow
1. For volume expansion enabled storage classes (e.g. EBS, Ceph, Local-Path with CSI expansion):
```bash
kubectl patch pvc <pvc-name> -n <namespace> -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'
```
2. Clean up rotated logs, dump files, or temporary WAL segments:
```bash
kubectl exec <pod-name> -n <namespace> -- find /var/log -type f -name "*.gz" -mtime +7 -delete
```
""",
    ),
    (
        DocumentMetadata(
            document_id="postmortem-2026-payment-db-cascade",
            title="Incident Post-Mortem: Payment Service Memory Leak & DB Pool Cascading Failure",
            source="postmortems/2026/incident-2026-0042.md",
            document_type="postmortem",
            service="payment-service",
            namespace="default",
            tags=["payment-service", "postgres-primary", "cascade", "pool", "connection_exhaustion"],
        ),
        """# Post-Mortem: Payment Service Memory Leak & DB Connection Exhaustion

## Incident Summary
On May 12, 2026, `payment-service` experienced a progressive memory leak under peak order processing. As memory pressure exceeded 90%, garbage collection pauses increased request latency from 45ms to 3200ms.

Because HTTP clients continued retrying without backoff, connection pools between `checkout-service`, `payment-service`, and `postgres-primary` became saturated. `postgres-primary` reached its maximum connection limit of 500, causing downstream `api-gateway` 504 Gateway Timeouts.

## Root Cause
A cache eviction bug in `payment-service` un-bounded transaction context tracking held onto connection objects in memory.

## Resolution
1. Temporary Mitigation:
```bash
kubectl rollout restart deployment/payment-service -n default
kubectl set env deployment/payment-service -n default DB_MAX_CONNECTIONS=50 DB_IDLE_TIMEOUT=30
```
2. Permanent Fix: Fixed Cache TTL eviction policy in v2.4.1 and implemented exponential jitter backoff on upstream `checkout-service`.
""",
    ),
    (
        DocumentMetadata(
            document_id="arch-services-network",
            title="SentinelOps Core Microservices Architecture & Dependency Topology",
            source="architecture/core_topology.md",
            document_type="architecture",
            service="all",
            namespace="default",
            tags=["architecture", "topology", "dependencies", "sla", "critical_path"],
        ),
        """# Core Microservices Architecture & Dependency Topology

## Critical Request Paths
1. `api-gateway` → `auth-service` → `redis-cache`
2. `api-gateway` → `checkout-service` → `payment-service` → `postgres-primary`
3. `api-gateway` → `inventory-service` → `postgres-primary`

## Resilience Tier Classification
- **Tier 1 (Mission Critical)**: `api-gateway`, `auth-service`, `payment-service`, `postgres-primary`. Required availability: 99.99%.
- **Tier 2 (Core Business)**: `checkout-service`, `inventory-service`. Required availability: 99.9%.
- **Tier 3 (Auxiliary)**: `recommendation-engine`, `analytics-worker`. Required availability: 99.5%.

## Failure Propagation Rules
- A degradation in `postgres-primary` directly impacts both `payment-service` and `inventory-service`.
- Memory pressure in `payment-service` cascades to `checkout-service` within 90 seconds due to thread saturation.
""",
    ),
    (
        DocumentMetadata(
            document_id="runbook-dependency-outage",
            title="Downstream Dependency Outage & Cascading Failure Runbook",
            source="k8s-operations/runbooks/dependency_outage.md",
            document_type="runbook",
            service="all",
            namespace="all",
            tags=["dependency", "outage", "cascade", "pool", "database"],
        ),
        """# Downstream Dependency Outage & Cascading Failure Runbook

## Overview
A downstream dependency outage occurs when a critical upstream service or database becomes unavailable (e.g. 0 replicas, network isolation, or connection exhaustion), propagating 500/504 errors across dependent services.

## Symptoms
- Connection refused or timeout errors to downstream endpoints (e.g. payment-db, redis).
- Cascading thread pool and connection pool exhaustion on calling services.
- Upstream circuit breakers tripping open.

## Diagnostics & Remediation
1. Verify downstream service and pod readiness:
```bash
kubectl get pods,endpoints -n <namespace> -l app=<downstream-service>
```
2. Scale up downstream dependency if replicas reached 0:
```bash
kubectl scale deployment/<downstream-service> -n <namespace> --replicas=1
```
3. Purge saturated connection pools and verify circuit breaker recovery.
""",
    ),
    (
        DocumentMetadata(
            document_id="runbook-healthy-workload",
            title="Normal Baseline Operations & Workload Health Verification Guide",
            source="k8s-operations/runbooks/healthy_workload.md",
            document_type="runbook",
            service="all",
            namespace="all",
            tags=["healthy", "baseline", "normal", "slo", "heartbeat"],
        ),
        """# Normal Baseline Operations & Workload Health Verification Guide

## Overview
Normal baseline operations represent standard steady-state execution across all microservices with zero crash loops, healthy probe responses, and latencies within SLA thresholds.

## Indicators of Healthy Operation
- Container restart count remains 0 over 24-hour periods.
- Continuous heartbeat logs emitting `status=OK`.
- CPU and memory utilization stable below 70% threshold.
- All pods reporting `1/1 Running` status with ready probes passing.

## Verification Procedures
```bash
kubectl get pods -n <namespace> --field-selector=status.phase=Running
```
No remediation required under normal baseline operations.
""",
    ),
]