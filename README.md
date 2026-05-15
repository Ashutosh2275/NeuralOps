# SentinelOps AI

**Event-driven AI operational intelligence for Kubernetes**

ABB Hackathon Theme 2 — Beyond Monitoring: AI Agents for Real-Time Pod Resource Discovery and Dependency Mapping.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ K8s Cluster │────▶│ Event        │────▶│ Redis Streams   │
│ + Prom/Loki │     │ Collector    │     │ Event Bus       │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
         ┌─────────────────────────────────────────┼──────────────────────────┐
         ▼                     ▼                    ▼                          ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐      ┌─────────────────┐
│ Correlation     │  │ Dependency   │  │ Multi-Agent AI   │      │ Replay +        │
│ Engine          │  │ Intelligence │  │ System (Ollama)  │      │ Topology Engine │
└────────┬────────┘  └──────┬───────┘  └────────┬─────────┘      └────────┬────────┘
         │                  │                   │                          │
         └──────────────────┴───────────────────┴──────────────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │ FastAPI + WS     │
                              │ PostgreSQL       │
                              └────────┬─────────┘
                                       ▼
                              ┌──────────────────┐
                              │ React Dashboard  │
                              └──────────────────┘
```

## Quick Start

```bash
# 1. Copy environment
cp .env.example .env

# 2. Start infrastructure (Postgres, Redis, Prometheus, Loki, Ollama)
docker compose up -d

# 3. Run migrations
make migrate

# 4. Start backend
make backend

# 5. Start workers
make workers

# 6. Start frontend
make frontend
```

## Minikube Deployment

```bash
make minikube-up
make minikube-deploy
```

See [docs/MVP_BUILD_ORDER.md](docs/MVP_BUILD_ORDER.md) for implementation sequence.

## License

MIT
