"""Phase 12 - Enterprise incident intelligence and predictive operations tests."""

import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from sentinelops.engines.forecast import predictive_forecast_engine
from sentinelops.engines.timeline import timeline_intelligence
from sentinelops.engines.service_health import enterprise_health_scorer
from sentinelops.engines.k8s_intelligence import k8s_intelligence
from sentinelops.engines.confidence import confidence_validator
from sentinelops.engines.event_intelligence import event_intelligence
from sentinelops.engines.analytics import executive_analytics
from sentinelops.engines.remediation_orchestration import remediation_orchestrator


class TestPredictiveIncidentForecasting:
    """Test predictive incident forecasting engine."""

    @pytest.mark.asyncio
    async def test_forecast_pod_crashes(self):
        """Test pod crash forecasting based on history."""
        cluster_id = uuid4()
        incident_history = [
            {
                "started_at": datetime.utcnow() - timedelta(hours=i),
                "root_service": "api-gateway",
                "severity": "high",
                "error_type": "pod_crash",
            }
            for i in range(5)
        ]

        forecasts = await predictive_forecast_engine.forecast_future_incidents(
            cluster_id=cluster_id,
            incident_history=incident_history,
            topology={"services": ["api-gateway", "auth-service"]},
            forecast_horizon_hours=24,
        )

        assert len(forecasts) > 0
        assert any(f.forecast_type == "pod_crash" for f in forecasts)
        assert all(0.0 <= f.probability <= 1.0 for f in forecasts)
        assert all(0.0 <= f.confidence_score <= 1.0 for f in forecasts)

    @pytest.mark.asyncio
    async def test_forecast_memory_issues(self):
        """Test memory leak forecasting."""
        cluster_id = uuid4()
        incident_history = [
            {
                "started_at": datetime.utcnow() - timedelta(hours=i),
                "root_service": "worker-service",
                "severity": "medium",
                "error_type": "oom_kill",
            }
            for i in range(3)
        ]

        forecasts = await predictive_forecast_engine.forecast_future_incidents(
            cluster_id=cluster_id,
            incident_history=incident_history,
            topology={"services": ["worker-service", "cache"]},
            forecast_horizon_hours=24,
        )

        memory_forecasts = [f for f in forecasts if f.forecast_type == "memory_leak"]
        assert len(memory_forecasts) > 0

    @pytest.mark.asyncio
    async def test_forecast_cascading_failures(self):
        """Test cascading failure prediction."""
        cluster_id = uuid4()
        topology = {
            "services": ["api-gateway", "auth-service", "database"],
            "dependencies": {
                "api-gateway": ["auth-service"],
                "auth-service": ["database"],
            },
        }
        incident_history = [
            {
                "started_at": datetime.utcnow() - timedelta(hours=i),
                "root_service": "database",
                "affected_services": ["auth-service", "api-gateway"],
                "severity": "critical",
            }
            for i in range(2)
        ]

        forecasts = await predictive_forecast_engine.forecast_future_incidents(
            cluster_id=cluster_id,
            incident_history=incident_history,
            topology=topology,
            forecast_horizon_hours=24,
        )

        cascade_forecasts = [f for f in forecasts if f.forecast_type == "cascading_failure"]
        assert len(cascade_forecasts) > 0


class TestInfrastructureTimelineIntelligence:
    """Test incident ancestry and timeline analysis."""

    @pytest.mark.asyncio
    async def test_build_incident_ancestry(self):
        """Test incident ancestry chain building."""
        incident_id = uuid4()
        root_incident_id = uuid4()

        current_incident = {
            "id": incident_id,
            "root_service": "api-gateway",
            "affected_services": ["auth-service", "cache"],
            "cascade_chain": json.dumps([str(root_incident_id)]),
        }

        incident_history = [
            {
                "id": root_incident_id,
                "root_service": "database",
                "started_at": datetime.utcnow() - timedelta(hours=1),
                "resolved_at": datetime.utcnow() - timedelta(minutes=30),
            },
            {
                "id": incident_id,
                "root_service": "api-gateway",
                "started_at": datetime.utcnow() - timedelta(minutes=25),
            },
        ]

        timeline_events = [
            {
                "service": "database",
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "event_type": "pod_crash",
            },
            {
                "service": "auth-service",
                "timestamp": datetime.utcnow() - timedelta(minutes=29),
                "event_type": "cascading_failure",
            },
            {
                "service": "api-gateway",
                "timestamp": datetime.utcnow() - timedelta(minutes=25),
                "event_type": "high_latency",
            },
        ]

        ancestry = await timeline_intelligence.build_incident_ancestry(
            current_incident=current_incident,
            incident_history=incident_history,
            timeline_events=timeline_events,
        )

        assert ancestry.incident_id == incident_id
        assert ancestry.ancestry_depth >= 1
        assert ancestry.amplification_factor > 0.0
        assert len(ancestry.evolution_chain) > 0

    @pytest.mark.asyncio
    async def test_track_timeline_event(self):
        """Test timeline event tracking."""
        cluster_id = uuid4()
        event_id = uuid4()

        timeline = await timeline_intelligence.track_timeline_event(
            cluster_id=cluster_id,
            event_type="pod_crash",
            source_entity="api-gateway",
            affected_entities=["auth-service", "cache"],
            parent_event_id=None,
        )

        assert timeline.cluster_id == cluster_id
        assert timeline.event_type == "pod_crash"
        assert timeline.source_entity == "api-gateway"
        assert timeline.causality_score > 0.0

    @pytest.mark.asyncio
    async def test_analyze_event_lineage(self):
        """Test event lineage analysis."""
        start_event_id = uuid4()
        child_event_id = uuid4()

        all_events = [
            {
                "id": start_event_id,
                "event_type": "pod_crash",
                "source_entity": "database",
                "affected_entities": ["auth-service"],
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "parent_event_id": None,
            },
            {
                "id": child_event_id,
                "event_type": "cascading_failure",
                "source_entity": "auth-service",
                "affected_entities": ["api-gateway"],
                "timestamp": datetime.utcnow() - timedelta(minutes=55),
                "parent_event_id": start_event_id,
            },
        ]

        lineage = await timeline_intelligence.analyze_event_lineage(
            start_event_id=start_event_id,
            all_events=all_events,
        )

        assert "propagation_depth" in lineage
        assert lineage["propagation_depth"] >= 1
        assert "affected_service_count" in lineage


class TestEnterpriseServiceHealthScoring:
    """Test service health scoring engine."""

    @pytest.mark.asyncio
    async def test_calculate_service_health_healthy(self):
        """Test health score calculation for healthy service."""
        cluster_id = uuid4()

        score = await enterprise_health_scorer.calculate_service_health(
            cluster_id=cluster_id,
            service_name="api-gateway",
            metrics={
                "uptime_percent": 99.95,
                "cpu_percent": 30,
                "memory_percent": 50,
                "restart_count": 0,
            },
            dependency_health_scores={"auth": 0.95, "database": 0.98},
            incident_history=[],
        )

        assert score.overall_health > 0.85
        assert score.risk_level == "low"
        assert score.uptime_score > 0.9
        assert score.stability_score > 0.9

    @pytest.mark.asyncio
    async def test_calculate_service_health_unhealthy(self):
        """Test health score calculation for unhealthy service."""
        cluster_id = uuid4()

        score = await enterprise_health_scorer.calculate_service_health(
            cluster_id=cluster_id,
            service_name="failing-service",
            metrics={
                "uptime_percent": 95.0,
                "cpu_percent": 95,
                "memory_percent": 92,
                "restart_count": 15,
            },
            dependency_health_scores={"auth": 0.6},
            incident_history=[
                {
                    "started_at": datetime.utcnow() - timedelta(hours=i),
                    "resolved_at": datetime.utcnow() - timedelta(hours=i - 1),
                }
                for i in range(5)
            ],
        )

        assert score.overall_health < 0.75
        assert score.risk_level in ["high", "critical"]

    @pytest.mark.asyncio
    async def test_calculate_cluster_risk_index(self):
        """Test cluster-wide risk index calculation."""
        cluster_id = uuid4()

        service_scores = [
            type("obj", (object,), {"service_name": "api", "overall_health": 0.95})(),
            type("obj", (object,), {"service_name": "db", "overall_health": 0.70})(),
            type("obj", (object,), {"service_name": "cache", "overall_health": 0.55})(),
        ]

        risk_index = await enterprise_health_scorer.calculate_cluster_risk_index(
            cluster_id=cluster_id,
            service_scores=service_scores,
        )

        assert "risk_index" in risk_index
        assert "at_risk_count" in risk_index
        assert "critical_count" in risk_index
        assert risk_index["at_risk_count"] >= 1


class TestAdvancedK8sIntelligence:
    """Test Kubernetes resource pressure analysis."""

    @pytest.mark.asyncio
    async def test_detect_noisy_neighbors(self):
        """Test noisy neighbor detection."""
        namespace = "production"
        pods = [
            {"name": "pod-a", "cpu": 50, "memory": 500},
            {"name": "pod-b", "cpu": 1200, "memory": 2500},  # Noisy neighbor
            {"name": "pod-c", "cpu": 45, "memory": 480},
        ]

        noisy = await k8s_intelligence.detect_noisy_neighbors(namespace, pods)

        assert len(noisy) > 0
        assert any(p["name"] == "pod-b" for p in noisy)

    @pytest.mark.asyncio
    async def test_detect_resource_imbalance(self):
        """Test resource imbalance detection across nodes."""
        nodes = [
            {"name": "node-1", "available_cpu": 2000, "available_memory": 4000},
            {"name": "node-2", "available_cpu": 500, "available_memory": 1000},
            {"name": "node-3", "available_cpu": 2100, "available_memory": 4200},
        ]

        imbalance = await k8s_intelligence.detect_resource_imbalance(nodes)

        assert imbalance is not None
        assert imbalance.get("variance") > 0.4

    @pytest.mark.asyncio
    async def test_detect_orphaned_pvcs(self):
        """Test orphaned PVC detection."""
        namespace = "default"
        pvcs = [
            {"name": "pvc-1", "status": "Bound"},
            {"name": "pvc-2", "status": "Unbound"},
            {"name": "pvc-3", "status": "Bound"},
        ]
        pods = [
            {"name": "pod-1", "volumes": ["pvc-1"]},
            {"name": "pod-2", "volumes": ["pvc-3"]},
        ]

        orphaned = await k8s_intelligence.detect_orphaned_pvcs(namespace, pvcs, pods)

        assert len(orphaned) > 0

    @pytest.mark.asyncio
    async def test_detect_zombie_workloads(self):
        """Test zombie workload detection."""
        namespace = "default"
        pods = [
            {
                "name": "active-pod",
                "age_seconds": 3600,
                "cpu": 500,
                "memory": 200,
                "rps": 100,
            },
            {
                "name": "zombie-pod",
                "age_seconds": 86400 * 2,
                "cpu": 5,
                "memory": 8,
                "rps": 0.05,
            },
        ]

        zombies = await k8s_intelligence.detect_zombie_workloads(namespace, pods)

        assert len(zombies) > 0
        assert any(p["name"] == "zombie-pod" for p in zombies)


class TestAIConfidenceValidator:
    """Test AI RCA validation and hallucination detection."""

    @pytest.mark.asyncio
    async def test_validate_valid_rca(self):
        """Test validation of valid RCA reasoning."""
        incident_id = uuid4()

        validation = await confidence_validator.validate_rca_reasoning(
            incident_id=incident_id,
            rca_reasoning="Pod OOM killed due to memory leak in worker process. App crashed.",
            confidence_score=0.85,
            incident_data={
                "root_service": "worker-service",
                "affected_services": ["worker-service"],
                "cascade_chain": [],
            },
            topology={"services": ["worker-service"], "dependencies": {}},
            incident_history=[],
        )

        assert validation.is_valid is True
        assert validation.is_hallucination is False
        assert validation.passed_checks >= 5

    @pytest.mark.asyncio
    async def test_validate_hallucinating_rca(self):
        """Test detection of hallucinating RCA."""
        incident_id = uuid4()

        validation = await confidence_validator.validate_rca_reasoning(
            incident_id=incident_id,
            rca_reasoning="Pod crashed due to non-existent service 'quantum-processor' overloading the network.",
            confidence_score=0.92,
            incident_data={
                "root_service": "api-gateway",
                "affected_services": ["api-gateway"],
                "cascade_chain": [],
            },
            topology={"services": ["api-gateway", "auth"], "dependencies": {}},
            incident_history=[],
        )

        assert validation.is_hallucination is True or validation.passed_checks < 5

    @pytest.mark.asyncio
    async def test_calculate_hallucination_risk(self):
        """Test hallucination risk calculation."""
        validations = [
            type("obj", (object,), {"is_hallucination": True})(),
            type("obj", (object,), {"is_hallucination": False})(),
            type("obj", (object,), {"is_hallucination": False})(),
            type("obj", (object,), {"is_hallucination": True})(),
        ]

        risk = await confidence_validator.calculate_ai_hallucination_risk(validations)

        assert 0.0 <= risk <= 1.0
        assert risk == 0.5  # 2/4 hallucinations


class TestEventIntelligence:
    """Test event deduplication and clustering."""

    @pytest.mark.asyncio
    async def test_deduplicate_events(self):
        """Test event deduplication."""
        events = [
            {
                "type": "pod_crash",
                "source": "api-gateway",
                "affected_entities": ["cache"],
                "timestamp": datetime.utcnow(),
            },
            {
                "type": "pod_crash",
                "source": "api-gateway",
                "affected_entities": ["cache"],
                "timestamp": datetime.utcnow() + timedelta(seconds=5),
            },
            {
                "type": "memory_spike",
                "source": "worker",
                "affected_entities": ["database"],
                "timestamp": datetime.utcnow() + timedelta(seconds=60),
            },
        ]

        deduplicated = await event_intelligence.deduplicate_events(events)

        assert len(deduplicated) < len(events)
        assert len(deduplicated) == 2

    @pytest.mark.asyncio
    async def test_cluster_anomalies(self):
        """Test anomaly clustering."""
        anomalies = [
            {
                "type": "high_latency",
                "service": "api-gateway",
                "severity": "high",
                "timestamp": datetime.utcnow(),
            },
            {
                "type": "high_cpu",
                "service": "api-gateway",
                "severity": "high",
                "timestamp": datetime.utcnow() + timedelta(seconds=10),
            },
            {
                "type": "memory_leak",
                "service": "worker",
                "severity": "medium",
                "timestamp": datetime.utcnow() + timedelta(minutes=5),
            },
        ]

        clusters = await event_intelligence.cluster_anomalies(anomalies)

        assert len(clusters) >= 1
        assert "cluster_type" in clusters[0]


class TestExecutiveAnalytics:
    """Test executive metrics calculation."""

    @pytest.mark.asyncio
    async def test_calculate_executive_metrics(self):
        """Test executive metrics calculation."""
        cluster_id = uuid4()
        incident_history = [
            {
                "started_at": datetime.utcnow() - timedelta(hours=i),
                "resolved_at": datetime.utcnow() - timedelta(hours=i - 1),
            }
            for i in range(7)
        ]

        metrics = await executive_analytics.calculate_executive_metrics(
            cluster_id=cluster_id,
            incident_history=incident_history,
            service_health_scores=[],
            forecasts=[],
            time_period_days=7,
        )

        assert metrics.mttr_seconds > 0
        assert metrics.mttd_seconds > 0
        assert 0.0 <= metrics.uptime_percent <= 100.0
        assert 0.0 <= metrics.sla_compliance_percent <= 100.0
        assert 0.0 <= metrics.reliability_score <= 1.0

    @pytest.mark.asyncio
    async def test_generate_analytics_report(self):
        """Test analytics report generation."""
        metrics = type(
            "obj",
            (object,),
            {
                "cluster_id": uuid4(),
                "mttr_seconds": 300,
                "mttd_seconds": 60,
                "incident_frequency_per_day": 1.5,
                "uptime_percent": 99.8,
                "sla_compliance_percent": 95.0,
                "predicted_uptime_24h": 99.5,
                "predicted_incidents_24h": 2,
                "reliability_score": 0.92,
                "operational_efficiency_score": 0.88,
            },
        )()

        report = await executive_analytics.generate_analytics_report(metrics)

        assert "key_metrics" in report
        assert "predictions_24h" in report
        assert "scores" in report
        assert report["key_metrics"]["mttr_minutes"] == 5.0


class TestRemediationOrchestration:
    """Test remediation workflow orchestration."""

    @pytest.mark.asyncio
    async def test_create_remediation_workflow(self):
        """Test workflow creation and step generation."""
        incident_id = uuid4()

        orchestration = await remediation_orchestrator.create_remediation_workflow(
            incident_id=incident_id,
            recommended_actions=["isolate_workload", "pod_restart", "scale_replicas"],
            topology={"services": ["api-gateway"], "dependencies": {}},
            affected_services=["api-gateway"],
        )

        assert orchestration.incident_id == incident_id
        assert orchestration.step_count == 3
        assert orchestration.status == "created"
        assert orchestration.confidence_score > 0.0

    @pytest.mark.asyncio
    async def test_action_prioritization(self):
        """Test action prioritization in workflows."""
        actions = ["scale_replicas", "isolate_workload", "monitor", "pod_restart"]
        prioritized = remediation_orchestrator._prioritize_actions(
            actions=actions,
            topology={},
            affected_services=[],
        )

        # Should be in priority order
        assert prioritized[0] == "isolate_workload"
        assert prioritized[1] == "pod_restart"
        assert prioritized[2] == "scale_replicas"

    @pytest.mark.asyncio
    async def test_validate_workflow_safety(self):
        """Test workflow safety validation."""
        workflow_steps = [
            {"action_type": "pod_restart", "target_service": "api"},
            {"action_type": "replica_scaling", "target_service": "api"},
        ]
        topology = {"services": ["api", "auth"], "dependencies": {"api": ["auth"]}}

        safety = await remediation_orchestrator.validate_workflow_safety(
            workflow_steps=workflow_steps,
            topology=topology,
        )

        assert "is_safe" in safety
        assert "issues" in safety
        assert "safety_score" in safety
        assert safety["safety_score"] < 1.0  # Should have identified risky sequence


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
