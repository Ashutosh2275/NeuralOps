"""
Startup Orchestrator — System 15
Single entry-point to boot the entire NeuralOps stack.
Preloads Ollama model, seeds topology, warms AI agents.
"""
from __future__ import annotations

import asyncio
import sys
import httpx

BASE = "http://localhost:8000"
OLLAMA = "http://localhost:11434"


async def wait_for(url: str, label: str, timeout: int = 60) -> bool:
    print(f"  ⏳  Waiting for {label}...", end="", flush=True)
    async with httpx.AsyncClient() as client:
        for _ in range(timeout):
            try:
                r = await client.get(url, timeout=3)
                if r.status_code < 500:
                    print(" ✅")
                    return True
            except Exception:
                pass
            await asyncio.sleep(1)
    print(" ❌ TIMEOUT")
    return False


async def seed_topology() -> None:
    print("  🗺️   Seeding 500-node topology...", end="", flush=True)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{BASE}/api/v1/topology/seed", timeout=30)
            if r.status_code == 200:
                d = r.json()
                print(f" ✅  {d['nodes']} nodes / {d['edges']} edges")
            else:
                print(f" ⚠️   {r.status_code}")
        except Exception as e:
            print(f" ⚠️   {e}")


async def trigger_demo_scenario() -> None:
    print("  🔥  Triggering cascading_failure scenario...", end="", flush=True)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(f"{BASE}/api/v1/demo/scenario/cascading_failure", timeout=20)
            if r.status_code == 200:
                d = r.json()
                print(f" ✅  {d['incident_count']} incidents injected")
            else:
                print(f" ⚠️   {r.status_code}: {r.text[:80]}")
        except Exception as e:
            print(f" ⚠️   {e}")


async def check_health() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/api/v1/health", timeout=10)
        return r.json()


async def main() -> None:
    print("\n╔══════════════════════════════════════════╗")
    print("║   NeuralOps Startup Orchestrator v1.0   ║")
    print("╚══════════════════════════════════════════╝\n")

    checks = [
        (f"{BASE}/api/v1/health", "Backend API"),
        (f"{OLLAMA}/api/tags", "Ollama Inference"),
    ]

    all_ok = True
    for url, label in checks:
        ok = await wait_for(url, label)
        if not ok:
            all_ok = False

    if not all_ok:
        print("\n❌  Some services unavailable. Check docker compose logs.")
        sys.exit(1)

    health = await check_health()
    print(f"\n  📊  Health: {health}")

    await seed_topology()
    await trigger_demo_scenario()

    print("\n╔══════════════════════════════════════════╗")
    print("║   🚀  NeuralOps Platform is READY!       ║")
    print("║   Frontend → http://localhost:5173       ║")
    print("║   Backend  → http://localhost:8000       ║")
    print("║   API Docs → http://localhost:8000/docs  ║")
    print("╚══════════════════════════════════════════╝\n")


if __name__ == "__main__":
    asyncio.run(main())
