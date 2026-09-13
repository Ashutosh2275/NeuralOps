# SENTINELOPS AI — LIVE CAPABILITY MATRIX (PHASE 7)

| Subsystem | Component | Live Endpoint / Port | Status | Real Verification Method | Empirical Latency |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **1. Kubernetes** | k3s v1.31.5 control plane | `https://172.19.224.117:6443` | **LIVE** | Workloads in `sentinelops-e2e` namespace, pods/events listed | ~742ms |
| **2. LLM Engine** | Ollama (`llama3.2`) | `http://127.0.0.1:11434` | **LIVE** | GPU-accelerated tool call JSON generation via CUDA | ~469ms |
| **3. Vector Embeddings** | Ollama (`nomic-embed-text`) | `http://127.0.0.1:11434` | **LIVE** | Document ingestion & semantic cosine retrieval | ~469ms |
| **4. Database** | PostgreSQL 18 | `localhost:5433` | **LIVE** | 38 Alembic tables, AsyncSession commits & reconnects | ~150ms |
| **5. Message Broker** | Redis 5.0.14.1 | `localhost:6380` | **LIVE** | `XADD` / `XRANGE` stream events pipeline | ~20ms |
| **6. Observability Metrics** | Prometheus v3.14.0 | `http://127.0.0.1:9090` | **LIVE** | PromQL TSDB queries (`up`, `cpu_usage`) | ~412ms |
| **7. Observability Logs** | Loki v3.7.7 | `http://127.0.0.1:3100` | **LIVE** | Live chunk push via HTTP POST, query_range retrieval | ~151ms |
| **8. Vector Store** | ChromaDB Persistent Store | `data/vector_store` | **LIVE** | 4 operational runbook chunks indexed & queried | ~9ms |
| **9. Tool Framework** | Read-Only Tools (16 tools) | In-process Registry | **LIVE** | Multi-step autonomous plan execution with AST safety | ~1ms |
| **10. Operator CLI** | SentinelOps CLI (`doctor`) | Console CLI | **LIVE** | `sentinelops doctor` checking all 10 subsystems | ~3.8s |
| **11. Web Dashboard** | React + Vite + TypeScript | `http://localhost:3000` | **BUILD OK** | Clean TypeScript build, zero compilation errors | N/A (Build: 8.86s) |

---

## Controlled E2E Workload Verification Matrix

| Target Workload | Namespace | Condition | Restarts | Tools Executed | Confirmed Hypothesis | Confidence |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| `healthy-service` | `sentinelops-e2e` | Healthy Heartbeat | 0 | `get_pod_status` | No active failure detected | 0.95 |
| `crashloop-service` | `sentinelops-e2e` | NullPointerException Exit 1 | 5+ | `get_pod_status`, `get_pod_logs`, `get_k8s_events`, RAG | Application crash loop / configuration defect | 0.88 - 0.92 |
| `oom-service` | `sentinelops-e2e` | Cgroup Memory Saturation Exit 137 | 4+ | `get_pod_details`, `get_container_status`, `get_pod_logs`, `get_k8s_events`, `get_resource_usage` | Out of Memory (OOMKilled) container termination | 0.89 - 0.92 |
| `payment-db` -> `payment-service` -> `checkout-service` | `sentinelops-e2e` | Service scale-down to 0 | 0 | `get_service_dependencies`, `calculate_blast_radius` | Downstream blast radius propagation | 0.90 |
