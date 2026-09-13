# SentinelOps AI — Project Structure

NeuralOps/
├── .env.example
├── docker-compose.yml
├── Makefile
├── LICENSE
├── pytest.ini
├── README.md
├── start.bat
├── start.sh
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   └── src/sentinelops/
│       ├── main.py                    # FastAPI application entrypoint
│       ├── config/settings.py         # Pydantic configuration
│       ├── core/                      # Database, Redis, logging infrastructure
│       ├── collectors/                # K8s Informer + Prometheus/Loki collectors
│       ├── events/                    # Event schemas and streams
│       ├── investigation/             # ReAct investigation engine & state machine
│       ├── tools/                     # 16 read-only diagnostic tools
│       ├── rag/                       # Vector RAG & SQLite embeddings store
│       ├── observability/             # Pod log shipping daemon & metric probes
│       ├── security/                  # RBAC, audit log, secret redactor
│       ├── services/                  # Incident, topology, and workload domain services
│       └── api/routes/                # Versioned REST and WebSocket endpoints
│
├── frontend/
│   ├── src/
│   │   ├── pages/                     # 13 verified operational screens
│   │   ├── components/                # Layout, DependencyGraph, modals, UI primitives
│   │   ├── contexts/                  # PlatformContext, SettingsContext
│   │   └── lib/api.ts                 # Strongly typed backend API client
│   ├── package.json
│   └── vite.config.ts
│
├── infra/
│   ├── prometheus/                    # Prometheus scrapers and alert rules
│   ├── loki/                          # Loki chunk configs
│   ├── docker/postgres/               # PostgreSQL schema migrations
│   └── kubernetes/                    # E2E workloads and cluster manifests
│
├── docs/
│   ├── ARCHITECTURE.md                # System and agent architecture
│   ├── DEMO.md                        # Deterministic 3-5 minute live demo guide
│   ├── INTERVIEW_GUIDE.md             # Technical QA & HCLTech competency guide
│   ├── RBAC_MATRIX.md                 # 3-tier authorization matrix
│   ├── RELEASE.md                     # Phase 14 verification & certification report
│   ├── SECURITY.md                    # Threat model & secret redaction
│   ├── TESTING.md                     # Pytest, Playwright & contract test suite
│   ├── UI_BACKEND_MAPPING.md          # 13 screens to 20 endpoints mapping
│   ├── assets/                        # High-resolution verified screenshots
│   └── history/                       # Historical development phase records
│
└── scripts/
    ├── final_verify.ps1               # Master 5-stage verification gate
    ├── start_local.ps1                # Local environment orchestrator
    ├── verify_real_environment.py     # Live infrastructure probe
    ├── verify_backend_contracts.py    # 20-endpoint contract test
    └── test_phase13_browser_certification.py

## Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| Redis streams | `so:<domain>:<type>` | `so:events:raw` |
| Consumer groups | `sentinelops-<role>` | `sentinelops-correlation` |
| API routes | `/api/v1/<resource>` | `/api/v1/incidents` |
| Agents | `<domain>_agent.py` | `cpu_agent.py` |
| Engines | `<function>_engine.py` | `correlation.py` |
| K8s labels | `app.kubernetes.io/part-of: sentinelops-ai` | namespace label |
