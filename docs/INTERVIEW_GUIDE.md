# SentinelOps AI — Engineering Architecture & Technical Interview Guide

This guide provides technically grounded answers to architectural, systems engineering, and operational questions regarding SentinelOps AI. It is designed for technical interviewers, SRE leads, cloud architects, and portfolio reviewers.

---

## 1. Architectural & Technology Rationale

### Q1: Why Kubernetes?
Kubernetes is the standard orchestration runtime for distributed microservices. Its declarative API exposes structured operational state: Pod phases, Container restart counts, Termination exit codes (`OOMKilled`, `137`, `1`), readiness probe failures, and controller `BackOff` events. SentinelOps utilizes the Kubernetes Informer/Watch pattern to intercept failures the exact moment the cluster detects them, rather than relying on delayed polling.

### Q2: Why Redis Streams?
- **Append-Only Event Log**: Redis Streams (`XADD`, `XREADGROUP`, `XACK`) provide persistent, ordered event streams with consumer group offsets. Multiple asynchronous workers (correlation engine, investigation scheduler) process cluster events independently without dropped messages.
- **Sub-Millisecond Ingestion**: Delivers microsecond event propagation with negligible memory overhead compared to Apache Kafka, making it ideal for local, sovereign, and edge operations.
- **Deterministic Replay**: Stream IDs are timestamp-based, enabling precise incident timeline reconstruction and replay.

### Q3: Why PostgreSQL?
PostgreSQL 18 serves as the relational source of truth for persistent entity lifecycles: incidents, root-cause deductions, remediation proposals, and immutable governance audit trails across 38 relational tables with foreign-key constraints and ACID transaction guarantees.

### Q4: Why Prometheus?
Prometheus provides dimensional time series metrics via PromQL. During investigations, the autonomous agent queries container memory limits (`container_memory_working_set_bytes`), CPU throttling, and network traffic to detect resource starvation and latency spikes.

### Q5: Why Grafana Loki?
Loki provides label-indexed container log aggregation without the massive index bloat of Elasticsearch. SentinelOps's `PodLogShipper` daemon tails `/var/log/pods` and pushes structured streams to Loki, enabling targeted LogQL queries (`{namespace="sentinelops-e2e", app="crashloop-service"}`) to extract exact container crash stack traces.

### Q6: Why Retrieval-Augmented Generation (RAG)?
LLMs have fixed training cutoffs and lack organizational context. RAG grounds LLM reasoning in verified standard operating procedures (SOPs), service architecture documents, and historical post-mortems. When an incident occurs, relevant runbook chunks are dynamically retrieved and injected into the prompt context, guaranteeing that recommendations follow organizational standards.

### Q7: Why Vector Embeddings (`nomic-embed-text`)?
Keywords fail when logs and runbooks use disparate terminology (e.g., "memory limit exceeded" vs. "OOMKilled" or "bind port conflict" vs. "port 8080 already in use"). Vector embeddings project operational text into a continuous 768-dimensional space where semantically related operational concepts cluster together regardless of exact phrasing.

### Q8: Why SQLite for Vector Storage?
Standalone vector databases (Pinecone, Milvus, Qdrant) introduce heavy operational complexity and external dependencies. SQLite with cosine distance computation (`data/rag_store/vectors.db`) provides an embedded, zero-maintenance vector store suitable for air-gapped, sovereign, and edge clusters while enabling relational metadata queries.

### Q9: Why Local Ollama Inference (`llama3.2`)?
- **Zero Data Egress & Sovereignty**: Production Kubernetes telemetry, pod environment variables, and stack traces frequently contain proprietary service names, internal IPs, and sensitive data. Local inference guarantees that no data ever leaves the cluster boundary.
- **No Token Costs or API Throttling**: Complex investigations execute dozens of tool steps; local GPU-accelerated inference (CUDA) avoids cloud API rate limits and recurring token billing.

### Q10: Why LLM Tool Calling?
Passive LLMs hallucinate when asked to describe live infrastructure. By equipping the model with a typed registry of 16 read-only diagnostic tools (`get_pod_details`, `get_pod_logs`, `query_prometheus_metric`, `get_k8s_events`), the agent operates as an active investigator: formulating a diagnostic hypothesis, executing a tool, observing factual output, and updating its deductions.

### Q11: Why Use an Agent Instead of a Simple LLM Call?
A single LLM call requires stuffing all possible cluster telemetry into a single prompt up front. In a live incident, logs can be millions of lines and metric time-series have thousands of points, overwhelming the context window and inducing hallucinations. An **autonomous agent** uses dynamic, closed-loop decision making:
- It inspects the initial symptom (e.g. `CrashLoopBackOff`).
- It decides *which specific tool* to call next (e.g. `get_pod_details` to check container exit code).
- Based on that observation (e.g. exit code 1), it decides whether to fetch logs or query memory metrics.
- It stops calling tools once sufficient evidence has proven or refuted the hypothesis.
This reduces LLM context token usage by >85% and produces deterministic, auditable investigative steps.

---

## 2. Investigation Engine & Accuracy

### Q12: How Does the Investigation Engine Work?
The investigation engine implements an autonomous ReAct (Reason + Act) loop:
1. **Trigger**: An incident is dispatched with target service and symptom.
2. **Hypothesis Generation**: The engine proposes diagnostic hypotheses.
3. **Sequential Tool Execution**: Invokes read-only diagnostic tools via the tool registry.
4. **Evidence Collection**: Normalizes tool outputs into structured evidence records.
5. **RAG Retrieval**: Retrieves relevant operational runbooks via vector cosine similarity.
6. **RCA Synthesis**: Synthesizes verified evidence into a final root-cause conclusion with confidence scoring.

### Q13: How Does SentinelOps Avoid Unsupported Claims & Hallucinations?
1. **Tool-Grounded Invariant**: Hypotheses are only accepted if substantiated by tool output.
2. **Epistemic Separation**: Findings are strictly divided into *Observed Facts* (raw cluster strings), *AI Inferences* (causal deductions), and *Uncertainties* (confidence bounds).
3. **Structured JSON Schemas**: Outputs must conform to rigid Pydantic schemas with type and range constraints.
4. **Deterministic Sanity Filters**: Deductions are cross-checked against live Kubernetes status before display.

### Q14: How Are Facts Separated from Inference?
The platform enforces a 3-way epistemic breakdown:
- **Observed Facts**: Raw, verifiable cluster telemetry (e.g. exit code 137, log line `unable to bind port 8080`, BackOff restart count 5).
- **AI Inferences**: Deductive causal links formed by the LLM (e.g. port bind failure caused process termination).
- **Uncertainties**: Disclaimers and unverified possibilities (e.g. transient network latency).

### Q15: How Does the Confidence Score Work?
Confidence is computed using a weighted multi-factor heuristic:
$$\text{Confidence} = 0.35 \cdot C_{\text{logs}} + 0.30 \cdot C_{\text{events}} + 0.20 \cdot C_{\text{rag}} + 0.15 \cdot C_{\text{metrics}}$$
- Direct error match in logs: **+0.35**
- Kubernetes event correlation (e.g. BackOff, exit code 137): **+0.30**
- Relevant RAG runbook match ($\text{similarity} > 0.80$): **+0.20**
- Prometheus metric anomaly verified: **+0.15**

### Q16: How Is Tool Selection Performed?
Tool selection uses an LLM planner guided by missing epistemic evidence:
1. **Context State Analysis**: The planner receives the list of available tools with JSON schemas, the current incident symptom, and the chronological history of already executed tools and outputs.
2. **Duplicate Prevention**: If the model suggests a tool that was already called with identical arguments (e.g. `get_pod_details`), the agent automatically intercepts the redundant call, records a `duplicate_prevented` event, and prompts the planner to gather alternative evidence (e.g. logs or metrics).
3. **Termination Condition**: Once an actionable hypothesis is substantiated (e.g. container status `OOMKilled` with exit code 137, corroborated by Prometheus memory saturation), the planner terminates the loop instead of executing redundant diagnostic calls.

### Q17: How Are Diagnostic Tools Validated and Secured?
1. **Schema Validation**: Every tool argument is validated against Pydantic models before dispatch. Malformed arguments trigger validation errors rather than unexpected exceptions.
2. **Read-Only Enclave Invariant**: The tool registry is strictly read-only. No tools exist that can delete pods, drain nodes, or alter Kubernetes deployments.
3. **Secret Redaction**: Tool outputs (especially raw stdout/stderr logs and pod environment descriptions) pass through `SecretRedactor` to strip passwords, JWT tokens, and private keys before being stored or presented to the LLM.

### Q18: How Does the Dependency Graph and Blast Radius Calculation Work?
1. **NetworkX Directed Graph**: SentinelOps maintains an in-memory directed acyclic graph (DAG) representing caller-to-callee dependencies between services (e.g. `frontend` -> `checkout-service` -> `payment-service` -> `payment-db`).
2. **Blast Radius Traversal**: When an incident affects a service (e.g. `payment-service`), the engine traverses the reverse edges of the graph to find all upstream caller services directly or transitively impacted (`checkout-service`, `frontend`).
3. **Impact Metric**: The blast radius score is calculated as $\frac{\text{impacted services}}{\text{total services in topology}}$, providing SREs with an instant quantitative measure of customer-facing risk.

---

## 3. Security, Governance & Enterprise Operations

### Q19: How Does Role-Based Access Control (RBAC) Work?
SentinelOps enforces a strict 3-tier authorization model:
- **Viewer**: Read-only inspection across all dashboards, telemetry, and topology.
- **Operator**: Operational triage: acknowledge/resolve incidents, launch autonomous investigations, execute diagnostic tools.
- **Admin**: Administrative governance: execute data retention cleanup, configure system overrides.
Authorization is enforced authoritatively at the FastAPI route dependency layer (`require_operator`, `require_admin`), returning `HTTP 403 Forbidden` on unauthorized attempts. The frontend reactively disables unauthorized buttons and displays tooltips explaining restrictions.

### Q20: How Is Prompt Injection & Secret Leakage Prevented?
1. **Input Sanitization**: User-supplied input strings in investigation prompts pass through an input sanitizer that strips prompt override delimiters (`IGNORE PREVIOUS INSTRUCTIONS`, `SYSTEM PROMPT:`, markdown code block jailbreaks).
2. **Schema Enforcement**: The model cannot return free-form text commands. Its output is forced into strict Pydantic JSON schemas with enumerations and regex bounds.
3. **Outbound Secret Scrubbing**: All logs, telemetry, and pod specs pass through `SecretRedactor` before LLM processing and database persistence, masking AWS keys, GitHub tokens, Bearer JWTs, and private keys.
4. **Read-Only Containment**: Even if an attacker somehow injected malicious instructions, the agent possesses no write or destructive tools; it cannot delete, restart, or mutate cluster resources.

### Q21: How Are Failures Handled (Resilience)?
- **Subsystem Degradation**: If Prometheus or Loki are unreachable, collectors return explicit `UNAVAILABLE` states rather than failing or displaying misleading zeroes.
- **Rule-Based Fallback**: If Ollama is offline, the investigation engine falls back to deterministic rule-based heuristic root-cause analysis based on exit codes and event reasons.
- **DB Connection Pooling**: Async connection pooling with auto-reconnect handles transient database disruptions.

### Q22: What Would Change in a Multi-Cluster Cloud Deployment?
1. **Collector Architecture**: Deploy lightweight DaemonSets / OpenTelemetry agents per cluster that ship events to a centralized Kafka or managed Redis cluster.
2. **Federated Topology**: Graph representations would partition by cluster and VPC, resolving cross-cluster service-mesh (Istio/Linkerd) endpoints.
3. **High-Throughput Model Serving**: Replace single-instance Ollama with an autoscaled vLLM or Triton Inference Server pool on AWS EKS or GCP GKE with continuous batching.
4. **Centralized Identity**: Replace local role headers with OpenID Connect (OIDC) JWT tokens issued by Okta or Azure AD, mapped to Kubernetes RBAC groups.

### Q23: What Are the System's Current Limitations?
- **Single-Cluster Evaluation**: Live validation is currently executed against a local k3s single-cluster environment (`sentinelops-e2e`).
- **Read-Only Diagnostic Scope**: Does not autonomously mutate production cluster state; remediation requires human operator approval and execution.
- **Deterministic Runbook Dependence**: RAG accuracy relies on curated operational runbooks for specific failure types (CrashLoop, OOM, Dependency Failure); novel failure modes rely on generalized heuristic reasoning.

---

## 4. Technical Competency Matrix (HCLTech Portfolio Alignment)

| Technical Domain | How Demonstrated in SentinelOps AI |
| :--- | :--- |
| **Python** | Modern async Python 3.11+, typed Pydantic models, async/await concurrency, custom decorators. |
| **FastAPI** | Clean REST API routing, OpenAPI docs, WebSocket live streaming, dependency injection security. |
| **SQL / PostgreSQL** | PostgreSQL 18, SQLAlchemy 2 async ORM, Alembic migrations, foreign-key cascade integrity. |
| **Redis** | Redis 5 Streams (`XADD`, `XREADGROUP`, `XACK`), consumer groups, pub/sub websocket fanout. |
| **Kubernetes** | Informer Watch APIs, CoreV1/AppsV1 resource collectors, pod lifecycle management, k3s cluster. |
| **Prometheus** | PromQL metric queries, time-series anomaly detection, cAdvisor container telemetry. |
| **Loki** | LogQL query ranges, structured stream ingestion, container log parsing. |
| **RAG & Embeddings** | 768-dim `nomic-embed-text` embeddings, SQLite vector store, cosine similarity ranking. |
| **LLM & Tool Calling** | Local `llama3.2` inference via Ollama, autonomous ReAct loop, 16 read-only diagnostic tools. |
| **Security & Governance** | 3-tier RBAC (`Viewer`/`Operator`/`Admin`), regex secret redaction, immutable audit logging. |
| **Testing & QA** | 123 Pytest unit/integration tests, Playwright browser E2E crawl, cross-screen consistency suites. |
| **Frontend Engineering** | React 18, TypeScript 5, Vite 5, TailwindCSS, D3.js force-directed topology graphs. |
