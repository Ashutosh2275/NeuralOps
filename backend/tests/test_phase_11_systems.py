"""Integration tests for SentinelOps Phase 11 systems."""
import asyncio
import json
import pytest
from uuid import uuid4

from sentinelops.engines.chaos import chaos_simulator
from sentinelops.engines.healing import autonomous_healer
from sentinelops.engines.health import health_engine
from sentinelops.engines.blast_radius import blast_radius_engine
from sentinelops.models.simulation import SimulatedIncident, SimulationType
from sentinelops.websocket.manager import ws_manager


class TestChaosSimulator:
    """Test chaos simulation engine."""

    @pytest.mark.asyncio
    async def test_cpu_spike_creation(self):
        """Test CPU spike simulation creation."""
        sim = await chaos_simulator.trigger_cpu_spike_storm(
            cluster_id=uuid4(),
            namespace="test",
            target_pods=["pod1", "pod2"],
            duration_seconds=60,
            severity="moderate",
        )
        assert sim.simulation_type == SimulationType.CPU_SPIKE
        assert sim.severity == "moderate"
        assert sim.duration_seconds == 60

    @pytest.mark.asyncio
    async def test_cascading_failure_creation(self):
        """Test cascading failure simulation."""
        sim = await chaos_simulator.trigger_cascading_multi_service_failure(
            cluster_id=uuid4(),
            namespace="test",
            service_chain=["api-gateway", "auth-service", "db"],
            duration_seconds=120,
        )
        assert sim.simulation_type == SimulationType.CASCADING_MULTI_SERVICE
        assert sim.severity == "critical"
        assert len(json.loads(sim.target_services)) == 3


class TestHealingEngine:
    """Test autonomous healing engine."""

    @pytest.mark.asyncio
    async def test_remediation_recommendation(self):
        """Test remediation recommendations."""
        incident_id = uuid4()
        sim_id = uuid4()
        actions = await autonomous_healer.recommend_remediation(
            incident_id=incident_id,
            simulation_id=sim_id,
            ai_recommendation="Restart affected pods and scale replicas",
        )
        assert len(actions) > 0
        assert any(a.action_type == "pod_restart" for a in actions)

    @pytest.mark.asyncio
    async def test_remediation_execution(self):
        """Test remediation action execution."""
        incident_id = uuid4()
        sim_id = uuid4()
        action = await autonomous_healer._create_pod_restart_action(
            incident_id=incident_id,
            simulation_id=sim_id,
            ai_recommendation="Test",
        )
        result = await autonomous_healer.execute_remediation_action(action)
        assert result is not None
        assert action.status == "completed"

    @pytest.mark.asyncio
    async def test_recovery_verification(self):
        """Test recovery verification."""
        incident_id = uuid4()
        recovered = await autonomous_healer.verify_recovery(incident_id, 0.6)
        assert isinstance(recovered, bool)


class TestHealthEngine:
    """Test infrastructure health scoring."""

    @pytest.mark.asyncio
    async def test_health_score_calculation(self):
        """Test health score calculation."""
        score = await health_engine.calculate_health_score(
            cluster_id=uuid4(),
            active_incidents=2,
            active_remediations=1,
        )
        assert 0 <= score.overall_health <= 1
        assert 0 <= score.cluster_health <= 1
        assert 0 <= score.incident_risk_score <= 1
        assert 0 <= score.cascading_failure_probability <= 1

    @pytest.mark.asyncio
    async def test_health_with_services(self):
        """Test health calculation with service data."""
        score = await health_engine.calculate_health_score(
            cluster_id=uuid4(),
            services={
                "api-gateway": {
                    "uptime_percent": 99.9,
                    "response_time_ms": 45,
                    "error_rate_percent": 0.1,
                },
                "auth-service": {
                    "uptime_percent": 99.8,
                    "response_time_ms": 60,
                    "error_rate_percent": 0.2,
                },
            },
        )
        assert score.service_health > 0.8


class TestBlastRadiusEngine:
    """Test blast radius intelligence."""

    @pytest.mark.asyncio
    async def test_blast_radius_calculation(self):
        """Test blast radius calculation."""
        event = await blast_radius_engine.calculate_blast_radius(
            origin_pod="api-gateway-1",
            origin_namespace="production",
            affected_services=["api-gateway", "auth-service", "payment-service"],
            simulation_id=uuid4(),
        )
        assert event.degradation_intensity > 0
        assert event.propagation_depth >= 0
        assert json.loads(event.recovery_path_json) is not None

    @pytest.mark.asyncio
    async def test_impact_estimation(self):
        """Test business impact estimation."""
        impact = await blast_radius_engine.estimate_impact(
            affected_services=["api-gateway", "payment-service"],
            severity=0.8,
        )
        assert "affected_service_count" in impact
        assert "business_impact_score" in impact
        assert "estimated_recovery_minutes" in impact


class TestWebSocketManager:
    """Test WebSocket event management."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        assert isinstance(ws_manager.connections, set)
        assert isinstance(ws_manager.subscribers, dict)

    def test_event_subscription(self):
        """Test event subscription."""
        called = []

        def handler(payload):
            called.append(payload)

        ws_manager.subscribe("test_event", handler)
        assert "test_event" in ws_manager.subscribers

    @pytest.mark.asyncio
    async def test_event_emission(self):
        """Test event emission to subscribers."""
        events = []

        async def handler(payload):
            events.append(payload)

        ws_manager.subscribe("test_event", handler)
        await ws_manager.emit_event("test_event", {"data": "test"})
        assert len(events) > 0


@pytest.mark.asyncio
async def test_full_incident_workflow():
    """Test complete incident workflow."""
    cluster_id = uuid4()
    incident_id = uuid4()

    # 1. Create simulation
    sim = await chaos_simulator.trigger_cpu_spike_storm(
        cluster_id=cluster_id,
        namespace="test",
        target_pods=["pod1"],
        duration_seconds=30,
    )
    assert sim.id is not None

    # 2. Get recommendations
    actions = await autonomous_healer.recommend_remediation(
        incident_id=incident_id,
        simulation_id=sim.id,
        ai_recommendation="Restart pods",
    )
    assert len(actions) > 0

    # 3. Execute remediation
    result = await autonomous_healer.execute_remediation_action(actions[0])
    assert result is not None

    # 4. Calculate health
    score = await health_engine.calculate_health_score(
        cluster_id=cluster_id,
        active_incidents=0,
        active_remediations=0,
    )
    assert score.overall_health > 0.5

    # 5. Verify recovery
    recovered = await autonomous_healer.verify_recovery(incident_id, score.overall_health)
    assert isinstance(recovered, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
