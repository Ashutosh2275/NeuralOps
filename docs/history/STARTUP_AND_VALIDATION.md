# SentinelOps AI System - Complete Startup & Validation Guide

## Files Created
- backend/src/sentinelops/ai/agents.py (4 new agents: NPLInfrastructureAssistant, StorageAgent, NetworkAgent, LogsAgent)
- frontend/src/components/dashboard/AIAssistantPanel.tsx (NLP Assistant UI)
- frontend/src/components/dashboard/ConfidenceVisualization.tsx (Confidence visualization)

## Files Modified
- backend/src/sentinelops/ai/agents.py (added 4 agents to existing 6)
- backend/src/sentinelops/ai/registry.py (registered new agents)
- backend/src/sentinelops/ai/orchestrator.py (updated PIPELINE with new agents)
- backend/src/sentinelops/ai/__init__.py (exported new agents)
- frontend/src/components/dashboard/AIInsightsPanel.tsx (enhanced with confidence visualization)
- frontend/src/components/dashboard/RCAPanel.tsx (enhanced cascade display)
- frontend/src/pages/IncidentDetail.tsx (integrated all AI dashboard components)
- docker-compose.yml (added model preloading to ollama services)

## Pre-Startup Verification

### 1. Check Python Version (3.12+ required)
```bash
python --version
python3 --version
```

### 2. Check Docker Installation
```bash
docker --version
docker-compose --version
```

### 3. Check GPU Availability (optional)
```bash
nvidia-smi
# If not available, will fall back to CPU
```

## Ollama Model Pull Commands

Run these BEFORE starting the system, or rely on docker-compose auto-pull:

```bash
# Pull models individually
ollama pull llama3.2:1b         # 2.5GB - Primary RCA analysis
ollama pull mistral:latest      # 4GB - CPU anomaly analysis  
ollama pull phi3:mini           # 2.2GB - Memory analysis
ollama pull qwen2.5:1.5b        # 1.8GB - Correlation analysis

# Or pull all:
for model in llama3.2:1b mistral phi3:mini qwen2.5:1.5b; do
  ollama pull $model
done

# Verify models loaded
curl http://localhost:11434/api/tags | jq '.models[] | .name'
```

## Database Migration Commands

```bash
# Navigate to backend directory
cd backend

# Run Alembic migrations (requires Python 3.12+)
alembic upgrade head

# Verify schema created
psql -h localhost -U sentinelops -d sentinelops -c "\dt"
```

## Docker Startup Commands

### Option A: GPU Support
```bash
# Start with GPU profile
docker-compose --profile gpu --profile app up -d

# Verify Ollama GPU detected
docker exec sentinelops-ollama ollama list
```

### Option B: CPU Only
```bash
# Start with CPU profile
docker-compose --profile cpu --profile app up -d

# Verify Ollama running
docker exec sentinelops-ollama-cpu ollama list
```

### Full System Startup
```bash
# 1. Start infrastructure (database, redis, prometheus, loki)
docker-compose up -d postgres redis prometheus loki

# 2. Wait for postgres health
sleep 10
docker-compose ps

# 3. Start Ollama (with appropriate profile)
docker-compose --profile gpu up -d ollama
# OR
docker-compose --profile cpu up -d ollama-cpu

# 4. Verify Ollama readiness
sleep 15
curl -s http://localhost:11434/api/tags | jq .

# 5. Start backend services
docker-compose --profile app up -d backend workers frontend

# 6. Verify all services running
docker-compose ps
```

## Validation Commands

### 1. Database Schema Validation
```bash
# Verify AI tables exist
docker exec sentinelops-postgres psql -U sentinelops -d sentinelops << EOF
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'ai_%';
EOF

# Expected output:
# ai_insights
# ai_reasoning_logs
# ai_recommendations
# incident_summaries
# infrastructure_memory
# anomaly_patterns
```

### 2. Ollama Service Validation
```bash
# Test Ollama API health
curl http://localhost:11434/api/health

# List available models
curl -s http://localhost:11434/api/tags | jq .

# Test model inference (llama3.2)
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "What is Kubernetes?",
  "stream": false
}'

# Response should contain "response" field with text
```

### 3. Backend API Validation
```bash
# Check backend health
curl http://localhost:8000/health

# Verify API is running
curl http://localhost:8000/docs

# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8000/ws

# Expected: 101 Switching Protocols
```

### 4. Frontend Validation
```bash
# Access frontend
curl -s http://localhost:5173 | head -50

# Should return HTML with SentinelOps branding
```

## AI System Testing Commands

### 1. Test AI Orchestrator Startup
```bash
# Check worker logs for AI initialization
docker logs sentinelops-workers 2>&1 | grep -i "ai_agent"

# Expected: "ai_agent_completed_cpu", "ai_agent_completed_memory", etc.
```

### 2. Trigger Incident (for AI Analysis)
```bash
# Send test correlation event
curl -X POST http://localhost:8000/api/v1/test/incident \
  -H "Content-Type: application/json" \
  -d '{
    "namespace": "default",
    "event_type": "correlation",
    "severity": "critical"
  }'
```

### 3. Monitor AI Processing
```bash
# Watch worker logs for AI insights
docker logs -f sentinelops-workers 2>&1 | grep "ai_"

# Watch for:
# - "ai_agent_completed_[agent_type]"
# - "ai_orchestration_started"
# - "ai_response_validation_"
```

### 4. Check Database for AI Results
```bash
# Query AI insights stored
docker exec sentinelops-postgres psql -U sentinelops -d sentinelops << EOF
SELECT agent_type, insight_type, COUNT(*) 
FROM ai_insights 
GROUP BY agent_type, insight_type 
ORDER BY agent_type;
EOF

# Query reasoning logs
docker exec sentinelops-postgres psql -U sentinelops -d sentinelops << EOF
SELECT agent_type, model_used, AVG(latency_ms) as avg_latency, COUNT(*) 
FROM ai_reasoning_logs 
GROUP BY agent_type, model_used 
ORDER BY agent_type;
EOF
```

## WebSocket Testing Commands

### 1. Monitor WebSocket Events
```bash
# Connect to WebSocket and listen for AI events
websocat ws://localhost:8000/ws 2>&1 | jq '.'

# Filter for AI events
websocat ws://localhost:8000/ws 2>&1 | jq 'select(.type=="ai_insight")'
```

### 2. Expected WebSocket Events
```json
{
  "type": "ai_insight",
  "payload": {
    "agent": "cpu",
    "findings": ["High CPU usage detected"],
    "confidence": 0.85,
    "reasoning": "CPU anomaly analysis"
  }
}

{
  "type": "recommendations",
  "payload": [
    {
      "title": "Scale pod resource",
      "priority": 1,
      "confidence": 0.9
    }
  ]
}
```

## Docker Commands for Monitoring

### View All Logs
```bash
# Backend logs
docker logs -f sentinelops-backend

# Workers logs
docker logs -f sentinelops-workers

# Ollama logs
docker logs -f sentinelops-ollama-cpu

# All services
docker-compose logs -f
```

### Resource Usage
```bash
# Monitor container stats
docker stats --no-stream

# Expected for AI workloads:
# CPU: 5-15% per agent (depends on model size)
# Memory: 2-4GB total for system
# GPU: 1-2GB if CUDA available
```

### Clean Up
```bash
# Stop all services
docker-compose down

# Remove volumes (caution: deletes data)
docker-compose down -v

# Remove images
docker-compose down -v --rmi all
```

## Expected Demo Behavior

### 1. System Startup Sequence (5-10 minutes)
1. PostgreSQL initializes (30s)
2. Redis starts (10s)
3. Prometheus starts (15s)
4. Loki starts (10s)
5. Ollama downloads models (2-5 min depending on connection)
6. Backend initializes (20s)
7. Workers connect to backend (10s)
8. Frontend builds and serves (30s)

### 2. Incident Triggering Sequence
1. Event arrives on Redis stream
2. Collector publishes to "enriched" stream
3. Worker correlation handler processes event
4. Deterministic RCA runs first (< 100ms)
5. AI Orchestrator starts (triggers 10 agents in 4 stages)
6. Stage 0: CPU, Memory, Storage, Network, Logs, Correlation agents run parallel
7. Stage 1: RCA + NLP agents run parallel
8. Stage 2: Recommendation agent runs
9. Stage 3: Summarization agent runs
10. Total AI processing: 2-5 seconds (depends on model size)

### 3. Expected AI Agent Output
```
Stage 0 (Parallel Resource Analysis):
  ✓ CPU Agent: 2 findings, 0.85 confidence
  ✓ Memory Agent: 1 finding, 0.9 confidence
  ✓ Storage Agent: 0 findings, 0.3 confidence
  ✓ Network Agent: 0 findings, 0.3 confidence
  ✓ Logs Agent: 1 finding, 0.75 confidence
  ✓ Correlation Agent: 3 findings, 0.8 confidence

Stage 1 (Root Cause Analysis):
  ✓ RCA Agent: 2 findings, 0.88 confidence
  ✓ NLP Assistant: 1 finding, 0.8 confidence

Stage 2 (Remediation):
  ✓ Recommendation Agent: 5 recommendations, 0.85 confidence

Stage 3 (Summary):
  ✓ Summarization Agent: 1 summary, 0.85 confidence

Total confidence: 0.83 (average across all agents)
```

### 4. Frontend Dashboard Display
- AI Insights panel shows latest findings from all agents
- Confidence visualization shows 10 agent bars (expected: 70-90% range)
- RCA panel displays cascade chain with influence scores
- Recommendation cards show prioritized actions
- AI Assistant panel shows real-time insights
- WebSocket updates every 100-500ms

### 5. No Cloud API Usage Verification
```bash
# Verify no external API calls
docker exec sentinelops-backend grep -r "openai\|claude\|gemini\|anthropic\|aws\|azure" src/
# Should return: nothing (only local ollama references)

docker exec sentinelops-workers grep -r "openai\|claude\|gemini\|anthropic\|aws\|azure" sentinelops/
# Should return: nothing
```

## Troubleshooting

### Issue: Ollama models not found
```bash
# Check Ollama is running
docker exec sentinelops-ollama-cpu ollama list
# If empty, models haven't downloaded yet

# Manually pull models
docker exec sentinelops-ollama-cpu ollama pull llama3.2:1b
```

### Issue: Backend can't connect to Ollama
```bash
# Check Ollama is accessible
curl -s http://ollama-cpu:11434/api/tags
# If fails, check docker network
docker network ls
docker inspect sentinelops_default
```

### Issue: AI agents failing silently
```bash
# Check worker logs for errors
docker logs sentinelops-workers | grep "ai_agent_failed"

# Check database for failed logs
docker exec sentinelops-postgres psql -U sentinelops -d sentinelops << EOF
SELECT agent_type, error_message FROM ai_reasoning_logs WHERE success = false;
EOF
```

### Issue: WebSocket not receiving AI events
```bash
# Verify events are being published
docker logs sentinelops-backend | grep "broadcast"

# Check frontend console for errors
# In browser DevTools: Console tab
```

## Performance Expectations

### Model Size vs Performance
- llama3.2:1b: ~500ms per query (recommended for most tasks)
- mistral: ~800ms per query (better reasoning)
- phi3:mini: ~300ms per query (fastest)
- qwen2.5:1.5b: ~600ms per query

### Concurrency
- Default: 3 agents in parallel (ai_agent_concurrency setting)
- Max recommended: 5 (depends on available VRAM)
- Stage 0 typically takes: 2-3 seconds (6 agents parallel)
- Full pipeline: 5-8 seconds

### Memory Usage
- Per model loaded: 500MB - 4GB
- Total with all 4 models: 8-12GB
- System total: 16GB recommended
- Minimum: 8GB (with 1-2 models)

## Configuration Tuning

Edit `.env` or docker-compose environment:

```bash
# Model selection
OLLAMA_MODEL=llama3.2:1b      # Primary model
OLLAMA_FALLBACK_MODEL=phi3:mini

# Concurrency
AI_AGENT_CONCURRENCY=3

# Feature flags
FEATURE_AI_AGENTS=true
FEATURE_LIVE_TOPOLOGY=true

# Timeouts
OLLAMA_TIMEOUT_SECONDS=30
AI_ORCHESTRATION_TIMEOUT_SECONDS=60
```

## Production Checklist

- [ ] Python 3.12+ installed
- [ ] Docker and Docker Compose installed
- [ ] GPU driver installed (nvidia-smi works)
- [ ] 16GB+ RAM available
- [ ] 10GB+ free disk for models
- [ ] All migrations run successfully
- [ ] Ollama models downloaded
- [ ] Backend health check passes
- [ ] WebSocket connectivity verified
- [ ] No cloud API keys in code/config
- [ ] Frontend loads without errors
- [ ] AI agents execute without failures
- [ ] RCA generation working
- [ ] Recommendations generating
- [ ] NLP assistant responding
- [ ] WebSocket AI events streaming
- [ ] Docker Compose still boots cleanly
