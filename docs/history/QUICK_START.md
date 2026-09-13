# SentinelOps AI System - Quick Start Reference

## Pre-Startup (One-Time)

```bash
# Verify Python 3.12+
python --version

# Navigate to project
cd /path/to/NetraAI

# Run database migrations
cd backend
alembic upgrade head
cd ..
```

## Full System Startup (Choose One)

### GPU-Accelerated Startup
```bash
docker-compose --profile gpu --profile app up -d

# Wait for Ollama models (2-5 minutes)
sleep 120
docker logs sentinelops-ollama | tail -20
```

### CPU-Only Startup
```bash
docker-compose --profile cpu --profile app up -d

# Wait for Ollama models (2-5 minutes)
sleep 120
docker logs sentinelops-ollama-cpu | tail -20
```

### Manual Step-by-Step
```bash
docker-compose up -d postgres redis prometheus loki promtail
sleep 10

# GPU or CPU Ollama
docker-compose --profile gpu up -d ollama
# OR
docker-compose --profile cpu up -d ollama-cpu

sleep 120
docker-compose --profile app up -d backend workers frontend

# Verify all services
docker-compose ps
```

## Service URLs

```
Frontend: http://localhost:5173
Backend: http://localhost:8000
Prometheus: http://localhost:9090
Loki: http://localhost:3100
Ollama: http://localhost:11434
PostgreSQL: localhost:5433
Redis: localhost:6380
```

## Quick Verification

```bash
# All services running
docker-compose ps

# Backend health
curl http://localhost:8000/health

# Ollama models loaded
curl -s http://localhost:11434/api/tags | jq '.models[].name'

# Frontend loads
curl -s http://localhost:5173 | head -20

# Database ready
docker exec sentinelops-postgres pg_isready -U sentinelops
```

## Test AI System

```bash
# Trigger incident
curl -X POST http://localhost:8000/api/v1/test/incident \
  -H "Content-Type: application/json" \
  -d '{"namespace":"default","event_type":"correlation","severity":"critical"}'

# Monitor AI execution (30 seconds)
docker logs -f sentinelops-workers 2>&1 | grep "ai_agent" | head -15

# View WebSocket events
websocat ws://localhost:8000/ws 2>&1 | jq '.type' | sort | uniq -c
```

## View Results

```bash
# AI insights in database
docker exec sentinelops-postgres psql -U sentinelops -d sentinelops -c \
  "SELECT agent_type, COUNT(*) FROM ai_insights GROUP BY agent_type;"

# Recommendations
docker exec sentinelops-postgres psql -U sentinelops -d sentinelops -c \
  "SELECT priority, COUNT(*) FROM ai_recommendations GROUP BY priority;"

# Worker logs
docker logs sentinelops-workers | tail -100

# Backend logs
docker logs sentinelops-backend | tail -50
```

## Shutdown

```bash
# Stop all services
docker-compose down

# Remove all volumes (WARNING: Deletes data)
docker-compose down -v

# Clean images
docker-compose down -v --rmi all
```

## Troubleshooting

```bash
# Ollama not ready
docker logs sentinelops-ollama-cpu | grep -i error

# AI agents failing
docker logs sentinelops-workers | grep "ai_agent_failed"

# Database connection issues
docker logs sentinelops-backend | grep -i "database\|connection"

# WebSocket events not received
docker logs sentinelops-backend | grep "broadcast"

# Frontend build issues
docker logs sentinelops-frontend | grep -i error
```

## Restart Services

```bash
# Restart specific service
docker-compose restart sentinelops-backend

# Rebuild and restart
docker-compose up -d --build sentinelops-backend

# Full restart
docker-compose down
docker-compose up -d --build
```

## Monitor Performance

```bash
# Resource usage
docker stats --no-stream

# Real-time resource monitoring
docker stats

# Container resource limits
docker inspect sentinelops-backend | jq '.HostConfig.Memory'
```

## Expected Timing

```
Startup:
├─ PostgreSQL: 30s
├─ Redis: 10s
├─ Prometheus: 20s
├─ Loki: 20s
├─ Ollama startup: 10s
├─ Model download: 120-300s (depends on connection)
├─ Backend startup: 30s
├─ Workers startup: 10s
└─ Frontend startup: 30s

Total: ~5-15 minutes

Incident Processing:
├─ Event detection: <1s
├─ Deterministic RCA: <100ms
├─ AI Orchestration: 2-5s
│  ├─ Stage 0 (6 parallel): 2-3s
│  ├─ Stage 1 (2 parallel): 1-2s
│  ├─ Stage 2 (1 agent): 1-2s
│  └─ Stage 3 (1 agent): 1-2s
├─ Database persist: <100ms
└─ WebSocket broadcast: <50ms

Total AI processing: 4-8 seconds
```

## System Requirements

```
CPU: 4+ cores (8+ recommended)
RAM: 16GB minimum (32GB recommended)
Disk: 30GB+ (for models + data)
GPU: Optional (nvidia-smi must work)
Network: 10+ Mbps (for model downloads)
```

## Key Endpoints

```bash
# Health checks
GET /health
GET /api/v1/health

# Incidents
GET /api/v1/incidents
GET /api/v1/incidents/{id}
POST /api/v1/test/incident

# Topology
GET /api/v1/topology/graph
GET /api/v1/topology/versions

# WebSocket
WS /ws

# Ollama
GET http://localhost:11434/api/tags
POST http://localhost:11434/api/generate
```

## Files to Verify

```bash
# AI agents
ls -la backend/src/sentinelops/ai/

# Frontend components
ls -la frontend/src/components/dashboard/

# Database migrations
ls -la backend/alembic/versions/ | grep 004

# Config
cat .env | grep OLLAMA
cat .env | grep AI_
```

## Documentation Files

```
- AI_SYSTEM_IMPLEMENTATION_COMPLETE.md (This file's parent)
- STARTUP_AND_VALIDATION.md (Comprehensive guide)
- verify_ai_system.sh (Verification script)
- docker-compose.yml (Service definitions)
```

## One-Liner System Check

```bash
echo "=== SentinelOps AI System Status ===" && \
docker-compose ps && \
echo "=== Ollama Models ===" && \
curl -s http://localhost:11434/api/tags | jq '.models[].name' && \
echo "=== Backend Health ===" && \
curl -s http://localhost:8000/health | jq '.' && \
echo "=== AI Agents Executed ===" && \
docker exec sentinelops-postgres psql -U sentinelops -d sentinelops -c "SELECT agent_type, COUNT(*) FROM ai_insights GROUP BY agent_type;" 2>/dev/null || echo "Database not ready"
```

## Performance Optimization

```bash
# Increase concurrency (if have GPU)
# In .env or docker-compose environment:
AI_AGENT_CONCURRENCY=5

# Use faster models
OLLAMA_MODEL=phi3:mini

# Reduce timeout (for faster failure)
OLLAMA_TIMEOUT_SECONDS=20

# Disable feature if not needed
FEATURE_AI_AGENTS=false  # Falls back to deterministic only
```
