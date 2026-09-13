# Phase 12: API Reference & Integration Guide

## Quick Start

### Installation & Setup

1. **Run Alembic Migration**
   ```bash
   cd backend
   alembic upgrade head
   ```
   This creates 8 new tables: incident_forecasts, incident_ancestry, service_health_scores, k8s_resource_intelligence, infrastructure_timelines, ai_confidence_validations, remediation_orchestrations, executive_metrics.

2. **Verify Models Loaded**
   ```python
   from sentinelops.models import (
       IncidentForecast,
       IncidentAncestry,
       ServiceHealthScore,
       K8sResourceIntelligence,
       InfrastructureTimeline,
       AIConfidenceValidation,
       RemediationOrchestration,
       ExecutiveMetrics,
   )
   ```

3. **Start Backend**
   ```bash
   uvicorn sentinelops.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Verify Endpoints**
   ```bash
   curl http://localhost:8000/api/intelligence/forecasts/00000000-0000-0000-0000-000000000000
   ```

## API Endpoints (10 Total)

### Intelligence Endpoints (5)

#### 1. GET /api/intelligence/forecasts/{cluster_id}

Retrieve incident forecasts for a cluster.

**Path Parameters:**
- `cluster_id` (UUID): Cluster identifier

**Query Parameters:**
- `forecast_type` (optional): Filter by type (pod_crash, memory_leak, cascading_failure, etc.)
- `min_probability` (optional): Minimum probability threshold (0.0-1.0)

**Response (200 OK):**
```json
{
  "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
  "forecasts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "forecast_type": "pod_crash",
      "target_service": "api-gateway",
      "probability": 0.45,
      "confidence_score": 0.78,
      "severity_prediction": "moderate",
      "forecast_time": "2026-05-17T10:30:00Z"
    }
  ],
  "forecast_count": 5,
  "high_probability_count": 2
}
```

**Use Cases:**
- Dashboard forecast widget
- Risk assessment before deployments
- Predictive alerting

---

#### 2. GET /api/intelligence/incident-ancestry/{incident_id}

Trace incident ancestry and causality chain.

**Path Parameters:**
- `incident_id` (UUID): Incident to analyze

**Response (200 OK):**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440002",
  "root_incident_id": "550e8400-e29b-41d4-a716-446655440000",
  "ancestry_depth": 3,
  "amplification_factor": 1.75,
  "evolution_chain": [
    {
      "service": "database",
      "severity": "critical",
      "event": "root_cause",
      "timestamp": "2026-05-16T08:00:00Z"
    },
    {
      "service": "auth-service",
      "severity": "high",
      "event": "cascading_failure",
      "timestamp": "2026-05-16T08:02:00Z"
    },
    {
      "service": "api-gateway",
      "severity": "high",
      "event": "high_latency",
      "timestamp": "2026-05-16T08:04:00Z"
    }
  ]
}
```

**Use Cases:**
- Incident timeline visualization
- Understanding cascade propagation
- Blast radius assessment

---

#### 3. GET /api/intelligence/service-health/{cluster_id}/{service_name}

Get comprehensive service health score.

**Path Parameters:**
- `cluster_id` (UUID): Cluster identifier
- `service_name` (string): Service name (e.g., "api-gateway")

**Response (200 OK):**
```json
{
  "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
  "service_name": "api-gateway",
  "overall_health": 0.87,
  "uptime_score": 0.92,
  "stability_score": 0.89,
  "dependency_score": 0.85,
  "resource_score": 0.92,
  "risk_level": "medium",
  "metrics": {
    "restart_frequency_per_day": 0.5,
    "incident_frequency_per_day": 0.2,
    "avg_recovery_time_seconds": 240.0
  }
}
```

**Health Score Formula:**
```
overall_health = (uptime × 0.40) + (stability × 0.30) + (dependency × 0.20) + (resource × 0.10)

Risk Levels:
- Low: health > 0.90
- Medium: health 0.75-0.90
- High: health 0.60-0.75
- Critical: health < 0.60
```

**Use Cases:**
- Service detail dashboard
- Dependency health inspection
- Performance trend analysis

---

#### 4. GET /api/intelligence/k8s-pressure/{cluster_id}/{namespace}

Analyze Kubernetes resource pressure in namespace.

**Path Parameters:**
- `cluster_id` (UUID): Cluster identifier
- `namespace` (string): Kubernetes namespace

**Response (200 OK):**
```json
{
  "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
  "namespace": "production",
  "pressure_issues": [
    {
      "resource_type": "memory",
      "pressure_type": "exhaustion",
      "saturation_percent": 78.5,
      "affected_workloads": ["api-gateway", "worker-1"],
      "mitigation": "Increase memory limits or scale horizontally"
    },
    {
      "resource_type": "cpu",
      "pressure_type": "noisy_neighbor",
      "saturation_percent": 89.0,
      "affected_workloads": ["heavy-worker"],
      "mitigation": "Isolate workload or implement QoS"
    }
  ],
  "critical_count": 0,
  "high_count": 2,
  "medium_count": 1
}
```

**Detected Pressure Types:**
- **exhaustion**: Node resource > 80%
- **noisy_neighbor**: Pod using > 2× percentile resources
- **contention**: Resource variance > 40% across nodes
- **imbalance**: Workload distribution uneven

**Use Cases:**
- Kubernetes diagnostics
- Resource optimization recommendations
- Capacity planning

---

#### 5. POST /api/intelligence/confidence-validate

Validate AI RCA reasoning and detect hallucinations.

**Request Body:**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440002",
  "rca_reasoning": "Pod OOM killed due to memory leak in cache layer. Service recovered after restart.",
  "confidence_score": 0.85
}
```

**Response (200 OK):**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440002",
  "is_valid": true,
  "is_hallucination": false,
  "confidence_score": 0.85,
  "passed_checks": 8,
  "failed_checks": 0,
  "validation_details": {
    "root_cause_exists": true,
    "affected_services_valid": true,
    "cascade_chain_valid": true,
    "timeline_match": true,
    "confidence_justified": true,
    "no_impossible_services": true,
    "recovery_realistic": true,
    "metrics_support": true
  }
}
```

**8-Point Validation Checklist:**
1. root_cause_exists - Service exists in topology
2. affected_services_valid - All services exist
3. cascade_chain_valid - Sequence matches history
4. timeline_match - Event timing is realistic
5. confidence_justified - Confidence supported by evidence
6. no_impossible_services - No fabricated services
7. recovery_realistic - Recovery actions address root cause
8. metrics_support - Metrics validate diagnosis

**Response (200 OK) - Hallucination Detected:**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440003",
  "is_valid": false,
  "is_hallucination": true,
  "confidence_score": 0.92,
  "passed_checks": 4,
  "failed_checks": 4,
  "validation_details": {
    "root_cause_exists": false,
    "affected_services_valid": false,
    "cascade_chain_valid": true,
    "timeline_match": false,
    "confidence_justified": false,
    "no_impossible_services": false,
    "recovery_realistic": false,
    "metrics_support": false
  }
}
```

**Use Cases:**
- RCA quality assurance gate
- AI model performance monitoring
- Audit trail for compliance

---

### Analytics Endpoints (1)

#### 6. GET /api/analytics/executive-dashboard/{cluster_id}

Retrieve executive-level KPIs and metrics.

**Path Parameters:**
- `cluster_id` (UUID): Cluster identifier

**Query Parameters:**
- `time_period_days` (optional, default=7): Analysis period

**Response (200 OK):**
```json
{
  "cluster_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_generated_at": "2026-05-17T10:30:00Z",
  "key_metrics": {
    "mttr_minutes": 5.2,
    "mttd_minutes": 1.04,
    "incidents_per_day": 0.86,
    "uptime_percent": 99.75,
    "sla_compliance_percent": 98.0
  },
  "predictions_24h": {
    "predicted_uptime_percent": 99.5,
    "predicted_incidents": 1
  },
  "scores": {
    "reliability": 0.921,
    "operational_efficiency": 0.88
  }
}
```

**KPI Reference:**

| Metric | Formula | Target |
|--------|---------|--------|
| MTTR (min) | Σ recovery_time / incident_count | < 5 min |
| MTTD (min) | MTTR × 0.2 | < 1 min |
| Incident Rate | incidents_per_period / days | < 1 /day |
| Uptime | 100 × (total_seconds - downtime) / total_seconds | > 99.9% |
| SLA Compliance | See formula below | > 99.0% |
| Reliability | (uptime/100×0.5) + ((1-mttr/3600)×0.3) + ((1-freq/5)×0.2) | > 0.90 |
| Efficiency | (avg_health×0.6) + ((1-mttr/3600)×0.4) | > 0.85 |

**SLA Compliance Calculation:**
```
if uptime >= 99.9%:  → 100%
elif uptime >= 99.5%: → 95%
elif uptime >= 99.0%: → 85%
else:                 → uptime × 0.8
```

**Use Cases:**
- Executive dashboards
- C-suite reporting
- Quarterly reviews
- SLA tracking

---

### Remediation Endpoints (2)

#### 7. POST /api/remediation/create-workflow

Create intelligent remediation workflow.

**Request Body:**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440002",
  "recommended_actions": ["isolate_workload", "pod_restart", "scale_replicas"],
  "affected_services": ["api-gateway"]
}
```

**Response (200 OK):**
```json
{
  "orchestration_id": "550e8400-e29b-41d4-a716-446655440010",
  "incident_id": "550e8400-e29b-41d4-a716-446655440002",
  "step_count": 3,
  "status": "created",
  "confidence_score": 0.87,
  "rollback_required": true,
  "workflow": [
    {
      "step": 0,
      "action_type": "isolate_workload",
      "target_services": ["api-gateway"],
      "details": {
        "strategy": "namespace",
        "qos_class": "Guaranteed"
      }
    },
    {
      "step": 1,
      "action_type": "pod_restart",
      "target_services": ["api-gateway"],
      "details": {
        "grace_period": 30,
        "max_retries": 3
      }
    },
    {
      "step": 2,
      "action_type": "scale_replicas",
      "target_services": ["api-gateway"],
      "details": {
        "scale_factor": 1.5,
        "max_replicas": 10
      }
    }
  ]
}
```

**Action Priority (Auto-Ordered):**
1. isolate_workload (prevent cascade)
2. route_traffic (failover)
3. pod_restart (recovery)
4. scale_replicas (scaling)
5. monitor (observe)

**Use Cases:**
- Automated incident response
- Runbook generation
- Operator assistance

---

#### 8. POST /api/remediation/execute-step

Execute a single remediation workflow step.

**Request Body:**
```json
{
  "incident_id": "550e8400-e29b-41d4-a716-446655440002",
  "step_index": 1
}
```

**Response (200 OK):**
```json
{
  "step_index": 1,
  "step_type": "pod_restart",
  "status": "executed",
  "result": {
    "pods_restarted": 3,
    "time_seconds": 12
  },
  "workflow_progress": "2/3"
}
```

**Use Cases:**
- Progressive remediation execution
- Manual approval workflow
- Step-by-step incident recovery

---

### Event Endpoints (2)

#### 9. POST /api/events/deduplicate

Deduplicate similar infrastructure events.

**Request Body:**
```json
{
  "events": [
    {
      "type": "pod_crash",
      "source": "api-gateway",
      "affected_entities": ["cache"],
      "timestamp": "2026-05-17T10:30:00Z"
    },
    {
      "type": "pod_crash",
      "source": "api-gateway",
      "affected_entities": ["cache"],
      "timestamp": "2026-05-17T10:30:05Z"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "original_count": 2,
  "deduplicated_count": 1,
  "removed_duplicates": 1,
  "events": [
    {
      "type": "pod_crash",
      "source": "api-gateway",
      "affected_entities": ["cache"],
      "timestamp": "2026-05-17T10:30:00Z",
      "occurrence_count": 2
    }
  ]
}
```

**Similarity Formula:**
```
similarity = (0.3 × type_match) + (0.3 × source_match) + (0.4 × entity_overlap)

Duplicate threshold: similarity >= 0.85
```

**Use Cases:**
- Event noise reduction
- Alert fatigue mitigation
- Event correlation

---

#### 10. POST /api/events/cluster-anomalies

Cluster related anomalies into incident groups.

**Request Body:**
```json
{
  "anomalies": [
    {
      "type": "high_latency",
      "service": "api-gateway",
      "severity": "high",
      "timestamp": "2026-05-17T10:30:00Z"
    },
    {
      "type": "high_cpu",
      "service": "api-gateway",
      "severity": "high",
      "timestamp": "2026-05-17T10:30:10Z"
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "anomaly_count": 2,
  "cluster_count": 1,
  "clusters": [
    {
      "cluster_type": "resource_exhaustion",
      "service": "api-gateway",
      "severity": "high",
      "anomaly_count": 2,
      "anomalies": [
        {"type": "high_latency", "severity": "high"},
        {"type": "high_cpu", "severity": "high"}
      ]
    }
  ]
}
```

**Use Cases:**
- Root cause anomaly grouping
- Incident correlation
- Pattern detection

---

## Error Responses

All endpoints follow standard HTTP error codes:

### 400 Bad Request
```json
{
  "detail": "Invalid cluster_id format"
}
```

### 404 Not Found
```json
{
  "detail": "Incident not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database connection failed"
}
```

## Integration Examples

### Example 1: Full Incident Analysis Pipeline

```python
import requests
import json

CLUSTER_ID = "550e8400-e29b-41d4-a716-446655440000"
INCIDENT_ID = "550e8400-e29b-41d4-a716-446655440002"

# 1. Get forecasts
forecasts = requests.get(
    f"http://localhost:8000/api/intelligence/forecasts/{CLUSTER_ID}"
).json()

# 2. Trace incident ancestry
ancestry = requests.get(
    f"http://localhost:8000/api/intelligence/incident-ancestry/{INCIDENT_ID}"
).json()

# 3. Check service health
health = requests.get(
    f"http://localhost:8000/api/intelligence/service-health/{CLUSTER_ID}/api-gateway"
).json()

# 4. Validate RCA
rca_validation = requests.post(
    "http://localhost:8000/api/intelligence/confidence-validate",
    json={
        "incident_id": INCIDENT_ID,
        "rca_reasoning": "Pod crash due to memory leak",
        "confidence_score": 0.85
    }
).json()

# 5. Create remediation workflow
workflow = requests.post(
    "http://localhost:8000/api/remediation/create-workflow",
    json={
        "incident_id": INCIDENT_ID,
        "recommended_actions": ["isolate_workload", "pod_restart"],
        "affected_services": ["api-gateway"]
    }
).json()

print(f"Analysis complete. Hallucination detected: {rca_validation['is_hallucination']}")
print(f"Recommended workflow: {workflow['step_count']} steps")
```

### Example 2: Executive Metrics Dashboard

```python
import requests

CLUSTER_ID = "550e8400-e29b-41d4-a716-446655440000"

# Fetch executive dashboard
dashboard = requests.get(
    f"http://localhost:8000/api/analytics/executive-dashboard/{CLUSTER_ID}?time_period_days=30"
).json()

# Display KPIs
print(f"MTTR: {dashboard['key_metrics']['mttr_minutes']:.1f} minutes")
print(f"Uptime: {dashboard['key_metrics']['uptime_percent']:.2f}%")
print(f"SLA Compliance: {dashboard['key_metrics']['sla_compliance_percent']:.1f}%")
print(f"Reliability Score: {dashboard['scores']['reliability']:.3f}")

# Check 24h predictions
print(f"Predicted incidents (24h): {dashboard['predictions_24h']['predicted_incidents']}")
```

### Example 3: Kubernetes Resource Analysis

```python
import requests

CLUSTER_ID = "550e8400-e29b-41d4-a716-446655440000"
NAMESPACE = "production"

# Analyze pressure
pressure = requests.get(
    f"http://localhost:8000/api/intelligence/k8s-pressure/{CLUSTER_ID}/{NAMESPACE}"
).json()

# Check for critical issues
if pressure['critical_count'] > 0:
    print(f"⚠️ {pressure['critical_count']} critical resource pressure issues")
    for issue in pressure['pressure_issues']:
        print(f"  - {issue['pressure_type']}: {issue['saturation_percent']:.1f}%")
        print(f"    Affected: {', '.join(issue['affected_workloads'])}")
        print(f"    Mitigation: {issue['mitigation']}")
```

## Rate Limiting & Performance

**Recommended Limits:**
- Forecasts: 100 req/min per cluster
- Health scores: 300 req/min per cluster
- RCA validation: 60 req/min per cluster
- Analytics: 30 req/min per cluster

**Optimization Tips:**
- Cache forecast results for 5 minutes
- Batch health score requests when possible
- Use time_period_days=7 (default) for analytics
- Call K8s pressure analysis every 5 minutes

## Monitoring

Key metrics to track:

```
phase_12_forecast_latency_ms
phase_12_health_score_latency_ms
phase_12_validation_latency_ms
phase_12_analytics_latency_ms
phase_12_hallucination_rate
phase_12_forecast_accuracy
phase_12_workflow_execution_time_ms
```

Recommended alerts:
- Forecast latency > 500ms
- Hallucination rate > 5%
- Validation failed_checks > 3
- Remediation workflow execution > 60s
