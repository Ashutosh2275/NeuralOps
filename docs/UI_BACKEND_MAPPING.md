# SentinelOps AI — UI to Backend Data & Contract Mapping

This document provides a strict, field-by-field and screen-by-screen architectural mapping between the SentinelOps AI React frontend components and the real backend services, FastAPI endpoints, database schemas, and telemetry collectors.

---

## 1. Global Shell & Navigation Header

| UI Component / Element | Displayed Label / Data | Backend Endpoint / Source | Underlying Data Source / Service |
| :--- | :--- | :--- | :--- |
| `Layout.tsx` (Logo/Title) | SentinelOps AI &bull; Autonomous Operations | Static Platform Identity | Platform Configuration |
| `Layout.tsx` (Cluster Badge) | `sentinelops-e2e` | `/api/v1/system/info` &bull; `platform.cluster_id` | Core Kubernetes Cluster (`k3s`) |
| `Layout.tsx` (Environment Badge) | `local-k3s` | `/api/v1/system/info` &bull; `platform.environment` | Environment Config (`Settings.app_env`) |
| `Layout.tsx` (System Health Dot) | Green "Healthy" (7/7) | `/api/v1/health` &bull; `healthy_count` / `total_dependencies` | Real Health Probes: k8s, prom, loki, pg, redis, ollama, vector_store |
| `Layout.tsx` (Health Drawer) | Individual subsystem status | `/api/v1/health` &bull; `dependencies[key]` | Individual socket/ping/HTTP checks |
| `Layout.tsx` (WebSocket Stream) | `CONNECTED` / `DISCONNECTED` | `ws://127.0.0.1:8000/ws/events` | FastAPI WebSocket Hub (`ws_hub`) |
| `Layout.tsx` (Role Switcher) | Viewer / Operator / Admin | `/api/v1/system/session` | Client Auth State & HTTP Session Header |

---

## 2. Operations Overview (`/` — `Dashboard.tsx`)

| UI Section | Displayed Field / Table | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Header** | Timestamp, Cluster, Active Scope | Local Time + `/api/v1/system/info` | Live Client Clock & Backend Settings |
| **System Health** | 7-service horizontal status row | `/api/v1/health` | Redis, Postgres, K8s, Prom, Loki, Ollama, Vector DB |
| **Active Incidents** | Severity, Status, Title, Service, Started, Confidence | `/api/v1/incidents` | PostgreSQL `incidents` table via `IncidentService.list_open()` |
| **Active Investigations** | Target, Question, State, Steps, Confidence, Open CTA | `/api/v1/investigations` | Redis `sentinelops:investigations:*` + JSON store |
| **Workload Health** | Total pods, Running, Failing, Restarts, Deployments | `/api/v1/workloads/overview` | Live K8s CoreV1 & AppsV1 API |
| **Recent Activity** | Timestamp, Actor, Action, Resource, Status badge | `/api/v1/investigations/audit/events` | Redis & SQLite `audit_events` |

---

## 3. Incident Center (`/incidents` — `Incidents.tsx`)

| UI Element / Filter | Field Mapped | Backend Endpoint | Behavior |
| :--- | :--- | :--- | :--- |
| **Severity Filter** | All, Critical, High, Medium, Low | `/api/v1/incidents` | Client-side reactive filter on `IncidentSummary.severity` |
| **Status Filter** | All, Open, Acknowledged, Investigating, Resolved | `/api/v1/incidents` | Client-side reactive filter on `IncidentSummary.status` |
| **Incident Table** | Severity Badge | `IncidentSummary.severity` | Rendered with enterprise color tokens |
| | Title & ID | `IncidentSummary.title`, `IncidentSummary.id` | Click navigates directly to `/incidents/:id` |
| | Root Service | `IncidentSummary.root_service` | Identifies failing microservice |
| | Started / Duration | `IncidentSummary.started_at` | Formatted relative duration from UTC ISO string |
| | AI Confidence | `IncidentSummary.confidence_score` | Formatted percentage badge (e.g., 94%) |
| | Action Button | Investigate / Review | Links to `/incidents/:id` |

---

## 4. Incident Detail (`/incidents/:id` — `IncidentDetail.tsx`)

| Section | UI Element | Backend Endpoint / Field | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Header** | Title, Severity, Lifecycle, Service, Duration | `GET /api/v1/incidents/{id}` | PostgreSQL `incidents` row |
| **Actions** | Investigate, Acknowledge, Resolve | `POST /api/v1/incidents/{id}/acknowledge`<br>`POST /api/v1/incidents/{id}/resolve` | Role-gated backend transition endpoints |
| **Section 1: RCA** | Persisted Root Cause & Confidence Score | `incident.root_cause`, `incident.confidence_score` | PostgreSQL `incidents.root_cause` & `confidence_score` |
| **Section 2: Evidence** | **Observed Facts** | `investigation.epistemic_breakdown.facts` | Direct K8s status, log snippets, pod errors |
| | **AI Inferences** | `investigation.epistemic_breakdown.inferences` | Autonomous deductive reasoning from engine |
| | **Uncertainties** | `investigation.epistemic_breakdown.uncertainties` | Epistemic limitations & confidence bounds |
| **Section 3: Timeline** | Step-by-step chronological audit trace | `incident.timeline` or `investigation.tool_history` | K8s Events, Alert timestamps, tool start/end |
| **Section 4: Tool Execution** | Tool name, arguments, duration, redacted output | `investigation.tool_history` | Tool registry execution logs with secret redaction |
| **Section 5: Blast Radius** | Root service, Upstream callers, Downstream deps | `GET /api/v1/intelligence/blast-radius/{ns}/{service}` | D3 Dependency graph walk in `dependency.py` |
| **Section 6: Recommendation** | Remediation title, type, justification, kubectl cmd | `GET /api/v1/intelligence/incidents/{id}/recommendations` | RCA recommendation engine (`recommendations` table) |
| **Section 7: Knowledge** | RAG Runbook citations, cosine similarity, excerpt | `investigation.citations` or `GET /api/v1/knowledge/search` | SQLite `data/rag_store/vectors.db` via `nomic-embed-text` |

---

## 5. Investigation Workspace (`/investigations` & `/investigations/:id` — `Investigations.tsx`)

| UI Pane | Displayed Field / Section | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Left Sidebar** | History list of investigations (target, status, date) | `GET /api/v1/investigations?limit=25` | Redis investigation index |
| **Trigger Form** | Service, Pod, Namespace, Trigger Reason, Max Steps | `POST /api/v1/investigations` | Role-gated autonomous investigation dispatcher |
| **Hypothesis Tab** | Working theory, status (confirmed/refuted), confidence | `investigation.hypotheses` | Autonomous investigation engine state machine |
| **Tool Trace Tab** | Sequential tool execution records with payloads | `investigation.tool_history` | Secret-redacted tool call execution store |
| **Evidence Tab** | Evidence grouped by K8s, Loki, Prometheus, Topology | `investigation.evidence` | Verified raw telemetry artifacts |
| **RAG Knowledge Tab** | Semantic queries, matched chunks, similarity | `investigation.rag_results` | Vector store embeddings cosine similarity |
| **RCA Tab** | Final root cause, blast radius summary, recommendation | `investigation.final_root_cause` | Epistemic consensus synthesis |

---

## 6. Dependency Topology (`/topology` — `Topology.tsx`)

| UI Element | Visualization / Inspector | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Graph Canvas** | D3 Interactive Force-Directed Graph | `GET /api/v1/topology/graph` | Real K8s service, pod, and deployment selectors |
| **Node Inspector** | Node name, kind, namespace, health status | `topology.nodes[id]` | Live K8s cluster status (`Running`, `CrashLoopBackOff`, etc.) |
| **Edge Inspector** | Source $\to$ Target, call dependency, confidence | `topology.edges` | cAdvisor / netstat / app service dependency model |
| **Blast Radius CTA** | Calculates downstream services if node fails | Node metadata & `/api/v1/intelligence/blast-radius` | Graph traversal engine |

---

## 7. Workload Intelligence (`/workloads` & `/workloads/:namespace/:pod` — `Workloads.tsx`)

| UI View | Displayed Information | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Main Table** | Pod name, Namespace, Phase, Ready, Restarts, CPU, Mem | `GET /api/v1/workloads/pods` | Live Kubernetes CoreV1 API |
| **Workload Detail** | Container image, restart policy, node, pod IP | `GET /api/v1/workloads/pods/{namespace}/{pod_name}` | Pod spec & status in live cluster |
| **Logs Tab** | Container stdout/stderr log stream | `GET /api/v1/workloads/logs?pod_name=...` | Grafana Loki log aggregator (`loki-local.yml`) |
| **Metrics Tab** | Container CPU & Memory usage charts | `GET /api/v1/workloads/metrics?pod_name=...` | Prometheus TSDB metrics queries (`up`, `container_cpu...`) |

---

## 8. Runbook & Knowledge Base (`/knowledge` & `/knowledge/:documentId` — `Knowledge.tsx`)

| UI Element | Functionality | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Corpus List** | Document title, category, chunk count, status | `GET /api/v1/knowledge/documents` | SQLite `vector_chunks` table in `data/rag_store/vectors.db` |
| **Semantic Search** | Vector search bar with cosine similarity scores | `POST /api/v1/knowledge/search` | Ollama `nomic-embed-text` embeddings + Cosine distance |
| **Document Viewer** | Complete Markdown runbook with indexed chunk list | `GET /api/v1/knowledge/documents/{documentId}` | Ordered chunks by `order_index` from vector store |

---

## 9. Diagnostic Capabilities (`/tools` — `Tools.tsx`)

| UI Element | Functionality | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Tool Registry** | 16 diagnostic tools categorized by domain | `GET /api/v1/investigations/tools` | In-memory `ToolRegistry` with Pydantic parameter schemas |
| **Tool Execution** | Parameter form, execute button (Operator/Admin) | `POST /api/v1/investigations/tools/{name}/execute` | Role-gated tool execution sandbox |
| **Output Console** | JSON response viewer with secret redaction | Execution response payload | Secret redactor filter (`[REDACTED]`) |

---

## 10. Governance & Audit Trail (`/audit` — `Audit.tsx`)

| UI Element | Displayed Information | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Audit Table** | Timestamp, Actor, Role, Action, Resource, Status | `GET /api/v1/investigations/audit/events` | Immutable security audit log (`audit_events`) |
| **Event Drawer** | Full request ID, client IP, sanitized arguments | Event payload metadata | Structured audit log records |

---

## 11. Platform Settings (`/settings` — `SystemSettings.tsx`)

| UI Section | Displayed Fields | Backend Endpoint | Source of Truth |
| :--- | :--- | :--- | :--- |
| **Environment** | Cluster ID, App Env, Version, Namespace | `GET /api/v1/system/info` &bull; `platform` | Backend Settings (`config/settings.py`) |
| **AI Runtime** | Provider, Model (`llama3.2`), Embeddings (`nomic-embed-text`) | `GET /api/v1/system/info` &bull; `ai_engine` | Ollama runtime configuration |
| **Data Retention** | Dry-run toggle, Scanned/Expired/Deleted summary | `POST /api/v1/investigations/retention/cleanup` | Role-gated retention manager (Admin only) |
