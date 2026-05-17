from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID

from sentinelops.simulator.incident_simulator import IncidentSimulator, SimulationConfig, IncidentType, SimulationSeverity
from sentinelops.self_healing.engine import SelfHealingEngine
from sentinelops.services.incident_generator import create_incident_from_scenario
from sentinelops.core.logging import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])

_simulator: IncidentSimulator = None
_healing_engine: SelfHealingEngine = None


def get_simulator() -> IncidentSimulator:
    global _simulator
    if not _simulator:
        _simulator = IncidentSimulator()
    return _simulator


def get_healing_engine() -> SelfHealingEngine:
    global _healing_engine
    if not _healing_engine:
        _healing_engine = SelfHealingEngine()
    return _healing_engine


class IncidentTriggerRequest(BaseModel):
    incident_type: str
    severity: str = "high"
    namespace: str = "default"
    duration_seconds: int = 60
    cascade_enabled: bool = False


class DemoScenarioRequest(BaseModel):
    scenario_name: str
    namespace: str = "demo"


@router.post("/incident/trigger")
async def trigger_incident(request: IncidentTriggerRequest):
    try:
        simulator = get_simulator()
        await simulator.initialize()

        incident_type = IncidentType(request.incident_type)
        severity = SimulationSeverity(request.severity)

        config = SimulationConfig(
            incident_type=incident_type,
            severity=severity,
            namespace=request.namespace,
            duration_seconds=request.duration_seconds,
            cascade_enabled=request.cascade_enabled,
        )

        simulation_id = await simulator.start_simulation(config)
        log.info(f"incident_triggered_{incident_type.value}", simulation_id=simulation_id)

        return {
            "status": "success",
            "simulation_id": simulation_id,
            "incident_type": incident_type.value,
            "severity": severity.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid incident type or severity: {str(e)}")
    except Exception as e:
        log.error("incident_trigger_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents/active")
async def get_active_incidents():
    simulator = get_simulator()
    return {"active_incidents": simulator.get_active_simulations()}


@router.post("/scenario/{scenario_name}")
async def trigger_demo_scenario(scenario_name: str, namespace: str = "demo"):
    scenarios = {
        "ecommerce_checkout": [
            {
                "incident_type": IncidentType.CPU_SPIKE.value,
                "severity": "high",
                "duration_seconds": 60,
            },
            {
                "incident_type": IncidentType.DEPENDENCY_FAILURE.value,
                "severity": "critical",
                "duration_seconds": 45,
                "delay_seconds": 20,
            },
        ],
        "database_saturation": [
            {
                "incident_type": IncidentType.DATABASE_BOTTLENECK.value,
                "severity": "critical",
                "duration_seconds": 120,
            },
        ],
        "api_meltdown": [
            {
                "incident_type": IncidentType.API_GATEWAY_CONGESTION.value,
                "severity": "critical",
                "duration_seconds": 90,
            },
            {
                "incident_type": IncidentType.NETWORK_LATENCY.value,
                "severity": "high",
                "duration_seconds": 60,
                "delay_seconds": 15,
            },
        ],
        "cascading_failure": [
            {
                "incident_type": IncidentType.MEMORY_LEAK.value,
                "severity": "high",
                "duration_seconds": 120,
            },
            {
                "incident_type": IncidentType.POD_RESTART_STORM.value,
                "severity": "high",
                "duration_seconds": 90,
                "delay_seconds": 30,
            },
            {
                "incident_type": IncidentType.DEPENDENCY_FAILURE.value,
                "severity": "critical",
                "duration_seconds": 60,
                "delay_seconds": 60,
            },
        ],
        "kubernetes_exhaustion": [
            {
                "incident_type": IncidentType.PVC_SATURATION.value,
                "severity": "critical",
                "duration_seconds": 90,
            },
            {
                "incident_type": IncidentType.POD_RESTART_STORM.value,
                "severity": "high",
                "duration_seconds": 60,
                "delay_seconds": 20,
            },
        ],
    }

    if scenario_name not in scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_name} not found")

    simulator = get_simulator()
    await simulator.initialize()

    simulation_ids = []
    for i, incident in enumerate(scenarios[scenario_name]):
        delay = incident.get("delay_seconds", 0)
        config = SimulationConfig(
            incident_type=IncidentType(incident["incident_type"]),
            severity=SimulationSeverity(incident["severity"]),
            namespace=namespace,
            duration_seconds=incident["duration_seconds"],
            start_delay_seconds=delay,
            cascade_enabled=False,
        )
        sim_id = await simulator.start_simulation(config)
        simulation_ids.append(sim_id)

    await create_incident_from_scenario(scenario_name)

    return {
        "status": "success",
        "scenario": scenario_name,
        "simulation_ids": simulation_ids,
        "incident_count": len(scenarios[scenario_name]),
    }


@router.get("/scenarios/available")
async def get_available_scenarios():
    scenarios = [
        {
            "name": "ecommerce_checkout",
            "description": "E-Commerce checkout failure with CPU spike and dependency cascade",
            "estimated_duration": 90,
        },
        {
            "name": "database_saturation",
            "description": "Database connection pool exhaustion",
            "estimated_duration": 120,
        },
        {
            "name": "api_meltdown",
            "description": "API gateway congestion with network latency",
            "estimated_duration": 120,
        },
        {
            "name": "cascading_failure",
            "description": "Memory leak leading to cascade of pod restarts and service failure",
            "estimated_duration": 180,
        },
        {
            "name": "kubernetes_exhaustion",
            "description": "Kubernetes resource exhaustion (PVC + pod restart storm)",
            "estimated_duration": 120,
        },
    ]
    return {"scenarios": scenarios}


@router.get("/remediation/actions")
async def get_remediation_actions():
    healing_engine = get_healing_engine()
    return {"executed_actions": healing_engine.get_executed_actions()}
