# SentinelOps AI — Phase 11 Screen-by-Screen UI / Backend Audit

This document establishes the authoritative data-integrity and integration audit across all 10 primary operational views in SentinelOps AI. Each section details the frontend route, API dependencies, backend service architecture, persistence sources, RBAC controls, observed mismatches, required fixes, and verification tests.

---

## 1. Screen: Overview / Dashboard

- **SCREEN**: Operations Overview
- **ROUTE**: `/` (`frontend/src/pages/Dashboard.tsx`)
- **API**:
  - `GET /api/v1/health`
  - `GET /api/v1/incidents`
  - `GET /api/v1/workloads/overview`
  - `GET /api/v1/investigations`
- **BACKEND SERVICE**:
  - `HealthService` (`backend/src/sentinelops/api/routes/health.py`)
  - `IncidentService` (`backend/src/sentinelops/services/incident_service.py`)
  - `KubernetesCollector` (`backend/src/sentinelops/collectors/k8s_collector.py`)
  - `InvestigationService` (`backend/src/sentinelops/api/routes/investigations.py`)
- **DATABASE/STREAM SOURCE**:
  - PostgreSQL tables: `incidents`, `investigations`
  - Live Probes: PostgreSQL TCP socket, Redis TCP socket, Ollama HTTP, VectorStore Chroma SQLite, k3s API, Prometheus HTTP, Loki HTTP
- **ROLE REQUIREMENTS**:
  - `viewer`: Read-only view. "New Investigation" button disabled with tooltip.
  - `operator` / `admin`: Full operational view and permission to launch investigations.
- **EXPECTED DATA**:
  - 7/7 healthy subsystems with live latencies and timestamp.
  - Non-duplicated open incidents with accurate severity and lifecycle status.
  - Real workload KPI metrics (total pods, failing pods, total restarts) matching k3s namespace `sentinelops-e2e`.
- **CURRENT DATA / MISMATCH**:
  - `GET /api/v1/health` lacks a `timestamp` field, causing header/settings to display "Checked: N/A".
  - Repeated duplicate incidents in the incident feed with status stuck on `investigating`.
  - Fallback defaults (`?? 2`, `?? 79`) in workload stats if API returns undefined.
- **FIX REQUIRED**:
  - Add `timestamp` and latency metrics to `/api/v1/health`.
  - Implement incident deduplication and fingerprinting in `IncidentService`.
  - Ensure zero hardcoded fallback counts.
- **TEST REQUIRED**:
  - Verify `GET /api/v1/health` returns valid timestamp.
  - Validate that `Dashboard.tsx` displays exact live pod and restart counts.

---

## 2. Screen: Active Incidents

- **SCREEN**: Incidents Registry
- **ROUTE**: `/incidents` (`frontend/src/pages/Incidents.tsx`)
- **API**:
  - `GET /api/v1/incidents`
  - `POST /api/v1/incidents/{id}/acknowledge`
- **BACKEND SERVICE**:
  - `IncidentService` (`backend/src/sentinelops/services/incident_service.py`)
- **DATABASE/STREAM SOURCE**:
  - PostgreSQL table: `incidents`, `incident_timeline`
  - Redis Stream: `so:incidents`
- **ROLE REQUIREMENTS**:
  - `viewer`: Read-only listing and filtering.
  - `operator` / `admin`: Can acknowledge incidents (`POST /api/v1/incidents/{id}/acknowledge`).
- **EXPECTED DATA**:
  - Distinct operational incidents fingerprinted by `(cluster_id, namespace, root_service, failure_mode)`.
  - Valid lifecycle states: `open`, `investigating`, `acknowledged`, `resolved`.
- **CURRENT DATA / MISMATCH**:
  - Severe incident pollution: 14 duplicate entries of "Database connection pool exhaustion on payment-service".
  - Every single incident permanently stuck in `status: investigating` because `update_rca` blindly overwrote status without a completion or resolution transition.
- **FIX REQUIRED**:
  - Introduce fingerprint-based deduplication in `IncidentService.create_from_event()`.
  - Add `status: resolved` and `status: acknowledged` transitions.
  - Create safe cleanup script `scripts/reset_demo_state.ps1` to purge historical duplicate test pollution.
- **TEST REQUIRED**:
  - Query `/api/v1/incidents` after running multiple failure triggers to ensure deduplication prevents duplicate active rows.

---

## 3. Screen: Incident Forensics / Detail

- **SCREEN**: Incident Forensics & Root-Cause Analysis
- **ROUTE**: `/incidents/:id` (`frontend/src/pages/IncidentDetail.tsx`)
- **API**:
  - `GET /api/v1/incidents/{id}`
  - `GET /api/v1/incidents/{id}/replay`
  - `POST /api/v1/incidents/{id}/acknowledge`
- **BACKEND SERVICE**:
  - `IncidentService` (`backend/src/sentinelops/services/incident_service.py`)
  - `ReplayEngine` (`backend/src/sentinelops/engines/replay.py`)
  - `RCAService` (`backend/src/sentinelops/engines/rca.py`)
- **DATABASE/STREAM SOURCE**:
  - PostgreSQL tables: `incidents`, `incident_timeline`, `incident_events`
- **ROLE REQUIREMENTS**:
  - `viewer`: View forensics, timeline, blast radius, and recommendations.
  - `operator` / `admin`: Acknowledge incident and trigger remediation.
- **EXPECTED DATA**:
  - Meaningful, coherent root-cause statement (e.g., "Pod CrashLoopBackOff due to NullPointerException in TransactionRouter").
  - Mathematical confidence score (0.0 to 1.0) derived from evidence corroboration.
  - Epistemic separation: Observed Facts vs. AI Inferences vs. Uncertainties.
- **CURRENT DATA / MISMATCH**:
  - Malformed RCA text strings such as `"None=91.0 exceeded threshold on None"` generated by `rca.py:_describe_event` when metric payload keys were missing or mapped to alternative names.
- **FIX REQUIRED**:
  - Refactor `rca.py:_describe_event` to safely extract metric name, value, and target pod/service with fallback to meaningful domain descriptors.
- **TEST REQUIRED**:
  - Verify that no incident report or RCA description contains the substring `"None="` or `"on None"`.

---

## 4. Screen: Autonomous Investigations

- **SCREEN**: Autonomous AI Investigations
- **ROUTE**: `/investigations` (`frontend/src/pages/Investigations.tsx`)
- **API**:
  - `GET /api/v1/investigations`
  - `POST /api/v1/investigations/trigger`
  - `GET /api/v1/investigations/{id}`
- **BACKEND SERVICE**:
  - `InvestigationEngine` (`backend/src/sentinelops/investigation/engine.py`)
  - `InvestigationPlanner` (`backend/src/sentinelops/investigation/planner.py`)
  - `EvidenceCorrelator` (`backend/src/sentinelops/investigation/correlator.py`)
- **DATABASE/STREAM SOURCE**:
  - In-memory / PostgreSQL investigation session records.
- **ROLE REQUIREMENTS**:
  - `viewer`: Read-only inspection of past investigations, hypotheses, and tool call traces. "Launch Investigation" button disabled.
  - `operator` / `admin`: Interactive investigation launch enabled.
- **EXPECTED DATA**:
  - Precise state machine: `QUEUED`, `COLLECTING_EVIDENCE`, `CORRELATING`, `RETRIEVING_KNOWLEDGE`, `REASONING`, `COMPLETED`, `FAILED`.
  - Sequential execution trace of real tools called with exact parameters, duration, and status.
  - Dynamic tool count matching the active registry (16 tools).
- **CURRENT DATA / MISMATCH**:
  - Completed investigations occasionally display indeterminate progress if execution timestamp is stale.
  - Some UI badges reference generic "AI reasoning" steps rather than actual tool call outputs.
- **FIX REQUIRED**:
  - Enforce canonical backend lifecycle state in investigation serialization.
  - Ensure every step in the timeline corresponds strictly to a recorded `ToolCallRecord`.
- **TEST REQUIRED**:
  - Trigger investigation and assert that all returned steps have non-empty `tool_name`, valid `duration_ms`, and valid `status`.

---

## 5. Screen: Service Dependency Topology

- **SCREEN**: Dependency Topology & Blast Radius
- **ROUTE**: `/topology` (`frontend/src/pages/Topology.tsx`)
- **API**:
  - `GET /api/v1/topology/graph`
  - `GET /api/v1/topology/cascade/{namespace}/{pod}`
- **BACKEND SERVICE**:
  - `TopologyService` (`backend/src/sentinelops/services/topology_service.py`)
  - `DependencyIntelligenceEngine` (`backend/src/sentinelops/engines/dependency.py`)
- **DATABASE/STREAM SOURCE**:
  - NetworkX directed graph in `DependencyIntelligenceEngine`.
  - PostgreSQL tables: `topology_nodes`, `topology_edges`, `topology_snapshots`.
- **ROLE REQUIREMENTS**:
  - `viewer` / `operator` / `admin`: Full visibility into cluster dependency DAG and blast radius.
- **EXPECTED DATA**:
  - Directed acyclic graph showing consumer-to-dependency relationships:
    `checkout-service` → `payment-service` → `payment-db`.
  - Service-to-backing-pod relationships (`Service` routes_to `Pod`).
  - No self-referential loops (`A → A`).
- **CURRENT DATA / MISMATCH**:
  - Apparent self-dependency: `checkout-service → checkout-service` caused by pod-to-service routing edges being truncated in the UI to service names, and `k8s_collector.py` adding `depends_on` between a pod and its own service.
  - Lack of multi-tier service dependencies (`checkout-service` → `payment-service` → `payment-db`).
- **FIX REQUIRED**:
  - Fix edge generation in `k8s_collector.py` and `dependency.py`:
    - Pod backs Service (`routes_to`), never `depends_on` itself.
    - Explicitly forbid self-edges (`source == target`).
    - Infer inter-service dependencies from container environment variables and service ports.
  - Update `Topology.tsx` to render clean service-to-service architecture with progressive disclosure.
- **TEST REQUIRED**:
  - Validate `/api/v1/topology/graph` returns 0 self-edges and correctly routes `checkout-service` to `payment-service`.

---

## 6. Screen: Workloads Intelligence

- **SCREEN**: Workloads Intelligence
- **ROUTE**: `/workloads` (`frontend/src/pages/Workloads.tsx`)
- **API**:
  - `GET /api/v1/workloads/overview?namespace=sentinelops-e2e`
  - `GET /api/v1/workloads/pods?namespace=sentinelops-e2e`
  - `GET /api/v1/workloads/logs?pod_name={pod}&namespace=sentinelops-e2e`
  - `GET /api/v1/workloads/metrics?pod_name={pod}&namespace=sentinelops-e2e`
- **BACKEND SERVICE**:
  - `KubernetesCollector` (`backend/src/sentinelops/collectors/k8s_collector.py`)
  - `PrometheusCollector` (`backend/src/sentinelops/collectors/prometheus_collector.py`)
  - `LokiCollector` (`backend/src/sentinelops/collectors/loki_collector.py`)
- **DATABASE/STREAM SOURCE**:
  - Live k3s API (`/api/v1/namespaces/sentinelops-e2e/pods`)
  - Live Prometheus TSDB (`container_cpu_usage_seconds_total`, `container_memory_working_set_bytes`)
  - Live Loki Log Stream (`/var/log/pods`)
- **ROLE REQUIREMENTS**:
  - `viewer` / `operator` / `admin`: Full visibility into container state, logs, and telemetry.
- **EXPECTED DATA**:
  - Exact pod phases (`Running`, `CrashLoopBackOff`, `OOMKilled`, `Failed`).
  - Correct `ready` status (`true` / `false`) reflecting actual container readiness.
  - Real Prometheus memory and CPU metrics; if no metrics match, show "NO DATA" rather than 0 or simulated values.
  - Real Loki logs; if empty, show "No recent logs found".
- **CURRENT DATA / MISMATCH**:
  - Severe contradiction: `healthy-service` reported as `CRASH / OOM` in the table because `k8s_collector.py` did not set top-level `ready: bool`, causing `!pod.ready` to evaluate to true.
  - Prometheus collector returned synthetic `_demo_metrics` because `k8s-client.crt` certificates were out of sync.
- **FIX REQUIRED**:
  - Set top-level `ready` and `status_display` in `k8s_collector.py:_collect_pods_raw()`.
  - Distinguish between `CrashLoopBackOff`, `OOMKilled`, `Running`, and `NotReady`.
  - Synchronize Prometheus scraping certs with k3s to serve live cAdvisor metrics.
- **TEST REQUIRED**:
  - Verify `healthy-service` is marked `RUNNING` with `1/1 Ready` and 0 restarts.
  - Verify `crashloop-service` is marked `CRASHLOOPBACKOFF` with `0/1 Ready`.

---

## 7. Screen: Operational Knowledge / RAG

- **SCREEN**: Knowledge Base & Runbooks
- **ROUTE**: `/knowledge` (`frontend/src/pages/Knowledge.tsx`)
- **API**:
  - `GET /api/v1/knowledge/documents`
  - `POST /api/v1/knowledge/search`
- **BACKEND SERVICE**:
  - `RAGEngine` (`backend/src/sentinelops/rag/engine.py`)
  - `PersistentVectorStore` (`backend/src/sentinelops/rag/vector_store.py`)
- **DATABASE/STREAM SOURCE**:
  - SQLite vector store (`data/rag_store/vectors.db`)
  - Ollama `nomic-embed-text` embeddings (768-dim)
- **ROLE REQUIREMENTS**:
  - `viewer` / `operator` / `admin`: Read and search runbook repository.
- **EXPECTED DATA**:
  - Canonical set of 7 distinct operational runbooks (CrashLoopBackOff, OOMKilled, PVC Saturation, Dependency Outage, Healthy Workload, Architecture, Post-Mortem).
  - Deterministic document IDs without random UUID duplicate proliferation.
  - Semantic search returning cosine similarity scores (0.0 to 1.0) and exact chunk citations.
- **CURRENT DATA / MISMATCH**:
  - 9 duplicate "Auth Runbook" documents in `vectors.db` due to automated test executions appending randomized IDs (`runbook-auth-memory-leak-{uuid4()}`).
- **FIX REQUIRED**:
  - Clean `data/rag_store/vectors.db` to remove accidental test artifacts.
  - Make test ingestion deterministic with automatic teardown/cleanup.
- **TEST REQUIRED**:
  - Query `GET /api/v1/knowledge/documents` and assert `documents` list contains 0 duplicates.

---

## 8. Screen: Diagnostic Tools Sandbox

- **SCREEN**: Diagnostic Tool Registry
- **ROUTE**: `/tools` (`frontend/src/pages/Tools.tsx`)
- **API**:
  - `GET /api/v1/investigations/tools`
  - `POST /api/v1/investigations/tools/execute`
- **BACKEND SERVICE**:
  - `ToolRegistry` (`backend/src/sentinelops/tools/base.py`)
- **DATABASE/STREAM SOURCE**:
  - Tool decorators and metadata schemas in Python runtime.
- **ROLE REQUIREMENTS**:
  - `viewer`: Read-only view of tool catalog. "Run Tool" button disabled with permission tooltip.
  - `operator` / `admin`: Can execute tools (`POST /api/v1/investigations/tools/execute`).
- **EXPECTED DATA**:
  - Dynamic tool count derived directly from backend registry (exactly 16 tools across `k8s`, `observability`, `topology`, `incidents`, `rag`).
  - Read-only safety badge on all tools.
  - Form inputs matching JSON Schema parameters.
- **CURRENT DATA / MISMATCH**:
  - Backend has 16 tools, UI dynamically loads 16, but static documentation previously cited 14 tools.
- **FIX REQUIRED**:
  - Align all documentation and frontend headers to dynamic count: `tools.length`.
- **TEST REQUIRED**:
  - Assert `GET /api/v1/investigations/tools` returns `count: 16`.

---

## 9. Screen: Security & Governance Audit

- **SCREEN**: Audit Trail & Governance
- **ROUTE**: `/audit` (`frontend/src/pages/Audit.tsx`)
- **API**:
  - `GET /api/v1/system/audit`
- **BACKEND SERVICE**:
  - `AuditTrail` (`backend/src/sentinelops/security/audit.py`)
- **DATABASE/STREAM SOURCE**:
  - Append-only JSONL log (`data/audit/audit_trail.jsonl`).
- **ROLE REQUIREMENTS**:
  - `viewer` / `operator`: View audit trail.
  - `admin`: Full audit inspection and data retention cleanup.
- **EXPECTED DATA**:
  - Immutable audit events recording `actor`, `role`, `action`, `resource`, `status`, and `timestamp`.
  - Roles accurately reflect the actor who initiated the event (`admin`, `operator`, or `system`).
- **CURRENT DATA / MISMATCH**:
  - All audit records rendered `role: "viewer"` because `AuditEvent` had a hardcoded default `role: str = "viewer"`.
- **FIX REQUIRED**:
  - Update `AuditEvent` to capture the caller's actual authenticated role from the request context, or default to `"system"` when internally triggered.
- **TEST REQUIRED**:
  - Execute a tool as `operator` and verify audit log records `role: "operator"`.

---

## 10. Screen: System Settings & Governance

- **SCREEN**: Platform Configuration & System Health
- **ROUTE**: `/settings` (`frontend/src/pages/SystemSettings.tsx`)
- **API**:
  - `GET /api/v1/system/info`
  - `GET /api/v1/health`
  - `POST /api/v1/system/retention/cleanup`
- **BACKEND SERVICE**:
  - `SystemService` (`backend/src/sentinelops/api/routes/system.py`)
  - `HealthService` (`backend/src/sentinelops/api/routes/health.py`)
  - `RetentionManager` (`backend/src/sentinelops/security/retention.py`)
- **DATABASE/STREAM SOURCE**:
  - Runtime environment configuration, Pydantic settings, active k8s client.
- **ROLE REQUIREMENTS**:
  - `viewer`: Read-only settings. Retention cleanup hidden or disabled.
  - `operator`: Read-only settings. Retention cleanup restricted.
  - `admin`: Full administrative control; Data Retention & Purge Policy Management panel enabled.
- **EXPECTED DATA**:
  - Target namespace: `sentinelops-e2e` (matching active Kubernetes cluster).
  - Last health check timestamp rendered as formatted time (e.g., `2:41:48 PM`), not `N/A`.
  - Data Retention Dry-Run and Purge execution returning structured record counts.
- **CURRENT DATA / MISMATCH**:
  - Backend setting `k8s_namespace` defaulted to `"default"` instead of `"sentinelops-e2e"`.
  - `Checked: N/A` rendered because `/api/v1/health` omitted `timestamp`.
- **FIX REQUIRED**:
  - Set `k8s_namespace: str = "sentinelops-e2e"` in `settings.py` and `.env`.
  - Return `timestamp` in `health.py`.
- **TEST REQUIRED**:
  - Query `/api/v1/system/info` and assert `platform.namespace == "sentinelops-e2e"`.
  - Assert `/settings` displays valid timestamp.
