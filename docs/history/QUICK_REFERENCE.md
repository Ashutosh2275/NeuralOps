# NetraAI Quick Reference Guide

## QUICK NAVIGATION

### Backend - What Goes Where?

| Need | Location | Key File |
|------|----------|----------|
| Add new API endpoint | `/backend/src/sentinelops/api/routes/` | `*.py` router files |
| Add new database table | `/backend/alembic/versions/` | `00X_*.py` migration |
| Add new ORM model | `/backend/src/sentinelops/models/` | `*.py` model files |
| Process events | `/backend/src/sentinelops/workers/` | `runner.py` |
| Real-time features | `/backend/src/sentinelops/websocket/` | `hub.py` (broadcasting) |
| Data analysis logic | `/backend/src/sentinelops/engines/` | One engine per concern |
| Business logic | `/backend/src/sentinelops/services/` | `*_service.py` |
| AI reasoning | `/backend/src/sentinelops/agents/` | `*_agent.py` |
| Metrics collection | `/backend/src/sentinelops/collectors/` | `*_collector.py` |
| Configuration | `/backend/src/sentinelops/config/` | `settings.py` |

### Frontend - What Goes Where?

| Need | Location | Key File |
|------|----------|----------|
| Add new page/view | `/frontend/src/pages/` | `*.tsx` page component |
| Add new route | `/frontend/src/App.tsx` | Routes definition |
| Reusable UI component | `/frontend/src/components/` | Organized by domain |
| API calls | `/frontend/src/lib/` | `api.ts` utilities |
| WebSocket listener | `/frontend/src/hooks/` | `useWebSocket.ts` |
| Real-time updates | Via `useWebSocket()` | Listen in components |
| D3.js viz | `/frontend/src/components/topology/` | Force graphs |

### Database - What's New?

**Phase 13 Tables** (4 new):
1. `failure_predictions` - Forecasted incidents
2. `infrastructure_memory` - Incident lineage & patterns
3. `remediation_workflows` - Multi-step healing tracking
4. `k8s_pressure_analysis` - Resource pressure detection

### Running the System

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head  # Run migrations
uvicorn sentinelops.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Both together
docker-compose up

# Workers (separate process)
python -m sentinelops.workers.runner
```

### Key Architectural Patterns

**Event Processing Flow**:
```
Collectors
  ↓
raw_events stream
  ↓
WorkerRunner (validates/normalizes)
  ↓
enriched_events stream
  ↓
Services (incident_service, etc.)
  ↓
WebSocket Hub (broadcasts to frontend)
```

**Engine Pattern**:
```python
# All engines follow this pattern:
class SomeEngine:
    async def analyze(self, data):
        # Process data
        return result

some_engine = SomeEngine()  # Singleton
```

**API Route Pattern**:
```python
# routes/some_feature.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/some-feature", tags=["feature"])

@router.get("/endpoint")
async def endpoint(session: AsyncSession = Depends(get_session)):
    return {"result": "data"}

# In routes/__init__.py
from sentinelops.api.routes.some_feature import router as some_feature_router
api_router.include_router(some_feature_router)
```

## PHASE 13 AT A GLANCE

### Engines (5 new)
- **Predictive Failure**: 24h failure forecasting
- **Infrastructure Memory**: Incident history & patterns
- **Consensus**: Multi-agent voting (no hallucinations)
- **Remediation Orchestrator**: Multi-step healing workflows
- **K8s Intelligence**: Resource pressure detection

### Frontend
- **Command Center**: Real-time predictive ops dashboard at `/command-center`
- **Features**: KPI board, health radar, live cluster map, incident stream

### API
- **15 endpoints** under `/api/v1/phase13/`
- **Health checks**, **predictions**, **memory**, **consensus**, **remediation**, **K8s analysis**

### Database
- **4 new tables** with 5 composite indexes
- **Migration 006** (revises 005)

## CRITICAL GAPS FOUND

### 🔴 Unregistered Predictive Router
**File**: `backend/src/sentinelops/api/routes/predictive.py`  
**Problem**: Exists but not included in `api/routes/__init__.py`  
**Fix**:
```python
# In backend/src/sentinelops/api/routes/__init__.py
from sentinelops.api.routes.predictive import router as predictive_router

# Then add to api_router:
api_router.include_router(predictive_router, prefix="/predictive", tags=["predictive"])
```

## CHECKLIST FOR NEXT PHASE (Phase 14)

- [ ] Decide on predictive router consolidation
- [ ] Add Phase 14 migration (007_phase_14_autoscaling.py)
- [ ] Implement autoscaling based on predictions
- [ ] Add capacity planning logic
- [ ] Add resource pre-allocation engine
- [ ] Test all Phase 13 endpoints
- [ ] Test Command Center UI
- [ ] Load test the system
- [ ] Deploy to production

## TESTING COMMANDS

```bash
# Test Phase 13 health
curl http://localhost:8000/api/v1/phase13/phase13/health

# Test forecasting
curl http://localhost:8000/api/v1/phase13/predictions/forecast/00000000-0000-0000-0000-000000000000

# Test K8s analysis
curl http://localhost:8000/api/v1/phase13/k8s/pressure/00000000-0000-0000-0000-000000000000/default

# Test memory
curl http://localhost:8000/api/v1/phase13/memory/stats/00000000-0000-0000-0000-000000000000

# Frontend Command Center
Open: http://localhost:5173/command-center
```

## COMMON TASKS

### Adding a new engine

1. Create: `/backend/src/sentinelops/engines/my_engine.py`
2. Define class with async methods
3. Create singleton instance at module level
4. Use in routes/services

### Adding a new API endpoint

1. Create/edit: `/backend/src/sentinelops/api/routes/my_feature.py`
2. Define router and endpoints
3. Add to `/backend/src/sentinelops/api/routes/__init__.py`
4. Test with curl/Postman

### Adding a new frontend page

1. Create: `/frontend/src/pages/MyPage.tsx`
2. Add route in `App.tsx`
3. Add navigation link in `Layout.tsx`
4. Import WebSocket via `useWebSocket()` if needed

### Adding a database table

1. Create migration: `/backend/alembic/versions/00X_description.py`
2. Define in `upgrade()` function
3. Add ORM model in `/backend/src/sentinelops/models/`
4. Export in `models/__init__.py`
5. Run: `alembic upgrade head`

---

Generated: 2026-05-17
