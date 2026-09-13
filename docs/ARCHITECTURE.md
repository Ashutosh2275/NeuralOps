# SentinelOps AI — Complete Platform Architecture

## 1. System Overview
SentinelOps AI is an enterprise-scale, event-driven AI operational intelligence platform for Kubernetes environments. It unifies real-time event streaming, dynamic topology intelligence, persistent vector retrieval (RAG), autonomous read-only tool calling, and human-in-the-loop governance into a deterministic operational engine.

---

## 2. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph External Telemetry & Ingestion
        K8S[Kubernetes Cluster API]
        PROM[Prometheus Metrics]
        LOKI[Loki Log Aggregator]
        EVENTS[Event Stream Ingestion]
    end

    subgraph Core Processing Pipeline
        NORM[Event Normalizer]
        CORR[Incident Correlator]
        TOPO[NetworkX Topology Engine]
        REDIS[(Redis Streams Pipeline)]
        DB[(PostgreSQL / SQLite)]
    end

    subgraph Autonomous Investigation Engine
        PLANNER[Autonomous Planner / LLM]
        REGISTRY[Tool Registry: 16 Read-Only Tools]
        CORRELATOR[Evidence Correlator & Refuter]
        RCA[Deterministic RCA Engine]
        VEC[(Persistent Vector Store RAG)]
    end

    subgraph Security & Governance Layer
        AUTH[RBAC: Viewer / Operator / Admin]
        SAN[Prompt Injection Sanitizer]
        RED[Centralized Secret Redactor]
        AUDIT[(Structured Audit Trail)]
        APPROVAL[Human Approval Workflow]
    end

    subgraph Presentation & Client Interfaces
        REST[FastAPI REST Engine]
        CLI[Terminal CLI: sentinelops]
        DASH[Vite + React Dashboard]
    end

    K8S --> NORM
    PROM --> NORM
    LOKI --> NORM
    EVENTS --> NORM
    NORM --> REDIS
    REDIS --> CORR
    CORR --> TOPO
    CORR --> DB

    REST --> AUTH
    AUTH --> PLANNER
    PLANNER --> REGISTRY
    REGISTRY --> K8S
    REGISTRY --> PROM
    REGISTRY --> LOKI
    REGISTRY --> TOPO
    REGISTRY --> VEC
    REGISTRY --> RED
    RED --> CORRELATOR
    CORRELATOR --> RCA
    RCA --> AUDIT
    RCA --> APPROVAL
    APPROVAL --> REST

    REST --> DASH
    CLI --> REST
```

---

## 3. Core Component Subsystems

### 3.1 Autonomous Tool Calling Framework
- 16 registered operational tools spanning Kubernetes inspection, Prometheus metrics, Loki logs, topology impact, past incidents, and RAG knowledge.
- In Phase 4, **all tools remain strictly `READ_ONLY`**. Mutating write actions are prohibited.

### 3.2 Evidence Correlation & Deterministic RCA
- Correlates multi-source telemetry items into cohesive investigation evidence.
- Epistemic refutation: Healthy live states (`Running`, `ready=True`, `restarts=0`) actively refute stale alert triggers.
- Grounded citations link every root-cause claim directly to specific evidence items.

### 3.3 Security & Governance Architecture
- Deterministic RBAC with VIEWER, OPERATOR, and ADMIN roles.
- Human approval governance for operational actions with strict Phase 4 execution blocking.
- Centralized secret redactor sanitizing AWS keys, JWTs, Bearer tokens, DB credentials, and private keys.
- Durable, append-oriented audit logging with automated data retention policies.

### 3.4 Evaluation & Benchmarking Suite
- 20 golden operational scenarios covering standard and adversarial failure modes.
- Epistemic classification into `FACT`, `INFERENCE`, and `UNCERTAINTY`.
- 10,000+ synthetic logical asset scale validation with sub-millisecond graph traversals.
