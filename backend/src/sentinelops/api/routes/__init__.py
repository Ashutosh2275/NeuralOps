from fastapi import APIRouter

from sentinelops.api.routes.health import router as health_router
from sentinelops.api.routes.incidents import router as incidents_router
from sentinelops.api.routes.ingestion import router as ingestion_router
from sentinelops.api.routes.intelligence import router as intelligence_router
from sentinelops.api.routes.nlp import router as nlp_router
from sentinelops.api.routes.topology import router as topology_router
from sentinelops.api.routes.demo import router as demo_router
from sentinelops.api.routes.phase13 import router as phase13_router
from sentinelops.api.routes.predictive import router as predictive_router
from sentinelops.api.routes.chaos import router as chaos_router
from sentinelops.api.routes.investigations import router as investigations_router
from sentinelops.api.routes.knowledge import router as knowledge_router
from sentinelops.api.routes.system import router as system_router
from sentinelops.api.routes.workloads import router as workloads_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(incidents_router, prefix="/incidents", tags=["incidents"])
api_router.include_router(topology_router, prefix="/topology", tags=["topology"])
api_router.include_router(nlp_router, prefix="/nlp", tags=["nlp"])
api_router.include_router(ingestion_router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(intelligence_router, prefix="/intelligence", tags=["intelligence"])
api_router.include_router(demo_router, tags=["demo"])
api_router.include_router(phase13_router, tags=["phase13"])
api_router.include_router(predictive_router, tags=["predictive"])
api_router.include_router(chaos_router, tags=["chaos"])
api_router.include_router(investigations_router, prefix="/investigations", tags=["investigations"])
api_router.include_router(workloads_router, tags=["workloads"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(system_router, tags=["system"])
