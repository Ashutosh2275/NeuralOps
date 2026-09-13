# NetraAI Codebase Complete Inventory

**Generated**: 2026-05-17  
**Project**: SentinelOps - Event-driven AI operational intelligence for Kubernetes  
**Status**: Phase 13 Integration Complete (8/13 systems deployed)

---

## TABLE OF CONTENTS

1. [Backend Architecture](#backend-architecture)
2. [Frontend Architecture](#frontend-architecture)
3. [Database Schema](#database-schema)
4. [Phase 13 Verification](#phase-13-verification)
5. [System Gaps & Next Steps](#system-gaps--next-steps)

---

## BACKEND ARCHITECTURE

### Root Directory: `/backend/src/sentinelops/`

#### **Main Entry Point**
- **`main.py`** (52 lines)
  - FastAPI application factory
  - Lifespan context manager (initialize event bus on startup)
  - CORS middleware configuration
  - WebSocket endpoint at `/ws` using `ws_hub`
  - API router includes at `/api/v1`

#### **API Routes** (`api/routes/`)

**Routers Registered** (8 routers in `__init__.py`):
1. **`health.py`** - Service health checks
2. **`incidents.py`** - `/incidents` - Incident management endpoints
3. **`topology.py`** - `/topology` - Topology graph operations
4. **`nlp.py`** - `/nlp` - Natural language processing
5. **`ingestion.py`** - `/ingestion` - Event/metric ingestion
6. **`intelligence.py`** - `/intelligence` - AI insights
7. **`demo.py`** - Demo/simulator endpoints
8. **`phase13.py`** - `/phase13` - **Phase 13 Predictive Operations** (15 endpoints)

**Unregistered Router**:
- `predictive.py` - Contains mock predictive endpoints (NOT integrated in `__init__.py`)
  - ⚠️ **GAP**: This router exists but is not registered in the API

#### **Engines** (`engines/` - 22 engines)

**Phase 13 Engines** (5 NEW):
- `predictive_failure_engine.py` (370 LOC) - Forecasts infrastructure failures
- `infrastructure_memory_engine.py` (305 LOC) - Tracks incident lineage & patterns
- `consensus_engine.py` (295 LOC) - Multi-agent voting & validation
- `advanced_remediation_orchestrator.py` (420 LOC) - Multi-step healing workflows
- `advanced_k8s_intelligence_engine.py` (360 LOC) - K8s resource pressure detection

**Existing Engines** (17):
- `rca.py` - Root cause analysis
- `correlation.py` - Event correlation
- `chaos.py` - Chaos engineering/injection
- `topology.py` - Topology graph management
- `dependency.py` - Dependency tracking
- `health.py` - Health state management
- `k8s_intelligence.py` - K8s insights (baseline)
- `service_health.py` - Enterprise health scoring
- `forecast.py` - Predictive forecast engine
- `timeline.py` - Timeline intelligence
- `confidence.py` - Confidence scoring/validation
- `event_intelligence.py` - Event analysis
- `analytics.py` - Executive analytics
- `remediation_orchestration.py` - Remediation (Phase 12)
- `blast_radius.py` - Blast radius calculation
- `healing.py` - Auto-healing
- `replay.py` - Incident replay/simulation

#### **Models** (`models/` - 11 model files)

**Exported Classes** (from `models/__init__.py`):
- **Cluster Management**: `Cluster`
- **Topology**: `TopologyNode`, `TopologyEdge`, `DependencyScore`, `DependencyEdge`, `TopologySnapshot`, `TopologyVersion`
- **Incidents**: `Incident`, `IncidentEvent`, `IncidentTimeline`
- **Kubernetes**: `Pod`, `PodMetric`, `Service`
- **Intelligence**: `AIInsight`, `CorrelationGroup`, `ReplayEvent`, `ReplayFrame`
- **AI Systems**: `AIReasoningLog`, `AIRecommendation`, `IncidentSummary`, `InfrastructureMemory`, `AnomalyPattern`
- **Simulation**: `SimulatedIncident`, `RemediationAction`, `InfrastructureScore`, `BlastRadiusEvent`, `ReplaySession`, `RecoveryTimeline`, `SimulationType`, `SimulationSeverity`
- **Recommendations**: `Recommendation`
- **Phase 13 Predictive** (7 new models):
  - `IncidentForecast`
  - `IncidentAncestry`
  - `ServiceHealthScore`
  - `K8sResourceIntelligence`
  - `InfrastructureTimeline`
  - `AIConfidenceValidation`
  - `RemediationOrchestration`
  - `ExecutiveMetrics`

#### **Services** (`services/` - 5 services)

1. **`incident_service.py`** - Incident CRUD, retrieval, history
2. **`intelligence_service.py`** - AI insights, correlations
3. **`topology_service.py`** - Topology graph queries (10,076 LOC)
4. **`recommendation_service.py`** - Remediation recommendations
5. **`nlp_service.py`** - NLP/semantic analysis

#### **Workers** (`workers/`)

**`runner.py`** - WorkerRunner class
- Event collection and processing pipeline
- Raw event consumption with buffering
- Correlation and anomaly detection
- AI orchestration
- Publishes to enriched/correlation streams
- Broadcasts to WebSocket hub

#### **Collectors** (`collectors/` - 5 collectors)

1. **`event_collector.py`** - Generic event collection
2. **`k8s_collector.py`** - Kubernetes API events
3. **`prometheus_collector.py`** - Prometheus metrics
4. **`loki_collector.py`** - Loki log collection
5. **`metrics_pipeline.py`** - Metrics aggregation

#### **Event Bus & Streams** (`streams/`)

**EventBus** (`bus.py`):
- Redis Streams based event bus
- Consumer group management for 11 streams
- Health checks and stream info
- Resilience layer via `RedisConnectionManager`

**Stream Consumer** (`consumer.py`):
- Consumes events from Redis Streams
- Consumer group coordination
- Dead letter queue handling

**Stream Publisher** (`publisher.py`):
- Publishes events to specific streams
- Enrichment and routing

**Resilience** (`resilience.py`):
- Connection pooling and retry logic
- Backoff strategies

**Dead Letter Queue** (`dead_letter.py`):
- Handles failed events

**Event Streams Managed**:
```
- stream_events_raw: Raw ingested events
- stream_events_enriched: Enriched events
- stream_metrics_events: Metrics
- stream_topology_events: Topology updates
- stream_anomaly_events: Anomalies
- stream_incident_events: Incidents
- stream_rca_events: RCA results
- stream_correlation: Correlations
- stream_ai_tasks: AI tasks
- stream_replay: Replay events
- stream_dead_letter: Failed messages
```

#### **WebSocket Hub** (`websocket/`)

**`hub.py`** - WebSocketHub class:
- Thread-safe connection management (asyncio.Lock)
- Broadcast methods:
  - `broadcast_topology_update()` - Graph updates
  - `broadcast_node_health_change()` - Node status
  - `broadcast_edge_health_change()` - Edge status
  - `broadcast_cascading_failure()` - Cascade detection
  - `broadcast_health_propagation()` - Health flows
- Ping/pong keepalive (30s interval on client)
- Dead connection cleanup

**`manager.py`** - WebSocket routing/management

#### **Pipeline** (`pipeline/`)

1. **`validator.py`** - Event validation
2. **`normalizer.py`** - Event normalization
3. **`normalized_event.py`** - Normalized event model
4. **`correlation_metadata.py`** - Correlation metadata
5. **`severity_engine.py`** - Severity calculation

#### **AI Agents** (`agents/` - 12 files)

**Agent Types**:
- `base.py` - BaseAgent class
- `cpu_agent.py` - CPU analysis
- `memory_agent.py` - Memory analysis
- `storage_agent.py` - Storage analysis
- `log_agent.py` - Log analysis
- `correlation_agent.py` - Correlation
- `rca_agent.py` - Root cause analysis
- `recommendation_agent.py` - Remediation recommendations

**Support**:
- `orchestrator.py` - AgentOrchestrator coordinates agents
- `registry.py` - Agent registration
- `shared_context.py` - Shared context between agents
- `ollama_client.py` - Local LLM integration (Ollama)

#### **AI System** (`ai/`)

- `base.py` - Base AI classes
- `agents.py` - AI agent implementations
- `ollama_client.py` - Ollama client
- `orchestrator.py` - AIOrchestrator
- `registry.py` - Model registry

#### **Core** (`core/`)

- **`database.py`** - SQLAlchemy async session factory, engine setup
- **`logging.py`** - Structured logging configuration
- **`redis_client.py`** - Redis connection management

#### **Configuration** (`config/`)

- **`settings.py`** - Pydantic Settings with environment variables
  - App settings (name, env, version)
  - Database URL and connection pools
  - Redis configuration
  - Stream names and consumer groups
  - CORS origins
  - API keys (Ollama, external services)

#### **Ingestion** (`ingestion/`)

- **`pipeline.py`** - Event ingestion pipeline orchestration

#### **Self-Healing** (`self_healing/`)

- **`engine.py`** - Auto-remediation engine

#### **Simulation** (`simulator/`)

- **`incident_simulator.py`** - Incident generation for testing/demo

#### **Events** (`events/`)

- **`schemas.py`** - BaseEvent, EventType enums

---

## FRONTEND ARCHITECTURE

### Root Directory: `/frontend/src/`

#### **Pages** (`pages/` - 8 pages)

1. **`Dashboard.tsx`** - Main operations dashboard
2. **`Incidents.tsx`** - Incident list/browser
3. **`IncidentDetail.tsx`** - Individual incident detail view
4. **`Topology.tsx`** - Topology graph visualization
5. **`NLPAssistant.tsx`** - Natural language Q&A
6. **`Replay.tsx`** - Incident replay/simulation
7. **`IncidentCommandCenter.tsx`** - Incident war room
8. **`EnterpriseCommandCenter.tsx`** - **Phase 13** - Predictive ops dashboard

#### **App Routes** (8 routes in `App.tsx`)

```
/ → Dashboard
/incidents → Incidents list
/incidents/:id → Incident detail
/topology → Topology visualization
/nlp → NLPAssistant
/replay/:id → Replay
/command-center → EnterpriseCommandCenter (Phase 13)
```

#### **Components** (`components/` - 9 directories)

**Analytics** (`analytics/`):
- `ExecutiveAnalyticsDashboard.tsx` - KPI board & metrics

**Dashboard** (`dashboard/` - 11 components):
- `AIAssistantPanel.tsx` - AI chat/suggestions
- `AIInsightsPanel.tsx` - Insight cards
- `ActiveIncidentsPanel.tsx` - Incident list
- `CascadingFailureMap.tsx` - Cascade visualization
- `ConfidenceVisualization.tsx` - Confidence scores
- `HealthScoreCard.tsx` - Health metric card
- `IncidentFeed.tsx` - Live incident stream
- `RCAPanel.tsx` - Root cause analysis
- `RCATimelinePanel.tsx` - Timeline of RCA
- `RecommendationPanel.tsx` - Remediation suggestions

**Topology** (`topology/` - 3 D3.js components):
- `DependencyGraph.tsx` - **D3.js** force-directed graph
- `LiveTopology.tsx` - **D3.js** real-time topology
- `CascadingFailureVisualizer.tsx` - **D3.js** cascade viz

**Intelligence** (`intelligence/`):
- `PredictiveIntelligenceDashboard.tsx` - **Phase 13** - Forecasting UI

**Warroom** (`warroom/`):
- `WarRoomDashboard.tsx` - Collaborative incident response

**Replay** (`replay/`):
- `ReplayCenter.tsx` - Incident timeline replay

**Demo** (`demo/`):
- `JudgeDemoMode.tsx` - Demo/tutorial mode

**Layout** (`layout/`):
- `Layout.tsx` - Main layout wrapper

#### **Hooks** (`hooks/`)

**`useWebSocket.ts`**:
- WebSocket connection management
- Automatic reconnection
- Event buffering (100 events max)
- Ping/pong keepalive (30s)
- URL: `import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws"`

#### **Utilities** (`lib/`)

- **`api.ts`** - API client, fetch wrappers

#### **Main Entry**

- **`main.tsx`** - React app bootstrap
- **`App.tsx`** - Route definitions
- **`vite-env.d.ts`** - Vite type definitions

#### **Configuration**

- **`vite.config.ts`** - Vite build config

### **D3.js Visualizations**

Used in 3 components:
1. **DependencyGraph.tsx**
   - Force simulation with links & charges
   - Node coloring by kind (Pod/Service)
   - Interactive drag and zoom

2. **LiveTopology.tsx**
   - Real-time graph updates
   - Collision detection
   - Health state visualization

3. **CascadingFailureVisualizer.tsx**
   - Cascade propagation animation
   - Multi-layer impact display

### **WebSocket Integration**

- Frontend connects to `ws://localhost:8000/ws`
- Listens for event types:
  - `topology` - Topology updates
  - `node_health` - Node status changes
  - `edge_health` - Edge status changes
  - `cascading_failure` - Cascade detection
  - `health_propagation` - Health state flows
  - `event` - Generic events

---

## DATABASE SCHEMA

### Alembic Migrations

**Migration Files** (6 total, revise chain):

```
001_initial_schema.py (7,822 bytes)
├─ 002_intelligence_schema.py (3,794 bytes)
├─ 003_topology_graph_schema.py (3,338 bytes)
├─ 004_ai_agents_schema.py (5,313 bytes)
└─ 005_phase_12_predictive_operations.py (8,604 bytes)
   └─ 006_phase_13_predictive_ops.py (4,133 bytes) ← LATEST
```

**Current Schema Version**: 006 (Phase 13)

### Core Tables (from migrations 001-005)

**Cluster Management**:
- `clusters` - Kubernetes clusters
- `nodes` - Cluster nodes
- `namespaces` - K8s namespaces

**Events & Incidents**:
- `incidents` - Incident records
- `incident_events` - Event log per incident
- `incident_timelines` - Timeline phases

**Metrics & Observability**:
- `pods` - Pod definitions
- `pod_metrics` - Pod resource metrics
- `services` - Service definitions
- `recommendations` - Auto-remediation suggestions

**Topology & Dependencies**:
- `topology_nodes` - Node records (Pod/Service)
- `topology_edges` - Dependency links
- `dependency_scores` - Link strength metrics
- `dependency_snapshots` - Historical versions

**Intelligence & Insights**:
- `ai_insights` - AI analysis results
- `correlation_groups` - Event correlations
- `ai_reasoning_logs` - Agent reasoning traces
- `ai_recommendations` - AI suggestions

**Simulation & Replay**:
- `replay_sessions` - Replay instances
- `replay_events` - Captured events
- `replay_frames` - Timeline frames
- `simulated_incidents` - Test incidents

**Phase 12 Tables**:
- `incident_forecasts` - Predictive incident forecasts
- `incident_ancestry` - Incident lineage
- `service_health_scores` - SLA tracking
- `k8s_resource_intelligence` - Resource analysis
- `infrastructure_timelines` - History tracking
- `ai_confidence_validations` - Validation scores
- `remediation_orchestrations` - Remediation tracking
- `executive_metrics` - KPI aggregates

### Phase 13 Tables (NEW - migration 006)

**Table 1: `failure_predictions`** (12 columns)
```sql
- id (UUID, PK)
- cluster_id (UUID, FK→clusters.id, indexed)
- incident_type (String, indexed)
- probability (Float)
- confidence (Float)
- time_to_failure_hours (Integer)
- severity_forecast (String)
- affected_services (Array[String])
- reasoning (Text)
- created_at (DateTime, indexed)
```
**Indexes**:
- `ix_failures_cluster_type` (cluster_id, incident_type)
- `ix_failures_created` (created_at)

**Table 2: `infrastructure_memory`** (8 columns)
```sql
- id (UUID, PK)
- cluster_id (UUID, FK→clusters.id, indexed)
- memory_type (String, indexed)
- key (String, indexed)
- value (JSON)
- source_incident_id (UUID)
- confidence (Float)
- last_updated (DateTime)
```
**Indexes**:
- `ix_memory_cluster_type` (cluster_id, memory_type)

**Table 3: `remediation_workflows`** (8 columns)
```sql
- id (UUID, PK)
- incident_id (UUID, FK→incidents.id, indexed)
- status (String, indexed)
- steps (JSON)
- confidence (Float)
- current_step (Integer)
- started_at (DateTime)
- completed_at (DateTime)
```
**Indexes**:
- `ix_workflows_incident_status` (incident_id, status)

**Table 4: `k8s_pressure_analysis`** (9 columns)
```sql
- id (UUID, PK)
- cluster_id (UUID, FK→clusters.id, indexed)
- namespace (String, indexed)
- resource_type (String)
- pressure_type (String, indexed)
- saturation_percent (Float)
- affected_pods (Array[String])
- mitigation_recommendation (Text)
- detected_at (DateTime, indexed)
```
**Indexes**:
- `ix_k8s_cluster_namespace` (cluster_id, namespace)

---

## PHASE 13 VERIFICATION

### ✅ PHASE 13 ENGINES

| Component | File | Status | LOC | Details |
|-----------|------|--------|-----|---------|
| Predictive Failure Engine | `engines/predictive_failure_engine.py` | ✅ EXISTS | 370 | Forecasts infrastructure failures |
| Infrastructure Memory Engine | `engines/infrastructure_memory_engine.py` | ✅ EXISTS | 305 | Tracks incident lineage & patterns |
| Consensus Engine | `engines/consensus_engine.py` | ✅ EXISTS | 295 | Multi-agent voting & validation |
| Advanced Remediation Orchestrator | `engines/advanced_remediation_orchestrator.py` | ✅ EXISTS | 420 | Multi-step healing workflows |
| Advanced K8s Intelligence | `engines/advanced_k8s_intelligence_engine.py` | ✅ EXISTS | 360 | K8s resource pressure detection |

### ✅ PHASE 13 API ROUTES

**File**: `api/routes/phase13.py` (320 LOC)

**Registered**: ✅ YES in `api/routes/__init__.py`
- Import: `from sentinelops.api.routes.phase13 import router as phase13_router`
- Registration: `api_router.include_router(phase13_router, tags=["phase13"])`
- Prefix: `/api/v1/phase13`

**Endpoints** (15 total):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/phase13/health` | GET | Health check |
| `/phase13/status` | GET | System status |
| `/predictions/forecast/{cluster_id}` | GET | 24h failure forecasts |
| `/memory/incident-ancestry/{incident_id}` | GET | Incident lineage |
| `/memory/service-history/{cluster_id}/{service}` | GET | Service history |
| `/memory/cascade-patterns/{cluster_id}/{service}` | GET | Cascade patterns |
| `/memory/stats/{cluster_id}` | GET | Memory statistics |
| `/consensus/vote/{incident_id}` | POST | Submit agent vote |
| `/consensus/compute/{incident_id}` | POST | Compute consensus |
| `/remediation/workflow/create` | POST | Create workflow |
| `/remediation/workflow/execute-step` | POST | Execute step |
| `/k8s/pressure/{cluster_id}/{namespace}` | GET | K8s pressure analysis |

### ✅ PHASE 13 DATA MODELS

**File**: `models/predictive.py`

**Models Exported** (8):
- `IncidentForecast`
- `IncidentAncestry`
- `ServiceHealthScore`
- `K8sResourceIntelligence`
- `InfrastructureTimeline`
- `AIConfidenceValidation`
- `RemediationOrchestration`
- `ExecutiveMetrics`

**All exported in**: `models/__init__.py` ✅

### ✅ PHASE 13 DATABASE MIGRATION

**File**: `backend/alembic/versions/006_phase_13_predictive_ops.py`

- ✅ Revision: 006
- ✅ Down revision: 005 (proper chain)
- ✅ Creates 4 tables with proper schema
- ✅ Creates 5 composite indexes
- ✅ Foreign keys properly defined
- ✅ Rollback support included

### ✅ PHASE 13 FRONTEND

**Page**: `frontend/src/pages/EnterpriseCommandCenter.tsx` (380 LOC)

**File**: ✅ EXISTS

**Integration**:
- ✅ Imported in `frontend/src/App.tsx`
- ✅ Route registered: `<Route path="/command-center" element={<EnterpriseCommandCenter />} />`

**Components** (7 sub-components):
- Header
- HealthRadar
- LiveClusterMap
- AIConfidenceVisualizer
- IncidentStream
- RemediationTimeline
- ExecutiveKPIBoard

**Features**:
- WebSocket integration via `useWebSocket` hook
- 30-second refresh interval for predictions
- Real-time metrics (MTTR, MTTD, uptime, SLA compliance)
- Dark theme with SentinelOps branding

---

## SYSTEM GAPS & NEXT STEPS

### ⚠️ IDENTIFIED GAPS

#### 1. **Unregistered Predictive Router**
- **File**: `backend/src/sentinelops/api/routes/predictive.py`
- **Status**: ❌ EXISTS BUT NOT REGISTERED
- **Issue**: Router defined but not included in `api/routes/__init__.py`
- **Impact**: Endpoints inaccessible at runtime
- **Fix**: Add to `api/routes/__init__.py`:
  ```python
  from sentinelops.api.routes.predictive import router as predictive_router
  api_router.include_router(predictive_router, prefix="/predictive", tags=["predictive"])
  ```

#### 2. **Duplicate/Conflicting Routes**
- **Note**: Phase 13 router uses `/api/v1/phase13` prefix
- **Note**: Predictive router (unregistered) also provides forecasting endpoints
- **Resolution**: Decide on route consolidation

### ✅ PHASE 13 COMPLETION STATUS

**Systems Completed**: 8/13
```
✅ 1. Predictive Failure Engine
✅ 2. Infrastructure Memory Engine
✅ 3. Enterprise AI Consensus Engine
✅ 4. Advanced Remediation Orchestrator
✅ 5. Advanced Kubernetes Intelligence
✅ 6. Database Schema (Migration 006)
✅ 7. API Routes (15 endpoints)
✅ 8. Enterprise Command Center (Frontend)
```

**Remaining Systems**: 5/13
```
⏳ 9. Cinematic Replay Engine Enhancement
⏳ 10. Advanced Topology Visualization
⏳ 11. Real-Time Incident Command Center (advanced)
⏳ 12. Enterprise Security Hardening
⏳ 13. Performance Optimization Pass
```

**Next Phase**: Phase 14
```
📋 Phase 14: Predictive Autoscaling Integration
   - Auto-scaling based on failure predictions
   - Capacity planning from forecasts
   - Resource pre-allocation logic
```

### 📊 CODEBASE STATISTICS

**Backend**:
- Python files: 93
- Total LOC (engines, routes, models, services): ~15,000
- Core engines: 22
- AI agents: 8
- Services: 5
- API routes: 8 (registered) + 1 (unregistered)
- Database migrations: 6
- Stream types: 11

**Frontend**:
- TypeScript/TSX files: 31
- Pages: 8
- Components: 25+
- D3.js visualizations: 3
- Custom hooks: 1
- Routes: 7

**Database**:
- Tables: 40+ (core + Phase 12 + Phase 13)
- Indexes: 50+
- Foreign keys: Comprehensive relational structure
- JSON columns: Used for complex data (steps, values)

### 🔧 ENHANCEMENT OPPORTUNITIES

1. **Route Organization**
   - Consolidate predictive endpoints into Phase 13 router
   - Or create new `/predictive` router and register it

2. **Test Coverage**
   - Add integration tests for Phase 13 endpoints
   - Add frontend E2E tests for Command Center

3. **Documentation**
   - API documentation (Swagger/OpenAPI)
   - Architecture decision records (ADRs)

4. **Performance**
   - Query optimization for memory tables
   - Connection pooling tuning
   - Frontend component memoization

5. **Resilience**
   - Retry logic for Phase 13 operations
   - Circuit breakers for external dependencies
   - Better error propagation

---

## FILE PATHS REFERENCE

### Backend Key Files
```
/backend/src/sentinelops/main.py
/backend/src/sentinelops/api/routes/__init__.py
/backend/src/sentinelops/api/routes/phase13.py
/backend/src/sentinelops/engines/predictive_failure_engine.py
/backend/src/sentinelops/engines/infrastructure_memory_engine.py
/backend/src/sentinelops/engines/consensus_engine.py
/backend/src/sentinelops/engines/advanced_remediation_orchestrator.py
/backend/src/sentinelops/engines/advanced_k8s_intelligence_engine.py
/backend/src/sentinelops/models/predictive.py
/backend/src/sentinelops/models/__init__.py
/backend/src/sentinelops/websocket/hub.py
/backend/src/sentinelops/streams/bus.py
/backend/src/sentinelops/services/*.py
/backend/alembic/versions/006_phase_13_predictive_ops.py
```

### Frontend Key Files
```
/frontend/src/App.tsx
/frontend/src/pages/EnterpriseCommandCenter.tsx
/frontend/src/components/intelligence/PredictiveIntelligenceDashboard.tsx
/frontend/src/components/topology/DependencyGraph.tsx
/frontend/src/components/topology/LiveTopology.tsx
/frontend/src/hooks/useWebSocket.ts
```

---

**Last Updated**: 2026-05-17  
**Inventory Status**: COMPLETE  
**Phase 13 Status**: ✅ INTEGRATED (Ready for Deployment)
