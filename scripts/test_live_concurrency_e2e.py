"""
Test Concurrent Live Investigations with Zero Cross-Contamination.
"""
import asyncio
import time
from sentinelops.investigation.engine import InvestigationEngine


async def run_one(engine: InvestigationEngine, idx: int):
    svc_name = f"service-{idx:02d}"
    trigger = f"Service degradation and intermittent 500s on {svc_name}"
    start = time.perf_counter()
    state = await engine.investigate(
        target_service=svc_name,
        namespace="production",
        trigger_reason=trigger,
        max_steps=4,
    )
    elapsed = time.perf_counter() - start
    assert state.target_service == svc_name
    assert state.initial_trigger == trigger
    assert state.status == "completed"
    return {
        "idx": idx,
        "id": state.investigation_id,
        "service": state.target_service,
        "status": state.status,
        "tools": len(state.tool_history),
        "duration": elapsed,
    }


async def test_concurrency(count: int = 10):
    print(f"\n--- Testing {count} Concurrent Autonomous Investigations ---")
    engine = InvestigationEngine()
    t0 = time.perf_counter()
    tasks = [run_one(engine, i) for i in range(count)]
    results = await asyncio.gather(*tasks)
    total_time = time.perf_counter() - t0

    # Verify state isolation
    inv_ids = set()
    for r in results:
        assert r["id"] not in inv_ids, f"Duplicate investigation ID detected: {r['id']}"
        inv_ids.add(r["id"])
        print(f"  Investigation [{r['idx']:02d}] {r['id']} for {r['service']}: status={r['status']}, tools={r['tools']}, time={r['duration']:.2f}s")

    print(f"\nAll {count} investigations completed successfully in {total_time:.2f}s!")
    print(f"Zero cross-contamination verified across {len(inv_ids)} distinct investigation states.")


if __name__ == "__main__":
    asyncio.run(test_concurrency(10))
