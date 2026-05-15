# SentinelOps AI — Project Structure

```
NeuralOps/
├── .env.example
├── docker-compose.yml
├── Makefile
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/001_initial_schema.py
│   └── src/sentinelops/
│       ├── main.py                    # FastAPI entrypoint
│       ├── config/settings.py         # Pydantic settings
│       ├── core/                      # DB, Redis, logging
│       ├── events/schemas.py          # Event models
│       ├── streams/                   # Redis Streams bus
│       ├── models/                    # SQLAlchemy ORM
│       ├── collectors/                # K8s + Prometheus
│       ├── engines/                   # Correlation, RCA, Replay, Topology
│       ├── agents/                    # 7 AI agents + orchestrator
│       ├── services/                  # Business logic
│       ├── api/routes/                # REST endpoints
│       ├── websocket/hub.py           # Real-time broadcast
│       └── workers/runner.py          # Background consumers
│
├── frontend/
│   ├── src/
│   │   ├── pages/                     # Dashboard, Incidents, Topology, NLP, Replay
│   │   ├── components/                # Layout, DependencyGraph
│   │   ├── hooks/useWebSocket.ts
│   │   └── lib/api.ts
│   ├── package.json
│   └── vite.config.ts
│
├── schemas/events/v1/                 # JSON Schema contracts
│   ├── base_event.json
│   ├── pod_event.json
│   ├── metric_event.json
│   └── incident_event.json
│
├── infra/
│   ├── prometheus/
│   ├── loki/
│   ├── docker/postgres/
│   └── kubernetes/
│       ├── sentinelops/
│       ├── ecommerce-demo/
│       └── configmaps/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── MVP_BUILD_ORDER.md
│   └── PROJECT_STRUCTURE.md
│
└── scripts/
    └── fix_div_tags.py
```

## Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| Redis streams | `so:<domain>:<type>` | `so:events:raw` |
| Consumer groups | `sentinelops-<role>` | `sentinelops-correlation` |
| API routes | `/api/v1/<resource>` | `/api/v1/incidents` |
| Agents | `<domain>_agent.py` | `cpu_agent.py` |
| Engines | `<function>_engine.py` | `correlation.py` |
| K8s labels | `app.kubernetes.io/part-of: sentinelops-ai` | namespace label |
