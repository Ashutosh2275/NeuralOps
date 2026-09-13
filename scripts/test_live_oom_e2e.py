import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
from sentinelops.investigation.engine import InvestigationEngine

async def main():
    print("=================================================================")
    print("PHASE 7: REAL OOMKILLED INCIDENT INVESTIGATION TRACE")
    print("=================================================================")

    engine = InvestigationEngine()
    import httpx
    try:
        r = httpx.get("http://127.0.0.1:8000/api/v1/workloads/pods")
        pods = r.json().get("pods", [])
        oom_pod = next((p["pod_name"] for p in pods if "oom-service" in p["pod_name"]), "oom-service")
    except Exception:
        oom_pod = "oom-service"

    state = await engine.investigate(
        incident_id="LIVE-INC-OOM-002",
        target_service="oom-service",
        target_pod=oom_pod,
        namespace="sentinelops-e2e",
        trigger_reason="Alert: Workload memory pressure threshold breached",
        max_steps=5,
    )

    print(f"Investigation ID: {state.investigation_id}")
    print(f"Status: {state.status}")
    print(f"Steps executed: {state.step_count}")
    print("\n--- Executed Tool History ---")
    for call in state.tool_history:
        print(f"Tool: {call.tool_name} | Args: {call.arguments}")

    print("\n--- Gathered Evidence Items ---")
    for ev in state.evidence:
        print(f"[{ev.evidence_type.value}] ({ev.source_tool}): {ev.summary}")

    print("\n--- Formulated Hypotheses ---")
    for h in state.hypotheses:
        print(f"Hypothesis: {h.description} | Status: {h.status.value} | Confidence: {h.confidence}")

    print(f"\nFinal Root Cause: {state.final_root_cause}")
    print(f"Overall Confidence: {state.confidence}")
    print(f"Facts: {state.epistemic_breakdown.get('facts')}")
    print(f"Inferences: {state.epistemic_breakdown.get('inferences')}")

    assert state.step_count > 0, "No tools were executed"
    assert any("oom" in h.description.lower() or "memory" in h.description.lower() for h in state.hypotheses), "OOM hypothesis not generated"
    print("\n[SUCCESS] LIVE OOM INCIDENT INVESTIGATION SUCCESSFULLY PROVEN!")

if __name__ == "__main__":
    asyncio.run(main())
