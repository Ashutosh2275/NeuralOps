# SentinelOps AI — MVP Build Order

## Phase 1: Foundation (Day 1) — BUILD FULLY

1. **Docker Compose stack** — Postgres, Redis, Prometheus, Loki
2. **PostgreSQL schema** — Alembic migration `001_initial_schema`
3. **Redis Streams bus** — Publisher, consumer, consumer groups
4. **FastAPI skeleton** — Health, CORS, lifespan, WebSocket hub
5. **Event schemas** — Pydantic models + JSON Schema in `schemas/events/v1/`
6. **Structured logging** — structlog JSON/console

**Demo checkpoint**: `curl localhost:8000/api/v1/health` returns healthy.

## Phase 2: Data Pipeline (Day 1-2) — BUILD FULLY

7. **Kubernetes Collector** — Pod watch with demo fallback
8. **Metrics Pipeline** — Prometheus queries with demo fallback
9. **Event Collector** — Orchestration + anomaly detection
10. **Worker runner** — Raw stream consumer, enrichment publish

**Demo checkpoint**: Events appear in Redis (`XLEN so:events:raw`).

## Phase 3: Intelligence Core (Day 2-3) — BUILD FULLY

11. **Correlation Engine** — Time-window grouping
12. **RCA Engine** — Deterministic scoring (no AI required)
13. **Incident Service** — CRUD + timeline
14. **Dependency Engine** — NetworkX graph + label discovery
15. **Topology snapshots** — Persist graph JSON

**Mock temporarily**: Network-based dependency discovery (use label selectors only).

## Phase 4: AI Layer (Day 3-4) — PARTIAL OK

16. **Ollama client** — Generate with fallback model
17. **CPU + Memory agents** — Threshold + AI enrichment
18. **RCA + Recommendation agents** — Ollama prompts
19. **Agent orchestrator** — Parallel execution with semaphore

**Mock temporarily**: Log agent Loki integration (pass sample logs in context).

**Skip for MVP**: qwen2.5 fine-tuning, multi-model routing.

## Phase 5: Frontend (Day 4-5) — BUILD FULLY

20. **Dashboard** — Health, incident list, event chart
21. **Incidents pages** — List + detail + cascade display
22. **Topology graph** — D3 force-directed layout
23. **NLP Assistant** — Query form + response
24. **Replay viewer** — Frame scrubber

**Mock temporarily**: Dashboard chart can use static data until live metrics flow.

## Phase 6: Demo Polish (Day 5-6)

25. **E-commerce demo namespace** — CrashLoop + CPU stress workloads
26. **Minikube deploy** — RBAC, configmaps, monitoring stack
27. **WebSocket live updates** — Incident + event broadcast
28. **Replay buffer** — Wire incident events to replay engine

---

## Safest Build Order (Dependencies)

```
Postgres + Redis → Event Schemas → Streams Bus → Collectors
     → Correlation → RCA → Incidents DB → API
     → Ollama → Agents → Frontend
     → Topology → Replay → K8s Deploy
```

## Highest-Risk Components

| Component | Risk | Mitigation |
|-----------|------|------------|
| Ollama GPU inference | Model load OOM on 4GB VRAM | Use llama3.2 3B, CPU fallback profile |
| K8s in-cluster auth | RBAC misconfiguration | Demo fallback data in collector |
| Prometheus scraping | Minikube networking | Demo metrics in MetricsPipeline |
| Redis stream lag | Consumer backlog | `MAXLEN ~` trimming, batch ack |
| D3 topology at scale | Performance >100 nodes | Limit graph to affected namespace |

## What to Build NOW vs LATER

### NOW (MVP/demo)
- Event collector with demo data
- Correlation + RCA + incident creation
- 3 AI agents (CPU, RCA, Recommendation)
- Dashboard + incidents + topology
- Docker Compose one-command start

### LATER (post-hackathon)
- Full Loki log pipeline integration
- Network policy / service mesh edge discovery
- Multi-cluster federation
- Persistent replay from Postgres (not in-memory)
- Custom Prometheus exporter
- AuthN/AuthZ (OAuth2)

## Fastest Path to Live Demo (2 hours)

```bash
cp .env.example .env
docker compose up -d postgres redis
cd backend && pip install -e . && alembic upgrade head
uvicorn sentinelops.main:app --reload &
python -m sentinelops.workers.runner &
cd frontend && npm install && npm run dev
```

Trigger demo incident: inventory-service CrashLoopBackOff is auto-detected from demo pod data.

## What to Mock Temporarily

| Feature | Mock Strategy |
|---------|---------------|
| K8s API | `_demo_pods()` in KubernetesCollector |
| Prometheus | `_demo_metrics()` in MetricsPipeline |
| Loki logs | Hardcoded error strings in AgentContext |
| Network dependencies | Label selector edges only |
| Event throughput chart | Static chart data in Dashboard |

## What to Implement Fully (No Shortcuts)

- Redis Streams pub/sub with consumer groups
- PostgreSQL incident persistence
- Correlation window logic
- Deterministic RCA scoring
- WebSocket broadcast on events
- Alembic migrations
- Pydantic event validation
- Agent orchestrator concurrency control
