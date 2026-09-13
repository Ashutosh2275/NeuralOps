import asyncio
import json
import random
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sentinelops.models.simulation import (
    SimulatedIncident,
    SimulationType,
    SimulationSeverity,
)


class ChaosSimulator:
    """Orchestrates infrastructure chaos simulations."""

    def __init__(self):
        self.active_simulations = {}
        self.event_handlers = []

    def on_event(self, handler):
        self.event_handlers.append(handler)
        return handler

    async def emit_event(self, event_type: str, payload: dict):
        """Emit simulation event to all listeners."""
        payload["timestamp"] = datetime.utcnow().isoformat()
        payload["event_type"] = event_type
        for handler in self.event_handlers:
            try:
                await handler(payload) if asyncio.iscoroutinefunction(handler) else handler(payload)
            except Exception as e:
                print(f"Event handler error: {e}")

    async def trigger_cpu_spike_storm(
        self,
        cluster_id: UUID,
        namespace: str,
        target_pods: list[str],
        duration_seconds: int = 300,
        severity: str = "moderate",
    ) -> SimulatedIncident:
        """Simulate CPU spike storms across pods."""
        sim = SimulatedIncident(
            id=uuid4(),
            cluster_id=cluster_id,
            simulation_type=SimulationType.CPU_SPIKE,
            severity=severity,
            namespace=namespace,
            target_pods=json.dumps(target_pods),
            target_services=json.dumps([]),
            duration_seconds=duration_seconds,
            cascading_probability=0.4,
            metadata_json=json.dumps({
                "cpu_percent": 95,
                "spike_frequency": "intermittent",
                "affected_pod_count": len(target_pods),
            }),
            started_at=datetime.utcnow(),
        )

        await self.emit_event("simulation_created", {
            "simulation_id": str(sim.id),
            "type": "cpu_spike",
            "namespace": namespace,
            "pods": target_pods,
            "severity": severity,
        })

        asyncio.create_task(self._simulate_degradation(sim, target_pods))
        return sim

    async def trigger_memory_leak(
        self,
        cluster_id: UUID,
        namespace: str,
        target_pods: list[str],
        duration_seconds: int = 600,
        severity: str = "major",
    ) -> SimulatedIncident:
        """Simulate memory leak degradation."""
        sim = SimulatedIncident(
            id=uuid4(),
            cluster_id=cluster_id,
            simulation_type=SimulationType.MEMORY_LEAK,
            severity=severity,
            namespace=namespace,
            target_pods=json.dumps(target_pods),
            target_services=json.dumps([]),
            duration_seconds=duration_seconds,
            cascading_probability=0.6,
            metadata_json=json.dumps({
                "memory_growth_rate_mb_per_sec": 10,
                "initial_memory_usage_percent": 45,
                "target_memory_usage_percent": 95,
            }),
            started_at=datetime.utcnow(),
        )

        await self.emit_event("simulation_created", {
            "simulation_id": str(sim.id),
            "type": "memory_leak",
            "namespace": namespace,
            "pods": target_pods,
            "severity": severity,
        })

        asyncio.create_task(self._simulate_degradation(sim, target_pods))
        return sim

    async def trigger_pvc_saturation(
        self,
        cluster_id: UUID,
        namespace: str,
        target_pods: list[str],
        duration_seconds: int = 450,
        severity: str = "major",
    ) -> SimulatedIncident:
        """Simulate PVC storage saturation."""
        sim = SimulatedIncident(
            id=uuid4(),
            cluster_id=cluster_id,
            simulation_type=SimulationType.PVC_SATURATION,
            severity=severity,
            namespace=namespace,
            target_pods=json.dumps(target_pods),
            target_services=json.dumps([]),
            duration_seconds=duration_seconds,
            cascading_probability=0.5,
            metadata_json=json.dumps({
                "disk_usage_growth_percent": 2,
                "initial_disk_usage_percent": 40,
                "target_disk_usage_percent": 98,
                "affected_pvcs": ["pvc-logs", "pvc-data"],
            }),
            started_at=datetime.utcnow(),
        )

        await self.emit_event("simulation_created", {
            "simulation_id": str(sim.id),
            "type": "pvc_saturation",
            "namespace": namespace,
            "pods": target_pods,
        })

        asyncio.create_task(self._simulate_degradation(sim, target_pods))
        return sim

    async def trigger_network_latency(
        self,
        cluster_id: UUID,
        namespace: str,
        target_services: list[str],
        latency_ms: int = 500,
        duration_seconds: int = 300,
        severity: str = "moderate",
    ) -> SimulatedIncident:
        """Simulate network latency."""
        sim = SimulatedIncident(
            id=uuid4(),
            cluster_id=cluster_id,
            simulation_type=SimulationType.NETWORK_LATENCY,
            severity=severity,
            namespace=namespace,
            target_pods=json.dumps([]),
            target_services=json.dumps(target_services),
            duration_seconds=duration_seconds,
            cascading_probability=0.7,
            metadata_json=json.dumps({
                "latency_ms": latency_ms,
                "packet_loss_percent": 0,
                "jitter_ms": latency_ms * 0.2,
            }),
            started_at=datetime.utcnow(),
        )

        await self.emit_event("simulation_created", {
            "simulation_id": str(sim.id),
            "type": "network_latency",
            "services": target_services,
            "latency_ms": latency_ms,
        })

        asyncio.create_task(self._simulate_degradation(sim, []))
        return sim

    async def trigger_cascading_multi_service_failure(
        self,
        cluster_id: UUID,
        namespace: str,
        service_chain: list[str],
        duration_seconds: int = 500,
        severity: str = "critical",
    ) -> SimulatedIncident:
        """Simulate cascading failure across multiple services."""
        sim = SimulatedIncident(
            id=uuid4(),
            cluster_id=cluster_id,
            simulation_type=SimulationType.CASCADING_MULTI_SERVICE,
            severity=severity,
            namespace=namespace,
            target_pods=json.dumps([]),
            target_services=json.dumps(service_chain),
            duration_seconds=duration_seconds,
            cascading_probability=0.95,
            metadata_json=json.dumps({
                "service_chain": service_chain,
                "cascade_delay_seconds": [0, 5, 10, 15, 20],
                "impact_intensity": 0.9,
            }),
            started_at=datetime.utcnow(),
        )

        await self.emit_event("cascade_started", {
            "simulation_id": str(sim.id),
            "service_chain": service_chain,
            "propagation_depth": len(service_chain),
        })

        asyncio.create_task(self._simulate_cascading_degradation(sim, service_chain))
        return sim

    async def _simulate_degradation(self, sim: SimulatedIncident, target_pods: list[str]):
        """Simulate gradual degradation over time."""
        start_time = datetime.utcnow()
        steps = 10

        for step in range(steps):
            if (datetime.utcnow() - start_time).total_seconds() > sim.duration_seconds:
                break

            progress = step / steps
            intensity = min(0.5 + (progress * 0.5), 1.0)

            await self.emit_event("degradation_progress", {
                "simulation_id": str(sim.id),
                "type": sim.simulation_type,
                "progress": progress,
                "intensity": intensity,
                "affected_pods": target_pods,
                "status": "degrading",
            })

            await asyncio.sleep(sim.duration_seconds / steps)

        sim.ended_at = datetime.utcnow()
        await self.emit_event("simulation_completed", {
            "simulation_id": str(sim.id),
            "duration": (sim.ended_at - sim.started_at).total_seconds(),
            "status": "completed",
        })

    async def _simulate_cascading_degradation(self, sim: SimulatedIncident, service_chain: list[str]):
        """Simulate cascading degradation through service chain."""
        metadata = json.loads(sim.metadata_json)
        cascade_delays = metadata.get("cascade_delay_seconds", [])

        for idx, service in enumerate(service_chain):
            delay = cascade_delays[idx] if idx < len(cascade_delays) else idx * 5
            await asyncio.sleep(delay)

            await self.emit_event("blast_radius_updated", {
                "simulation_id": str(sim.id),
                "origin_service": service_chain[0],
                "affected_service": service,
                "propagation_depth": idx + 1,
                "total_depth": len(service_chain),
                "degradation_intensity": 0.5 + (idx / len(service_chain)) * 0.5,
            })

        sim.ended_at = datetime.utcnow()
        await self.emit_event("cascade_completed", {
            "simulation_id": str(sim.id),
            "total_affected_services": len(service_chain),
            "max_propagation_depth": len(service_chain),
        })


chaos_simulator = ChaosSimulator()
