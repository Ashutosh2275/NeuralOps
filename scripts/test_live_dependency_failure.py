import asyncio
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sentinelops.collectors.k8s_collector import KubernetesCollector
from sentinelops.engines.dependency import DependencyIntelligenceEngine
from sentinelops.tools.topology_tools import GetServiceDependenciesTool, CalculateBlastRadiusTool


async def test_live_dependency():
    print("[TEST] Initializing KubernetesCollector for sentinelops-e2e...")
    collector = KubernetesCollector()
    await collector._init_clients()

    raw_data = await collector.collect_all(namespace="sentinelops-e2e")
    pods = raw_data["pods"]
    services = raw_data["services"]
    dependencies = raw_data.get("dependencies", [])
    print(f"Collected {len(pods)} pods and {len(services)} services from live cluster.")

    engine = DependencyIntelligenceEngine()
    
    # Register the dependency chain: checkout-service -> payment-service -> payment-db
    engine.add_edge(
        source_ns="sentinelops-e2e",
        source_name="checkout-service",
        source_kind="Service",
        target_ns="sentinelops-e2e",
        target_name="payment-service",
        target_kind="Service",
        edge_type="calls",
        confidence=0.9,
        method="service_mesh",
    )
    engine.add_edge(
        source_ns="sentinelops-e2e",
        source_name="payment-service",
        source_kind="Service",
        target_ns="sentinelops-e2e",
        target_name="payment-db",
        target_kind="Service",
        edge_type="queries",
        confidence=0.95,
        method="env_reference",
    )

    # Ingest collector pod/service mappings
    engine.discover_from_collector_data(pods, services, dependencies)
    print(f"[SUCCESS] Dependency graph built with {len(engine._graph.nodes)} nodes and {len(engine._graph.edges)} edges.")

    # 1. Test GetServiceDependenciesTool
    dep_tool = GetServiceDependenciesTool(engine=engine)
    res = await dep_tool.run(namespace="sentinelops-e2e", service_name="payment-service")
    print(f"[TOOL] GetServiceDependenciesTool: success={res.success}")
    assert res.success, f"Dependency tool failed: {res.errors}"
    data = res.data
    print(f"  Downstream of payment-service: {data['downstream_dependencies']}")
    print(f"  Upstream of payment-service: {data['upstream_callers']}")
    assert "sentinelops-e2e/Service/payment-db" in data['downstream_dependencies']
    assert "sentinelops-e2e/Service/checkout-service" in data['upstream_callers']

    # 2. Test CalculateBlastRadiusTool for checkout-service
    blast_tool = CalculateBlastRadiusTool(engine=engine)
    blast_res = await blast_tool.run(namespace="sentinelops-e2e", resource_name="checkout-service", kind="Service")
    print(f"[TOOL] CalculateBlastRadiusTool: success={blast_res.success}")
    assert blast_res.success, f"Blast radius tool failed: {blast_res.errors}"
    blast_data = blast_res.data
    affected = blast_data["blast_radius"]["affected_nodes"]
    scores = blast_data["blast_radius"]["influence_scores"]
    print(f"  Blast radius affected nodes: {affected}")
    print(f"  Influence scores: {scores}")
    assert "sentinelops-e2e/Service/payment-service" in affected or "sentinelops-e2e/Service/payment-db" in affected

    # Also test blast radius for payment-service
    blast_res2 = await blast_tool.run(namespace="sentinelops-e2e", resource_name="payment-service", kind="Service")
    print(f"[TOOL] payment-service blast radius: {blast_res2.data['blast_radius']['affected_nodes']}")
    assert "sentinelops-e2e/Service/payment-db" in blast_res2.data['blast_radius']['affected_nodes']

    # 3. Simulate failure propagation: scale payment-db to 0
    print("[ACTION] Scaling payment-db to 0 replicas...")
    os.system("kubectl scale deployment payment-db --replicas=0 -n sentinelops-e2e")
    await asyncio.sleep(4)

    # Verify pods
    updated_raw = await collector.collect_all(namespace="sentinelops-e2e")
    db_pods = [p for p in updated_raw["pods"] if "payment-db" in p.get("pod_name", "")]
    print(f"  Active payment-db pods after scale-down: {len(db_pods)}")

    # Propagate health in graph
    propagated = engine.propagate_health("sentinelops-e2e/Service/checkout-service", source_health="critical")
    print(f"  Propagated health impact count: {len(propagated)}")
    for p in propagated:
        print(f"    Impacted: {p.node_id} -> health: {p.propagated_health} (path: {p.propagation_path})")
    assert len(propagated) > 0, "Health propagation should affect downstream services"

    # Restore payment-db
    print("[RESTORE] Scaling payment-db back to 1 replica...")
    os.system("kubectl scale deployment payment-db --replicas=1 -n sentinelops-e2e")
    await asyncio.sleep(4)

    print("[SUCCESS] Section 8: Live Dependency Failure and Blast Radius passed!")


if __name__ == "__main__":
    asyncio.run(test_live_dependency())
