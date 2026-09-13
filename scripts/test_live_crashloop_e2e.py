import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))
from sentinelops.investigation.engine import InvestigationEngine

async def main():
    print("=================================================================")
    print("PHASE 7: REAL CRASHLOOP INCIDENT INVESTIGATION TRACE")
    print("=================================================================")

    engine = InvestigationEngine()
    import httpx
    try:
        r = httpx.get("http://127.0.0.1:8000/api/v1/workloads/pods")
        pods = r.json().get("pods", [])
        crashloop_pod = next((p["pod_name"] for p in pods if "crashloop-service" in p["pod_name"]), "crashloop-service")
    except Exception:
        crashloop_pod = "crashloop-service"

    # Trigger investigation WITHOUT hardcoding the root cause in trigger
    state = await engine.investigate(
        incident_id="LIVE-INC-CRASHLOOP-001",
        target_service="crashloop-service",
        target_pod=crashloop_pod,
        namespace="sentinelops-e2e",
        trigger_reason="Alert: Service transaction errors surging",
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
        if ev.source_tool == "get_pod_logs":
            print(f"   Logs snippet: {str(ev.raw_data.get('logs', ''))[:120]}...")

    print("\n--- Formulated Hypotheses ---")
    for h in state.hypotheses:
        print(f"Hypothesis: {h.description} | Status: {h.status.value} | Confidence: {h.confidence}")

    print(f"\nFinal Root Cause: {state.final_root_cause}")
    print(f"Overall Confidence: {state.confidence}")
    print(f"Facts: {state.epistemic_breakdown.get('facts')}")
    print(f"Inferences: {state.epistemic_breakdown.get('inferences')}")

    # Validate that live CrashLoop was autonomously discovered from the cluster
    assert state.step_count > 0, "No tools were executed"
    assert any("crashloop" in h.description.lower() for h in state.hypotheses), "CrashLoop hypothesis not generated from live cluster state"
    assert any("bind port 8080" in str(e.raw_data) for e in state.evidence), "Actual container log from cluster not captured"
    print("\n[SUCCESS] LIVE CRASHLOOP INCIDENT INVESTIGATION SUCCESSFULLY PROVEN!")

if __name__ == "__main__":
    asyncio.run(main())
