import asyncio
import json
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.core.database import async_session_maker
from sentinelops.services.topology_service import TopologyService

DEFAULT_CLUSTER_ID = UUID("00000000-0000-0000-0000-000000000001")

async def seed():
    async with async_session_maker() as session:
        service = TopologyService(session)
        
        nodes = []
        edges = []
        
        # Create core services
        core_services = ["api-gateway", "payment-service", "auth-service", "catalog-service", "inventory-service", "database", "redis-cache"]
        
        for name in core_services:
            nodes.append({
                "id": f"default:Service:{name}",
                "namespace": "default",
                "kind": "Service",
                "name": name,
                "health": "healthy"
            })
        
        # Create 500 pods
        for i in range(500):
            svc = core_services[i % len(core_services)]
            pod_name = f"{svc}-{i}"
            nodes.append({
                "id": f"default:Pod:{pod_name}",
                "namespace": "default",
                "kind": "Pod",
                "name": pod_name,
                "health": "healthy"
            })
            # Connect pod to service
            edges.append({
                "source": f"default:Pod:{pod_name}",
                "target": f"default:Service:{svc}",
                "edge_type": "belongs_to",
                "confidence": 1.0
            })
            
        # Connect services to each other
        edges.extend([
            {"source": "default:Service:api-gateway", "target": "default:Service:auth-service", "edge_type": "depends_on", "confidence": 0.9},
            {"source": "default:Service:api-gateway", "target": "default:Service:payment-service", "edge_type": "depends_on", "confidence": 0.9},
            {"source": "default:Service:api-gateway", "target": "default:Service:catalog-service", "edge_type": "depends_on", "confidence": 0.9},
            {"source": "default:Service:payment-service", "target": "default:Service:database", "edge_type": "depends_on", "confidence": 0.9},
            {"source": "default:Service:catalog-service", "target": "default:Service:redis-cache", "edge_type": "depends_on", "confidence": 0.9},
            {"source": "default:Service:catalog-service", "target": "default:Service:database", "edge_type": "depends_on", "confidence": 0.9},
            {"source": "default:Service:inventory-service", "target": "default:Service:database", "edge_type": "depends_on", "confidence": 0.9},
        ])
        
        snapshot_json = {
            "nodes": nodes,
            "edges": edges,
        }
        
        await service.create_version_snapshot(DEFAULT_CLUSTER_ID, snapshot_json)
        await session.commit()
        print(f"Successfully seeded topology with {len(nodes)} nodes and {len(edges)} edges.")

if __name__ == "__main__":
    asyncio.run(seed())
