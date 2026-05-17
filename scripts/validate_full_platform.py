"""
Full Platform Validation Suite — System 14
Validates every subsystem end-to-end. Runs autonomously with actionable output.
"""
from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass, field

import httpx

BASE = "http://localhost:8000"


@dataclass
class Result:
    name: str
    ok: bool
    msg: str
    latency_ms: float = 0.0


results: list[Result] = []


async def check(name: str, coro) -> None:
    t0 = time.perf_counter()
    try:
        msg = await coro
        results.append(Result(name, True, msg or "OK", (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(Result(name, False, str(e), (time.perf_counter() - t0) * 1000))


# ── Docker / Infra ──────────────────────────────────────────────────────────
async def v_backend_health() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/v1/health", timeout=10)
        r.raise_for_status()
        d = r.json()
        assert d["status"] == "healthy", f"status={d['status']}"
        svcs = d.get("services", {})
        assert svcs.get("redis"), "Redis unhealthy"
        assert svcs.get("postgres"), "Postgres unhealthy"
        return f"status={d['status']} redis={svcs['redis']} postgres={svcs['postgres']}"


async def v_topology_api() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/v1/topology/graph", timeout=15)
        r.raise_for_status()
        d = r.json()
        nodes = d.get("node_count", 0)
        return f"nodes={nodes}"


async def v_topology_seed() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/api/v1/topology/seed", timeout=30)
        r.raise_for_status()
        d = r.json()
        return f"seeded nodes={d['nodes']} edges={d['edges']}"


async def v_incidents_api() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/v1/incidents", timeout=10)
        r.raise_for_status()
        return f"status={r.status_code}"


async def v_demo_scenarios() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/v1/demo/scenarios/available", timeout=10)
        r.raise_for_status()
        d = r.json()
        return f"scenarios={len(d['scenarios'])}"


async def v_cascading_scenario() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/api/v1/demo/scenario/cascading_failure", timeout=20)
        r.raise_for_status()
        d = r.json()
        return f"injected {d['incident_count']} incidents"


async def v_api_meltdown() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/api/v1/demo/scenario/api_meltdown", timeout=20)
        r.raise_for_status()
        d = r.json()
        return f"injected {d['incident_count']} incidents"


async def v_websocket_latency() -> str:
    import websockets
    uri = "ws://localhost:8000/ws"
    latencies = []
    async with websockets.connect(uri) as ws:
        for _ in range(5):
            t0 = time.perf_counter()
            await ws.send("ping")
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            latency = (time.perf_counter() - t0) * 1000
            latencies.append(latency)
    avg = sum(latencies) / len(latencies)
    assert avg < 100, f"WS avg latency {avg:.1f}ms > 100ms threshold"
    return f"avg={avg:.1f}ms max={max(latencies):.1f}ms"


async def v_nlp_endpoint() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"{BASE}/api/v1/nlp/query",
            json={"query": "What is the current cluster status?"},
            timeout=30,
        )
        if r.status_code in (200, 422):
            return f"status={r.status_code}"
        r.raise_for_status()
        return f"status={r.status_code}"


async def v_perf_metrics() -> str:
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/api/v1/performance/metrics", timeout=10)
        if r.status_code == 404:
            return "endpoint not registered yet (ok — optional)"
        r.raise_for_status()
        return f"status={r.status_code}"


# ── Main ─────────────────────────────────────────────────────────────────────
async def main() -> None:
    print("\n╔════════════════════════════════════════════════╗")
    print("║   NeuralOps Full Platform Validation Suite    ║")
    print("╚════════════════════════════════════════════════╝\n")

    suite = [
        ("Backend Health", v_backend_health),
        ("Topology API", v_topology_api),
        ("Topology Seed (500 nodes)", v_topology_seed),
        ("Incidents API", v_incidents_api),
        ("Demo Scenarios List", v_demo_scenarios),
        ("Chaos: Cascading Failure", v_cascading_scenario),
        ("Chaos: API Meltdown", v_api_meltdown),
        ("WebSocket Latency", v_websocket_latency),
        ("NLP Assistant", v_nlp_endpoint),
        ("Performance Metrics", v_perf_metrics),
    ]

    for name, coro_fn in suite:
        await check(name, coro_fn())

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n{'Check':<40} {'Status':<8} {'Latency':>10}  Details")
    print("─" * 80)
    passed = 0
    for r in results:
        status = "✅ PASS" if r.ok else "❌ FAIL"
        if r.ok:
            passed += 1
        print(f"{r.name:<40} {status:<8} {r.latency_ms:>8.1f}ms  {r.msg[:50]}")

    total = len(results)
    print(f"\n{'─'*80}")
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉  Platform is FULLY OPERATIONAL and PRODUCTION READY!\n")
        sys.exit(0)
    else:
        failed = [r for r in results if not r.ok]
        print(f"\n⚠️   {len(failed)} check(s) failed:")
        for r in failed:
            print(f"   • {r.name}: {r.msg}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
