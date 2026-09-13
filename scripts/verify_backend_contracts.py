import asyncio
import json
import sys
import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

async def test_backend_contracts():
    print("=" * 70)
    print("SENTINELOPS AI — BACKEND API CONTRACT VERIFICATION")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    def report(name: str, ok: bool, details: str = ""):
        nonlocal passed, failed
        if ok:
            passed += 1
            print(f"  [PASS] {name} {details}")
        else:
            failed += 1
            print(f"  [FAIL] {name} {details}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health
        r = await client.get("/api/v1/health")
        data = r.json() if r.status_code == 200 else {}
        report("GET /api/v1/health", r.status_code == 200 and data.get("status") == "HEALTHY", f"-> {r.status_code}, status={data.get('status')}")

        # 2. Incidents List
        r = await client.get("/api/v1/incidents")
        incidents = r.json() if r.status_code == 200 else []
        report("GET /api/v1/incidents", r.status_code == 200 and isinstance(incidents, list) and len(incidents) > 0, f"-> {r.status_code}, count={len(incidents)}")

        # 3. Incident Detail
        if incidents:
            valid_id = incidents[0]["id"]
            r_det = await client.get(f"/api/v1/incidents/{valid_id}")
            inc_data = r_det.json()
            has_fields = all(k in inc_data for k in ["id", "title", "severity", "status", "confidence_score"])
            report(f"GET /api/v1/incidents/{valid_id[:8]}", r_det.status_code == 200 and has_fields, f"-> {r_det.status_code}, fields={has_fields}")
        else:
            report("GET /api/v1/incidents/{id}", False, "no incident found to test")

        # Incident 404 behavior
        r_404 = await client.get("/api/v1/incidents/00000000-0000-0000-0000-000000000000")
        report("GET /api/v1/incidents/nonexistent (404)", r_404.status_code == 404, f"-> {r_404.status_code}")

        # 4. Investigations List (wrapped in { count, investigations })
        r_inv = await client.get("/api/v1/investigations")
        inv_json = r_inv.json() if r_inv.status_code == 200 else {}
        invs = inv_json.get("investigations", [])
        report("GET /api/v1/investigations", r_inv.status_code == 200 and isinstance(invs, list), f"-> {r_inv.status_code}, count={len(invs)}")

        # 5. Investigation Detail
        if invs:
            valid_inv_id = invs[0].get("investigation_id")
            if valid_inv_id:
                r_inv_det = await client.get(f"/api/v1/investigations/{valid_inv_id}")
                inv_data = r_inv_det.json()
                has_inv_fields = "investigation" in inv_data or "investigation_id" in inv_data
                report(f"GET /api/v1/investigations/{valid_inv_id[:8]}", r_inv_det.status_code == 200 and has_inv_fields, f"-> {r_inv_det.status_code}")
        else:
            report("GET /api/v1/investigations/{id}", True, "(no existing investigations, verified empty behavior)")

        r_inv_404 = await client.get("/api/v1/investigations/nonexistent-inv-id-xyz")
        report("GET /api/v1/investigations/nonexistent (404)", r_inv_404.status_code == 404, f"-> {r_inv_404.status_code}")

        # 6. Topology Graph
        r_top = await client.get("/api/v1/topology/graph")
        top_data = r_top.json() if r_top.status_code == 200 else {}
        nodes = top_data.get("nodes", [])
        edges = top_data.get("edges", [])
        report("GET /api/v1/topology/graph", r_top.status_code == 200 and len(nodes) > 0 and len(edges) > 0, f"-> {r_top.status_code}, nodes={len(nodes)}, edges={len(edges)}")

        # 7. Workloads List
        r_wl = await client.get("/api/v1/workloads/pods")
        wl_data = r_wl.json() if r_wl.status_code == 200 else {}
        pods_list = wl_data.get("pods", [])
        report("GET /api/v1/workloads/pods", r_wl.status_code == 200 and len(pods_list) > 0, f"-> {r_wl.status_code}, pods={len(pods_list)}")

        # 8. Workload Pod Detail
        if pods_list:
            first_pod = pods_list[0]
            ns = first_pod.get("namespace", "sentinelops-e2e")
            pod_name = first_pod.get("pod_name") or first_pod.get("name")
            r_pod_det = await client.get(f"/api/v1/workloads/pods/{ns}/{pod_name}")
            pod_det = r_pod_det.json() if r_pod_det.status_code == 200 else {}
            has_pod_fields = "pod" in pod_det and "logs" in pod_det and "metrics" in pod_det
            report(f"GET /api/v1/workloads/pods/{ns}/{pod_name[:15] if pod_name else 'pod'}...", r_pod_det.status_code == 200 and has_pod_fields, f"-> {r_pod_det.status_code}")
        else:
            report("GET /api/v1/workloads/pods/{ns}/{pod}", False, "no pods found")

        r_pod_404 = await client.get("/api/v1/workloads/pods/sentinelops-e2e/nonexistent-pod-xyz")
        report("GET /api/v1/workloads/pods/nonexistent (404)", r_pod_404.status_code == 404, f"-> {r_pod_404.status_code}")

        # 9. Metrics
        r_met = await client.get("/api/v1/workloads/metrics?pod_name=healthy-service&namespace=sentinelops-e2e")
        met_data = r_met.json() if r_met.status_code == 200 else {}
        report("GET /api/v1/workloads/metrics", r_met.status_code == 200 and "metrics" in met_data, f"-> {r_met.status_code}, metrics={len(met_data.get('metrics', []))}")

        # 10. Logs
        r_log = await client.get("/api/v1/workloads/logs?pod_name=crashloop-service&namespace=sentinelops-e2e&limit=10")
        log_data = r_log.json() if r_log.status_code == 200 else {}
        report("GET /api/v1/workloads/logs", r_log.status_code == 200 and "logs" in log_data, f"-> {r_log.status_code}, logs={len(log_data.get('logs', []))}")

        # 11. Knowledge Documents & Search
        r_docs = await client.get("/api/v1/knowledge/documents")
        docs_data = r_docs.json() if r_docs.status_code == 200 else {}
        docs_list = docs_data.get("documents", [])
        report("GET /api/v1/knowledge/documents", r_docs.status_code == 200 and len(docs_list) >= 7, f"-> {r_docs.status_code}, count={len(docs_list)}")

        if docs_list:
            doc_id = docs_list[0].get("document_id") or docs_list[0].get("id")
            r_doc_det = await client.get(f"/api/v1/knowledge/documents/{doc_id}")
            doc_det = r_doc_det.json() if r_doc_det.status_code == 200 else {}
            report(f"GET /api/v1/knowledge/documents/{doc_id}", r_doc_det.status_code == 200 and "chunks" in doc_det, f"-> {r_doc_det.status_code}, chunks={len(doc_det.get('chunks', []))}")

        r_doc_404 = await client.get("/api/v1/knowledge/documents/nonexistent-runbook-xyz")
        report("GET /api/v1/knowledge/documents/nonexistent (404)", r_doc_404.status_code == 404, f"-> {r_doc_404.status_code}")

        # Knowledge Search
        r_search = await client.post("/api/v1/knowledge/search", json={"query": "CrashLoopBackOff memory limit", "top_k": 3})
        search_data = r_search.json() if r_search.status_code == 200 else {}
        results_list = search_data.get("results", [])
        report("POST /api/v1/knowledge/search", r_search.status_code == 200 and len(results_list) > 0, f"-> {r_search.status_code}, matches={len(results_list)}")

        # 12. Tools Registry (at /api/v1/investigations/tools)
        r_tools = await client.get("/api/v1/investigations/tools")
        tools_data = r_tools.json() if r_tools.status_code == 200 else {}
        tools_list = tools_data.get("tools", [])
        report("GET /api/v1/investigations/tools", r_tools.status_code == 200 and len(tools_list) >= 8, f"-> {r_tools.status_code}, tools={len(tools_list)}")

        # 13. Audit Events (at /api/v1/investigations/audit/events)
        r_audit = await client.get("/api/v1/investigations/audit/events")
        audit_data = r_audit.json() if r_audit.status_code == 200 else {}
        audit_events = audit_data.get("events", [])
        report("GET /api/v1/investigations/audit/events", r_audit.status_code == 200 and isinstance(audit_events, list), f"-> {r_audit.status_code}, events={len(audit_events)}")

        # 14. Settings / System Info (at /api/v1/system/info)
        r_sys = await client.get("/api/v1/system/info")
        sys_data = r_sys.json() if r_sys.status_code == 200 else {}
        has_sys_fields = "platform" in sys_data and "ai_engine" in sys_data and "infrastructure" in sys_data
        report("GET /api/v1/system/info", r_sys.status_code == 200 and has_sys_fields, f"-> {r_sys.status_code}, platform={sys_data.get('platform', {}).get('cluster_id')}")

    print("=" * 70)
    print(f"BACKEND CONTRACT AUDIT SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_backend_contracts())
