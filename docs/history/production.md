# SentinelOps AI — Production Deployment & Hardening Guide

## 1. Production Architecture Overview
SentinelOps AI is engineered for resilient, low-privilege execution within Kubernetes and containerized enterprise environments.

---

## 2. Container Hardening (`backend/Dockerfile`)

The production Docker container adheres to the principle of least privilege:
- **Non-Root Execution**: Runs as dedicated system user `sentinelops` (`UID 10001`, `GID 10001`).
- **Minimal Base Image**: Built upon `python:3.12-slim` with intermediate build artifacts removed.
- **Embedded Healthchecks**: Periodic HTTP polling against `/api/v1/ready` (`interval=30s`, `timeout=5s`, `retries=3`).
- **Filesystem Permissions**: Restricted write access limited to `/app/data`.

---

## 3. Kubernetes Manifest Hardening (`infra/kubernetes/`)

Production deployment manifests enforce strict Linux container security controls:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
  seccompProfile:
    type: RuntimeDefault
containers:
  - name: backend
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
    readinessProbe:
      httpGet:
        path: /api/v1/ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
    livenessProbe:
      httpGet:
        path: /api/v1/health
        port: 8000
      initialDelaySeconds: 15
      periodSeconds: 10
```

---

## 4. Health & Readiness Probing (`/health` & `/ready`)

SentinelOps AI implements comprehensive multi-dependency health checking across all 7 operational dependencies:
- **PostgreSQL**: Port socket probe (`postgres_host:postgres_port`)
- **Redis**: Ping probe via Event Bus
- **Ollama**: HTTP health check (`ollama_base_url`)
- **Vector Store**: In-memory dimension & persistence integrity check
- **Kubernetes**: API server connectivity probe
- **Prometheus**: HTTP endpoint check (`/-/healthy`)
- **Loki**: HTTP endpoint check (`/ready`)

### Status Classification:
- `HEALTHY`: All 7 dependencies are operational and reachable.
- `DEGRADED`: Core in-memory / vector store operational; auxiliary telemetry systems (K8s, Prometheus, Loki, or Ollama) offline.
- `UNAVAILABLE`: Critical core services offline.

> [!NOTE]
> Offline dependencies are **NEVER** reported as healthy.

---

## 5. CI/CD Pipeline (`.github/workflows/ci.yml`)

The automated pipeline executes on all pull requests and merges:
1. **Lint & Syntax Validation**: Python bytecode compilation check across `backend/src`.
2. **Test Pyramid**: Full regression across all 90 tests spanning Phase 1 to Phase 4 (Unit, Integration, Security, Golden, Resilience).
3. **Frontend Build**: TypeScript typecheck and Vite minified production bundle.
4. **Credential Scanning**: Automated static scanning preventing hardcoded AWS keys, private keys, or GitHub tokens from entering git history.
