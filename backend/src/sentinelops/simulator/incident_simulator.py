import asyncio
import random
from enum import Enum
from uuid import uuid4
from datetime import datetime, timedelta
from dataclasses import dataclass

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent, EventType, Severity
from sentinelops.streams.bus import EventBus

log = get_logger(__name__)


class SimulationSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, Enum):
    CPU_SPIKE = "cpu_spike"
    MEMORY_LEAK = "memory_leak"
    PVC_SATURATION = "pvc_saturation"
    NETWORK_LATENCY = "network_latency"
    PACKET_LOSS = "packet_loss"
    POD_RESTART_STORM = "pod_restart_storm"
    CRASHLOOP_BACKOFF = "crashloop_backoff"
    DEPENDENCY_FAILURE = "dependency_failure"
    DATABASE_BOTTLENECK = "database_bottleneck"
    API_GATEWAY_CONGESTION = "api_gateway_congestion"


@dataclass
class SimulationConfig:
    incident_type: IncidentType
    severity: SimulationSeverity
    namespace: str = "default"
    pod_pattern: str = "*"
    duration_seconds: int = 60
    start_delay_seconds: int = 0
    cascade_enabled: bool = False
    cascade_targets: list[str] = None


class IncidentSimulator:
    def __init__(self):
        self._settings = get_settings()
        self._bus = EventBus()
        self._active_simulations: dict[str, dict] = {}
        self._initialized = False

    async def initialize(self) -> None:
        await self._bus.initialize()
        self._initialized = True
        log.info("incident_simulator_initialized")

    async def start_simulation(self, config: SimulationConfig) -> str:
        if not self._initialized:
            await self.initialize()

        simulation_id = str(uuid4())
        self._active_simulations[simulation_id] = {
            "config": config,
            "started_at": datetime.utcnow(),
            "events_generated": 0,
        }

        asyncio.create_task(self._run_simulation(simulation_id, config))
        log.info(f"simulation_started_{config.incident_type}", simulation_id=simulation_id)
        return simulation_id

    async def _run_simulation(self, simulation_id: str, config: SimulationConfig) -> None:
        try:
            await asyncio.sleep(config.start_delay_seconds)

            if config.incident_type == IncidentType.CPU_SPIKE:
                await self._simulate_cpu_spike(simulation_id, config)
            elif config.incident_type == IncidentType.MEMORY_LEAK:
                await self._simulate_memory_leak(simulation_id, config)
            elif config.incident_type == IncidentType.PVC_SATURATION:
                await self._simulate_pvc_saturation(simulation_id, config)
            elif config.incident_type == IncidentType.NETWORK_LATENCY:
                await self._simulate_network_latency(simulation_id, config)
            elif config.incident_type == IncidentType.PACKET_LOSS:
                await self._simulate_packet_loss(simulation_id, config)
            elif config.incident_type == IncidentType.POD_RESTART_STORM:
                await self._simulate_pod_restart_storm(simulation_id, config)
            elif config.incident_type == IncidentType.CRASHLOOP_BACKOFF:
                await self._simulate_crashloop_backoff(simulation_id, config)
            elif config.incident_type == IncidentType.DEPENDENCY_FAILURE:
                await self._simulate_dependency_failure(simulation_id, config)
            elif config.incident_type == IncidentType.DATABASE_BOTTLENECK:
                await self._simulate_database_bottleneck(simulation_id, config)
            elif config.incident_type == IncidentType.API_GATEWAY_CONGESTION:
                await self._simulate_api_gateway_congestion(simulation_id, config)

            if config.cascade_enabled and config.cascade_targets:
                await self._trigger_cascades(simulation_id, config)

        except Exception as e:
            log.error(f"simulation_failed_{config.incident_type}", error=str(e))
        finally:
            if simulation_id in self._active_simulations:
                del self._active_simulations[simulation_id]

    async def _simulate_cpu_spike(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        pod_name = f"api-server-{random.randint(0, 3)}"
        severity_value = self._map_severity(config.severity)

        while datetime.utcnow() < end_time:
            cpu_percent = 50 + (random.random() * 45) if config.severity == SimulationSeverity.HIGH else 75 + (random.random() * 25)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value,
                payload={
                    "pod_name": pod_name,
                    "anomaly_type": "cpu_spike",
                    "cpu_percent": cpu_percent,
                    "threshold": 80,
                    "duration_seconds": 5,
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_memory_leak(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        pod_name = f"app-{random.randint(0, 2)}"
        severity_value = self._map_severity(config.severity)
        memory_percent = 30.0

        while datetime.utcnow() < end_time:
            memory_percent += random.uniform(3, 8)
            memory_percent = min(memory_percent, 95)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value if memory_percent > 80 else Severity.WARNING,
                payload={
                    "pod_name": pod_name,
                    "anomaly_type": "memory_leak",
                    "memory_percent": memory_percent,
                    "growth_rate": 5.0,
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_pvc_saturation(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        pod_name = f"database-{random.randint(0, 1)}"
        pvc_name = f"data-{pod_name}"
        severity_value = self._map_severity(config.severity)

        for i in range(config.duration_seconds // 5):
            if datetime.utcnow() > end_time:
                break

            usage_percent = 60 + (i * 3)
            usage_percent = min(usage_percent, 99)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value if usage_percent > 85 else Severity.WARNING,
                payload={
                    "pod_name": pod_name,
                    "pvc_name": pvc_name,
                    "anomaly_type": "pvc_saturation",
                    "usage_percent": usage_percent,
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_network_latency(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        severity_value = self._map_severity(config.severity)

        while datetime.utcnow() < end_time:
            latency_ms = 50 + random.uniform(100, 500) if config.severity == SimulationSeverity.CRITICAL else 20 + random.uniform(50, 200)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value,
                payload={
                    "anomaly_type": "network_latency",
                    "latency_ms": latency_ms,
                    "threshold_ms": 100,
                    "affected_services": ["api-gateway", "backend-service"],
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_packet_loss(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        severity_value = self._map_severity(config.severity)

        while datetime.utcnow() < end_time:
            packet_loss_percent = 0.5 + random.uniform(1, 5) if config.severity == SimulationSeverity.HIGH else 0.1 + random.uniform(0.5, 2)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value,
                payload={
                    "anomaly_type": "packet_loss",
                    "packet_loss_percent": packet_loss_percent,
                    "affected_nodes": ["node-1", "node-2"],
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_pod_restart_storm(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        severity_value = self._map_severity(config.severity)
        service = random.choice(["api", "worker", "cache"])

        while datetime.utcnow() < end_time:
            restart_count = random.randint(3, 10)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value,
                payload={
                    "anomaly_type": "pod_restart_storm",
                    "service": service,
                    "restart_count": restart_count,
                    "time_window_seconds": 60,
                    "affected_pods": restart_count,
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_crashloop_backoff(self, simulation_id: str, config: SimulationConfig) -> None:
        pod_name = f"service-{random.randint(0, 4)}"
        severity_value = self._map_severity(config.severity)

        event = BaseEvent(
            cluster_id="default",
            namespace=config.namespace,
            event_type=EventType.ANOMALY,
            severity=severity_value,
            payload={
                "pod_name": pod_name,
                "anomaly_type": "crashloop_backoff",
                "restart_count": 5,
                "reason": "CrashLoopBackOff",
                "simulation_id": simulation_id,
            },
        )
        await self._bus.publisher.publish_to_enriched(event)
        self._active_simulations[simulation_id]["events_generated"] += 1

    async def _simulate_dependency_failure(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        failed_service = random.choice(["database", "redis", "kafka"])
        severity_value = self._map_severity(config.severity)

        while datetime.utcnow() < end_time:
            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value,
                payload={
                    "anomaly_type": "dependency_failure",
                    "failed_service": failed_service,
                    "error_rate": random.uniform(50, 100),
                    "affected_downstream": ["api", "worker", "web"],
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_database_bottleneck(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        severity_value = self._map_severity(config.severity)

        while datetime.utcnow() < end_time:
            query_time_ms = 100 + random.uniform(500, 2000) if config.severity == SimulationSeverity.CRITICAL else 50 + random.uniform(100, 500)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value,
                payload={
                    "anomaly_type": "database_bottleneck",
                    "query_latency_ms": query_time_ms,
                    "connection_pool_utilization": random.uniform(70, 95),
                    "slow_queries": random.randint(5, 20),
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _simulate_api_gateway_congestion(self, simulation_id: str, config: SimulationConfig) -> None:
        end_time = datetime.utcnow() + timedelta(seconds=config.duration_seconds)
        severity_value = self._map_severity(config.severity)

        while datetime.utcnow() < end_time:
            request_rate = 1000 + random.uniform(5000, 20000) if config.severity == SimulationSeverity.CRITICAL else 500 + random.uniform(1000, 5000)

            event = BaseEvent(
                cluster_id="default",
                namespace=config.namespace,
                event_type=EventType.ANOMALY,
                severity=severity_value,
                payload={
                    "anomaly_type": "api_gateway_congestion",
                    "request_rate_per_sec": request_rate,
                    "error_rate": random.uniform(0.1, 10),
                    "p99_latency_ms": random.uniform(500, 5000),
                    "simulation_id": simulation_id,
                },
            )
            await self._bus.publisher.publish_to_enriched(event)
            self._active_simulations[simulation_id]["events_generated"] += 1
            await asyncio.sleep(5)

    async def _trigger_cascades(self, simulation_id: str, config: SimulationConfig) -> None:
        await asyncio.sleep(config.duration_seconds / 2)

        for target in config.cascade_targets or []:
            cascade_config = SimulationConfig(
                incident_type=random.choice(list(IncidentType)),
                severity=SimulationSeverity.HIGH,
                namespace=config.namespace,
                pod_pattern=target,
                duration_seconds=config.duration_seconds // 2,
                cascade_enabled=False,
            )
            await self.start_simulation(cascade_config)

    def get_active_simulations(self) -> list[dict]:
        result = []
        for sim_id, sim_data in self._active_simulations.items():
            result.append({
                "simulation_id": sim_id,
                "incident_type": sim_data["config"].incident_type.value,
                "severity": sim_data["config"].severity.value,
                "namespace": sim_data["config"].namespace,
                "started_at": sim_data["started_at"].isoformat(),
                "events_generated": sim_data["events_generated"],
            })
        return result

    def _map_severity(self, sim_severity: SimulationSeverity) -> Severity:
        mapping = {
            SimulationSeverity.LOW: Severity.INFO,
            SimulationSeverity.MEDIUM: Severity.WARNING,
            SimulationSeverity.HIGH: Severity.ERROR,
            SimulationSeverity.CRITICAL: Severity.CRITICAL,
        }
        return mapping.get(sim_severity, Severity.WARNING)
