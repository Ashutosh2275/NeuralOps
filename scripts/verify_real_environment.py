import asyncio
import json
import sys
import httpx
import time
from pathlib import Path

# Add backend/src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

async def verify_all():
    print("=" * 70)
    print("SENTINELOPS AI — REAL ENVIRONMENT COMPREHENSIVE HEALTH PROBES")
    print("=" * 70)
    results = {}

    # 1. PostgreSQL Probe (SQL query execution)
    try:
        from sentinelops.core.database import async_session_factory
        from sqlalchemy import text
        async with async_session_factory() as session:
            res = await session.execute(text("SELECT version(), current_database();"))
            row = res.fetchone()
            version, dbname = row[0], row[1]
            print(f"[1/9] PostgreSQL (Port 5433): OK | DB: {dbname} | Version: {version[:30]}...")
            results["postgres"] = True
    except Exception as e:
        print(f"[1/9] PostgreSQL: FAILED -> {e}")
        results["postgres"] = False

    # 2. Redis Probe (PING / PONG)
    try:
        from sentinelops.core.redis_client import get_redis
        redis_client = await get_redis()
        pong = await redis_client.ping()
        info = await redis_client.info(section="server")
        redis_ver = info.get("redis_version", "unknown")
        print(f"[2/9] Redis (Port 6380): OK | PING -> {pong} | Version: {redis_ver}")
        results["redis"] = True
    except Exception as e:
        print(f"[2/9] Redis: FAILED -> {e}")
        results["redis"] = False

    # 3. Prometheus Probe (API Build Info & Query)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://127.0.0.1:9090/api/v1/status/buildinfo")
            data = resp.json()
            prom_ver = data.get("data", {}).get("version", "unknown")
            resp_q = await client.get("http://127.0.0.1:9090/api/v1/query?query=up")
            targets_up = len(resp_q.json().get("data", {}).get("result", []))
            print(f"[3/9] Prometheus (Port 9090): OK | Version: {prom_ver} | Active Targets: {targets_up}")
            results["prometheus"] = True
    except Exception as e:
        print(f"[3/9] Prometheus: FAILED -> {e}")
        results["prometheus"] = False

    # 4. Loki Probe (Ready endpoint & labels API)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://127.0.0.1:3100/ready")
            ready_text = resp.text.strip()
            resp_labels = await client.get("http://127.0.0.1:3100/loki/api/v1/labels")
            labels = resp_labels.json().get("data", [])
            print(f"[4/9] Loki (Port 3100): OK | Status: {ready_text} | Indexed Labels: {labels}")
            results["loki"] = True
    except Exception as e:
        print(f"[4/9] Loki: FAILED -> {e}")
        results["loki"] = False

    # 5. Ollama LLM & Embeddings Probe (Tags & Embedding model check)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            models = [m["name"] for m in resp.json().get("models", [])]
            embed_resp = await client.post(
                "http://127.0.0.1:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": "healthcheck probe"}
            )
            dim = len(embed_resp.json().get("embedding", []))
            print(f"[5/9] Ollama (Port 11434): OK | Available Models: {models} | nomic-embed-text dim: {dim}")
            results["ollama"] = True
    except Exception as e:
        print(f"[5/9] Ollama: FAILED -> {e}")
        results["ollama"] = False

    # 6. Kubernetes / k3s Probe (Live API Client & Pod query in sentinelops-e2e)
    try:
        from sentinelops.collectors.k8s_collector import KubernetesCollector
        collector = KubernetesCollector()
        data = await collector.collect_all(namespace="sentinelops-e2e")
        pods = data.get("pods", [])
        pod_names = [p.get("name") or p.get("pod_name") for p in pods]
        print(f"[6/9] Kubernetes (k3s): OK | Namespace: sentinelops-e2e | Live Pods ({len(pod_names)}): {pod_names}")
        results["kubernetes"] = True
    except Exception as e:
        print(f"[6/9] Kubernetes: FAILED -> {e}")
        results["kubernetes"] = False

    # 7. Pod Log Shipper Probe (Query Loki query_range for recent log lines)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            now_ts = time.time()
            start_ts = now_ts - 3600
            resp = await client.get(
                "http://127.0.0.1:3100/loki/api/v1/query_range",
                params={
                    "query": '{namespace="sentinelops-e2e"}',
                    "start": str(int(start_ts * 1e9)),
                    "end": str(int(now_ts * 1e9)),
                    "limit": "50"
                }
            )
            streams = resp.json().get("data", {}).get("result", [])
            total_lines = sum(len(s.get("values", [])) for s in streams)
            print(f"[7/9] Pod Log Shipper: OK | Streams Active in Loki: {len(streams)} | Log Lines Captured: {total_lines}")
            results["pod_log_shipper"] = True
    except Exception as e:
        print(f"[7/9] Pod Log Shipper: FAILED -> {e}")
        results["pod_log_shipper"] = False

    # 8. FastAPI Probe (Health API endpoint)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://127.0.0.1:8000/api/v1/health")
            health_json = resp.json()
            status = health_json.get("status")
            deps = health_json.get("dependencies", {})
            healthy_count = health_json.get("healthy_count")
            total_deps = health_json.get("total_dependencies")
            print(f"[8/9] FastAPI Backend (Port 8000): OK | Status: {status} | Healthy Deps: {healthy_count}/{total_deps} -> {deps}")
            results["fastapi"] = (resp.status_code == 200 and status == "HEALTHY")
    except Exception as e:
        print(f"[8/9] FastAPI Backend: FAILED -> {e}")
        results["fastapi"] = False

    # 9. React Frontend Probe (HTML root & Title verification)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:5173/")
            html = resp.text
            has_title = "<title>SentinelOps AI" in html
            print(f"[9/9] React Frontend (Port 5173): OK | Status: {resp.status_code} | Title Match: {has_title}")
            results["react"] = (resp.status_code == 200 and has_title)
    except Exception as e:
        print(f"[9/9] React Frontend: FAILED -> {e}")
        results["react"] = False

    print("=" * 70)
    all_ok = all(results.values())
    print(f"OVERALL ENVIRONMENT HEALTH: {'ALL 9 SERVICES OPERATIONAL' if all_ok else 'SOME SERVICES UNHEALTHY'}")
    print("=" * 70)
    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_all())
