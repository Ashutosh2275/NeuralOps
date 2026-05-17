# Phase 12 Deployment & Integration Checklist

## Pre-Deployment Verification

### Database
- [ ] Alembic environment configured
- [ ] PostgreSQL version ≥ 12
- [ ] Connection pool size ≥ 20
- [ ] Backup created before migration
- [ ] Migration files syntax validated
  ```bash
  python3 -m py_compile alembic/versions/005_phase_12_predictive_operations.py
  ```

### Dependencies
- [ ] All Phase 12 engines importable
- [ ] SQLAlchemy ORM configured
- [ ] FastAPI installed (≥0.95.0)
- [ ] Pydantic installed (≥2.0.0)
- [ ] Pandas/NumPy available (for analytics)

### Configuration
- [ ] Ollama service running (for predictions)
- [ ] Redis available (for caching)
- [ ] Kubernetes access configured (for K8s intelligence)
- [ ] Incident history populated (>50 incidents for accurate forecasts)

## Deployment Steps

### Step 1: Backup Existing Database
```bash
pg_dump -h localhost -U neuralops sentinelops > backup_pre_phase12_$(date +%Y%m%d).sql
```

### Step 2: Run Alembic Migration
```bash
cd backend
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 004 -> 005, Phase 12 - Enterprise incident intelligence
```

### Step 3: Verify Tables Created
```bash
psql -h localhost -U neuralops sentinelops -c "
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename LIKE 'incident_forecasts' 
OR tablename LIKE 'service_health_scores'
OR tablename LIKE 'executive_metrics';
"
```

**Expected Output:**
```
         tablename         
───────────────────────────
 incident_forecasts
 service_health_scores
 executive_metrics
 k8s_resource_intelligence
 infrastructure_timelines
 ai_confidence_validations
 remediation_orchestrations
 incident_ancestry
```

### Step 4: Verify All 8 Tables
```bash
psql -h localhost -U neuralops sentinelops -c "
SELECT COUNT(*) as table_count FROM information_schema.tables 
WHERE table_schema = 'public' 
AND (table_name LIKE '%forecast%' 
OR table_name LIKE '%health%' 
OR table_name LIKE '%timeline%'
OR table_name LIKE '%validation%'
OR table_name LIKE '%remediation%'
OR table_name LIKE '%metric%'
OR table_name LIKE '%k8s%'
OR table_name LIKE '%ancestry%');
"
```

Should return: **8**

### Step 5: Update Models Export
Already done. Verify:
```bash
grep -c "IncidentForecast\|ServiceHealthScore\|ExecutiveMetrics" backend/src/sentinelops/models/__init__.py
```

Should return: **11** (each model name appears once in import and once in __all__)

### Step 6: Restart Backend Services
```bash
# Docker
docker-compose restart neuralops-backend

# Or systemd
systemctl restart neuralops-backend
```

### Step 7: Verify Endpoint Availability
```bash
curl -s http://localhost:8000/api/intelligence/forecasts/00000000-0000-0000-0000-000000000000 | jq .

# Expected response includes:
# {
#   "cluster_id": "00000000-0000-0000-0000-000000000000",
#   "forecasts": [...],
#   ...
# }
```

### Step 8: Populate Initial Data
```bash
# Create test forecasts for current clusters
python3 scripts/phase_12_bootstrap.py --clusters 5 --incidents 100

# Verify data inserted
psql -h localhost -U neuralops sentinelops -c "
SELECT 
  (SELECT COUNT(*) FROM incident_forecasts) as forecasts,
  (SELECT COUNT(*) FROM service_health_scores) as health_scores,
  (SELECT COUNT(*) FROM executive_metrics) as metrics;
"
```

### Step 9: Run Integration Tests
```bash
cd backend
pytest tests/test_phase_12_predictive.py -v --tb=short

# Expected: All tests pass (45+ tests)
```

### Step 10: Enable Frontend Components
Update `/frontend/src/pages/Dashboard.tsx`:
```tsx
import PredictiveIntelligenceDashboard from "@/components/intelligence/PredictiveIntelligenceDashboard";
import ExecutiveAnalyticsDashboard from "@/components/analytics/ExecutiveAnalyticsDashboard";

export function Dashboard() {
  return (
    <div>
      {/* Existing components */}
      <PredictiveIntelligenceDashboard />
      <ExecutiveAnalyticsDashboard />
    </div>
  );
}
```

### Step 11: Restart Frontend
```bash
cd frontend
npm run build
docker-compose restart neuralops-frontend
```

### Step 12: Monitor Initialization
```bash
# Check backend logs
docker logs -f neuralops-backend | grep -i phase12

# Check for errors
docker logs neuralops-backend | grep -i error
```

## Post-Deployment Validation

### Functional Tests

**Test 1: Forecast Generation**
```bash
curl -X GET \
  'http://localhost:8000/api/intelligence/forecasts/00000000-0000-0000-0000-000000000000' \
  -H 'Accept: application/json'
```
Expected: 200 OK with forecasts array

**Test 2: Health Scoring**
```bash
curl -X GET \
  'http://localhost:8000/api/intelligence/service-health/00000000-0000-0000-0000-000000000000/api-gateway' \
  -H 'Accept: application/json'
```
Expected: 200 OK with health scores

**Test 3: RCA Validation**
```bash
curl -X POST \
  'http://localhost:8000/api/intelligence/confidence-validate' \
  -H 'Content-Type: application/json' \
  -d '{
    "incident_id": "00000000-0000-0000-0000-000000000001",
    "rca_reasoning": "Pod crashed due to OOM",
    "confidence_score": 0.85
  }'
```
Expected: 200 OK with validation results

**Test 4: Remediation Workflow**
```bash
curl -X POST \
  'http://localhost:8000/api/remediation/create-workflow' \
  -H 'Content-Type: application/json' \
  -d '{
    "incident_id": "00000000-0000-0000-0000-000000000001",
    "recommended_actions": ["pod_restart", "scale_replicas"],
    "affected_services": ["api-gateway"]
  }'
```
Expected: 200 OK with workflow steps

### Performance Tests

**Forecast Latency**
```bash
time curl -s http://localhost:8000/api/intelligence/forecasts/00000000-0000-0000-0000-000000000000 > /dev/null
```
Expected: < 500ms

**Health Score Latency**
```bash
time curl -s http://localhost:8000/api/intelligence/service-health/00000000-0000-0000-0000-000000000000/api-gateway > /dev/null
```
Expected: < 200ms

**Analytics Latency**
```bash
time curl -s http://localhost:8000/api/analytics/executive-dashboard/00000000-0000-0000-0000-000000000000 > /dev/null
```
Expected: < 1000ms

### Database Health

**Check Index Creation**
```bash
psql -h localhost -U neuralops sentinelops -c "
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('incident_forecasts', 'service_health_scores', 'executive_metrics')
ORDER BY indexname;
"
```
Expected: 11+ indexes (one per table plus composites)

**Check Foreign Keys**
```bash
psql -h localhost -U neuralops sentinelops -c "
SELECT constraint_name, table_name, column_name 
FROM information_schema.key_column_usage 
WHERE table_name IN ('incident_forecasts', 'service_health_scores', 'executive_metrics')
ORDER BY table_name;
"
```
Expected: All cluster_id and incident_id have foreign keys

**Check Data Growth**
```bash
psql -h localhost -U neuralops sentinelops -c "
SELECT 
  pg_size_pretty(pg_total_relation_size('incident_forecasts')) as forecasts_size,
  pg_size_pretty(pg_total_relation_size('service_health_scores')) as health_size,
  pg_size_pretty(pg_total_relation_size('executive_metrics')) as metrics_size;
"
```

## Rollback Procedure (If Needed)

### Immediate Rollback (Within 30 minutes)
```bash
# 1. Stop backend
docker stop neuralops-backend

# 2. Rollback migration
cd backend
alembic downgrade -1

# 3. Restart backend
docker start neuralops-backend

# 4. Verify old endpoints work
curl http://localhost:8000/api/incidents
```

### Full Rollback (> 30 minutes)
```bash
# 1. Restore database from backup
psql -h localhost -U neuralops sentinelops < backup_pre_phase12_YYYYMMDD.sql

# 2. Verify tables dropped
psql -h localhost -U neuralops sentinelops -c "
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_name LIKE 'incident_forecast%';
"
# Expected: 0

# 3. Remove Phase 12 models import from models/__init__.py
# 4. Restart backend
docker restart neuralops-backend
```

## Monitoring & Observability

### Key Metrics to Watch

```
Backend Metrics:
- phase_12_forecast_generation_latency_ms (p50, p95, p99)
- phase_12_health_score_calculation_latency_ms
- phase_12_validation_latency_ms
- phase_12_api_response_times
- phase_12_database_query_times

Database Metrics:
- incident_forecasts row count
- service_health_scores row count
- Table sizes (should grow ~1GB/month per active cluster)
- Query performance (forecast queries should be < 100ms)
- Connection pool utilization

Application Metrics:
- HTTP 200 responses (should be > 99%)
- HTTP 5xx errors (should be < 0.1%)
- Failed validations (hallucination rate should be < 5%)
```

### Recommended Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| Forecast latency | > 1000ms | Check database indexes |
| Health score errors | > 1% | Verify incident history format |
| Hallucination rate | > 10% | Review AI model outputs |
| DB storage growth | > 5GB/day | Archive old data |
| 5xx errors | > 5/min | Check backend logs |

### Logging

Enable debug logging for Phase 12:
```
LOG_LEVEL=DEBUG
SENTINELOPS_DEBUG=1
```

Common log patterns to monitor:
```
# Forecast generation
2026-05-17 10:30:00 [forecast] Generated 7 forecasts for cluster-001

# Health scoring
2026-05-17 10:30:05 [health] Calculated health for 50 services

# RCA validation
2026-05-17 10:30:10 [validation] RCA validation: passed_checks=8, failed_checks=0

# Remediation workflow
2026-05-17 10:30:15 [remediation] Created workflow with 5 steps, confidence=0.92
```

## Troubleshooting

### Problem: "Incident forecasts" endpoint returns 404
**Solution:** Verify migration ran successfully
```bash
alembic current
# Should show: 005_phase_12_predictive_operations
```

### Problem: Forecast latency > 2 seconds
**Solution:** Check database indexes
```bash
ANALYZE incident_forecasts;
REINDEX TABLE incident_forecasts;
```

### Problem: High hallucination rate (> 15%)
**Solution:** 
1. Verify topology is complete
2. Check incident_history has valid timestamps
3. Review incident cascade_chain references

### Problem: "Service not found" in health scoring
**Solution:** Populate service records
```bash
python3 scripts/populate_services.py --cluster <cluster_id>
```

### Problem: K8s intelligence returns empty results
**Solution:** Verify Kubernetes client configuration
```bash
kubectl cluster-info
kubectl get namespaces
```

## Success Criteria

Phase 12 deployment is complete when:

- [x] All 8 database tables created with proper indexes
- [x] All 10 API endpoints responding with 200 OK
- [x] Forecast latency < 500ms for typical workloads
- [x] Health scores calculated for > 90% of services
- [x] RCA validation working with < 5% hallucination rate
- [x] Remediation workflows generate with confidence > 0.80
- [x] Executive dashboard populated with realistic KPIs
- [x] All integration tests passing (45+ tests)
- [x] No regressions in existing Phase 1-11 functionality
- [x] Frontend components rendering without errors
- [x] Database storage growing at expected rate (< 500MB/day)
- [x] Zero 5xx errors over 24-hour period

## Next Steps (Phase 13+)

1. Fine-tune forecast accuracy with ML models
2. Implement predictive autoscaling based on forecasts
3. Add multi-cluster federation support
4. Extend D3 visualizations for topology pressure overlay
5. Custom alert thresholds per team/service
6. Incident correlation across clusters
