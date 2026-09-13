"""Demo quickstart — seeds data and fires chaos demo automatically."""
from __future__ import annotations

import asyncio
import httpx

BASE = "http://localhost:8000"


async def main() -> None:
    print("🚀  NetraAI Demo Quickstart")
    print("   Warming up infrastructure... Injecting chaos simulation...")

    async with httpx.AsyncClient() as c:
        # Seed topology
        try:
            r = await c.post(f"{BASE}/api/v1/topology/seed", timeout=30)
            if r.status_code == 200:
                d = r.json()
                print(f"   ✅  Topology seeded: {d['nodes']} nodes, {d['edges']} edges")
        except Exception as e:
            print(f"   ⚠️   Topology seed failed: {e}")

        # Fire all demo scenarios
        for scenario in ["cascading_failure", "api_meltdown", "ecommerce_checkout"]:
            try:
                r = await c.post(f"{BASE}/api/v1/demo/scenario/{scenario}", timeout=20)
                if r.status_code == 200:
                    d = r.json()
                    print(f"   🔥  Scenario '{scenario}' fired: {d['incident_count']} incidents")
            except Exception as e:
                print(f"   ⚠️   {scenario}: {e}")

    print("\n   ✅  Judge demo ready. Real-time command center active.")
    print("   Open: http://localhost:5173/command-center")


if __name__ == "__main__":
    asyncio.run(main())
