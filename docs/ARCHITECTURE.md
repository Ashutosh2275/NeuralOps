# SentinelOps AI — System Architecture

## Service Boundaries

| Component | Responsibility | Input | Output |
|-----------|---------------|-------|--------|
| Event Collector | K8s watch + Prometheus scrape | Cluster API, PromQL | `so:events:raw` |
| Metrics Pipeline | Threshold breach detection | Prometheus | MetricEvent |
| Redis Event Bus | Durable async messaging | Stream XADD | Stream XREADGROUP |
| Correlation Engine | Time-window event grouping | Enriched events | CorrelationEvent |
| Dependency Engine | Graph construction | Labels, services, network | TopologySnapshot |
| RCA Engine | Deterministic root cause | Event batch | RCAResult |
| Agent Orchestrator | Parallel AI analysis | AgentContext | AgentResult[] |
| Replay Engine | Incident timeline playback | Buffered events | Replay frames |
| FastAPI API | REST + WebSocket | HTTP/WS | JSON |
| React Dashboard | Visualization | API/WS | UI |

## Event Flow

```
K8s API ──► EventCollector ──► so:events:raw
                                    │
Prometheus ──► MetricsPipeline ─────┤
                                    ▼
                            Worker (enrich)
                                    │
                                    ▼
                          so:events:enriched
                                    │
                                    ▼
                          CorrelationEngine
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            so:correlation    PostgreSQL      WebSocket
                    │               │
                    ▼               ▼
              RCAEngine      IncidentService
                    │
                    ▼
            AgentOrchestrator ──► Ollama
                    │
                    ▼
            Recommendations + Replay buffer
```

## Redis Streams Topology

| Stream | Producer | Consumer Group | Purpose |
|--------|----------|----------------|---------|
| `so:events:raw` | Collector | sentinelops-collector | Raw ingress |
| `so:events:enriched` | Worker | sentinelops-correlation | Normalized events |
| `so:metrics` | Metrics pipeline | sentinelops-collector | Metric snapshots |
| `so:correlation` | Correlation engine | sentinelops-correlation | Correlated groups |
| `so:incidents` | Incident service | sentinelops-ai | Incident lifecycle |
| `so:ai:tasks` | API/Worker | sentinelops-ai | Agent job queue |
| `so:ai:results` | Agents | sentinelops-ai | Agent outputs |
| `so:topology` | Dependency engine | sentinelops-collector | Graph updates |
| `so:replay` | Replay engine | sentinelops-replay | Playback frames |

## PostgreSQL Schema Strategy

- **Operational state**: clusters, pods, services, metrics (time-series samples)
- **Graph state**: dependency_edges, topology_snapshots (JSON graph blobs)
- **Incident state**: incidents, incident_timeline, incident_events, recommendations
- **Indexes**: namespace+name on pods/services, timestamp on metrics/timeline, status on incidents

## AI Agent Pipeline

1. Correlation triggers incident creation
2. RCA Engine produces deterministic baseline
3. Orchestrator fans out to specialized agents (CPU, Memory, Storage, Log, Correlation)
4. RCA Agent enriches with Ollama
5. Recommendation Agent produces prioritized kubectl actions

## Deployment Modes

| Mode | Use Case |
|------|----------|
| Docker Compose | Local dev, hackathon demo |
| Minikube | Full K8s integration test |
| In-cluster | Production-inspired edge deploy |
