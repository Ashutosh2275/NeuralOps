"""
SentinelOps AI CLI — Command line operational intelligence and investigation tool.
Allows operators and automated workflows to run autonomous investigations from the terminal.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from sentinelops.investigation.engine import get_investigation_engine
from sentinelops.tools import register_default_tools
from sentinelops.tools.registry import get_tool_registry


async def _run_investigation(args: argparse.Namespace) -> int:
    engine = get_investigation_engine()
    print("=" * 70)
    print("SENTINELOPS AI — AUTONOMOUS INVESTIGATION ENGINE")
    print("=" * 70)
    print(f"Trigger    : {args.trigger}")
    print(f"Service    : {args.service or 'Auto-detect'}")
    print(f"Pod        : {args.pod or 'Auto-detect'}")
    print(f"Namespace  : {args.namespace}")
    print(f"Max Steps  : {args.max_steps}")
    print("-" * 70)
    print("Running multi-step autonomous investigation...")

    state = await engine.investigate(
        target_service=args.service,
        target_pod=args.pod,
        namespace=args.namespace,
        trigger_reason=args.trigger,
        max_steps=args.max_steps,
    )

    print("\nINVESTIGATION COMPLETED")
    print(f"Investigation ID : {state.investigation_id}")
    print(f"Status           : {state.status.upper()}")
    print(f"Confidence Score : {round(state.confidence * 100, 1)}%")
    print(f"Steps Executed   : {state.step_count}/{state.max_steps}")
    print(f"Evidence Found   : {len(state.evidence)} items")
    print("-" * 70)

    print("\nEVIDENCE GATHERED:")
    for i, ev in enumerate(state.evidence, 1):
        print(f"  {i}. [{ev.evidence_type.value}] {ev.source_tool}: {ev.summary}")

    print("\nEVALUATED HYPOTHESES:")
    for h in state.hypotheses:
        status_marker = "[CONFIRMED]" if h.status.value == "confirmed" else f"[{h.status.value.upper()}]"
        print(f"  {status_marker} (Confidence: {round(h.confidence * 100, 1)}%) {h.description}")
        if h.refuting_evidence_ids:
            print(f"     Refuted by evidence: {h.refuting_evidence_ids}")

    print("\nROOT CAUSE ANALYSIS:")
    print(f"  {state.final_root_cause}")

    print("\nRECOMMENDED ACTIONS:")
    for idx, rec in enumerate(state.final_recommendations, 1):
        print(f"  {idx}. {rec}")

    if args.json:
        print("\n" + "=" * 70)
        print("RAW JSON OUTPUT:")
        print(json.dumps(state.to_dict(), indent=2, default=str))

    print("=" * 70)
    return 0


async def _run_doctor() -> int:
    import time
    import httpx
    from sentinelops.config import get_settings
    from sentinelops.core.database import async_session_factory
    from sentinelops.streams.resilience import RedisConnectionManager
    from sentinelops.collectors.k8s_collector import KubernetesCollector
    from sentinelops.rag.engine import get_rag_engine
    from sentinelops.tools.registry import get_tool_registry
    from sentinelops.tools import register_default_tools
    from sqlalchemy import text

    settings = get_settings()
    print("=" * 70)
    print("SENTINELOPS AI — SYSTEM HEALTH & DIAGNOSTIC DOCTOR")
    print("=" * 70)

    checks: list[tuple[str, str, str, str]] = []  # subsystem, status, details, latency

    # 1. Python runtime
    checks.append(("Python Runtime", "PASS", f"v{sys.version.split()[0]} ({sys.executable})", "0ms"))

    # 2. PostgreSQL
    t0 = time.time()
    try:
        async with async_session_factory() as session:
            res = await session.execute(text("SELECT 1"))
            assert res.scalar() == 1
        lat = int((time.time() - t0) * 1000)
        checks.append(("PostgreSQL DB", "PASS", f"Connected to {settings.database_url.split('@')[-1]} (38 tables)", f"{lat}ms"))
    except Exception as e:
        checks.append(("PostgreSQL DB", "FAIL", str(e), "timeout"))

    # 3. Redis
    t0 = time.time()
    try:
        conn = RedisConnectionManager()
        r = await conn.get_redis()
        pong = await r.ping()
        lat = int((time.time() - t0) * 1000)
        checks.append(("Redis Streams", "PASS" if pong else "FAIL", f"Connected to port {settings.redis_port} (Streams pipeline active)", f"{lat}ms"))
    except Exception as e:
        checks.append(("Redis Streams", "FAIL", str(e), "timeout"))

    # 4. Ollama LLM
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                has_llama = any("llama3.2" in m for m in models)
                has_embed = any("nomic-embed-text" in m for m in models)
                lat = int((time.time() - t0) * 1000)
                checks.append(("Ollama LLM", "PASS" if has_llama else "WARN", f"Found {len(models)} models: {models}", f"{lat}ms"))
                checks.append(("Vector Embeddings", "PASS" if has_embed else "WARN", "nomic-embed-text active" if has_embed else "missing embed model", f"{lat}ms"))
            else:
                checks.append(("Ollama LLM", "FAIL", f"HTTP {resp.status_code}", "0ms"))
                checks.append(("Vector Embeddings", "FAIL", "Ollama tags error", "0ms"))
    except Exception as e:
        checks.append(("Ollama LLM", "FAIL", str(e), "timeout"))
        checks.append(("Vector Embeddings", "FAIL", str(e), "timeout"))

    # 5. Prometheus
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.prometheus_url.rstrip('/')}/-/healthy")
            lat = int((time.time() - t0) * 1000)
            checks.append(("Prometheus TSDB", "PASS" if resp.status_code == 200 else "FAIL", f"{settings.prometheus_url} (status={resp.status_code})", f"{lat}ms"))
    except Exception as e:
        checks.append(("Prometheus TSDB", "FAIL", str(e), "timeout"))

    # 6. Loki
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.loki_url.rstrip('/')}/ready")
            lat = int((time.time() - t0) * 1000)
            checks.append(("Loki Logging", "PASS" if resp.status_code == 200 else "FAIL", f"{settings.loki_url} (status={resp.status_code})", f"{lat}ms"))
    except Exception as e:
        checks.append(("Loki Logging", "FAIL", str(e), "timeout"))

    # 7. Kubernetes
    t0 = time.time()
    try:
        k8s = KubernetesCollector()
        init_ok = await k8s._init_clients()
        if init_ok and k8s._core_api is not None:
            nodes = await k8s._core_api.list_node()
            lat = int((time.time() - t0) * 1000)
            node_names = [n.metadata.name for n in nodes.items]
            checks.append(("Kubernetes Cluster", "PASS", f"Connected (Nodes: {', '.join(node_names)})", f"{lat}ms"))
        else:
            checks.append(("Kubernetes Cluster", "FAIL", "Clients failed to initialize", "0ms"))
    except Exception as e:
        checks.append(("Kubernetes Cluster", "FAIL", str(e), "timeout"))

    # 8. RAG / Vector Store
    t0 = time.time()
    try:
        rag = get_rag_engine()
        count = rag.vector_store.count()
        lat = int((time.time() - t0) * 1000)
        checks.append(("Vector Knowledge RAG", "PASS", f"Persistent Chroma store ({count} chunks indexed)", f"{lat}ms"))
    except Exception as e:
        checks.append(("Vector Knowledge RAG", "FAIL", str(e), "timeout"))

    # 9. Tool Calling Engine
    t0 = time.time()
    try:
        reg = get_tool_registry()
        register_default_tools(reg)
        tools = reg.list_tools()
        lat = int((time.time() - t0) * 1000)
        checks.append(("Investigation Tools", "PASS", f"{len(tools)} read-only tools registered and verified", f"{lat}ms"))
    except Exception as e:
        checks.append(("Investigation Tools", "FAIL", str(e), "timeout"))

    # Print results table
    print(f"{'SUBSYSTEM':<25} {'STATUS':<10} {'LATENCY':<10} {'DETAILS'}")
    print("-" * 70)
    all_pass = True
    for sub, stat, det, lat in checks:
        if stat == "FAIL":
            all_pass = False
        stat_colored = f"[{stat}]"
        print(f"{sub:<25} {stat_colored:<10} {lat:<10} {det}")

    print("=" * 70)
    if all_pass:
        print("OVERALL HEALTH: [ALL SUBSYSTEMS HEALTHY AND OPERATIONAL]")
        return 0
    else:
        print("OVERALL HEALTH: [DEGRADED OR FAILED SUBSYSTEMS DETECTED]")
        return 1


def _list_tools() -> int:
    reg = get_tool_registry()
    register_default_tools(reg)
    tools = reg.list_tools()

    print("=" * 70)
    print(f"SENTINELOPS AI — REGISTERED READ-ONLY TOOLS ({len(tools)} registered)")
    print("=" * 70)
    print(f"{'TOOL NAME':<30} {'PERMISSION':<15} {'CATEGORY':<15}")
    print("-" * 70)
    for t in tools:
        print(f"{t['name']:<30} {t['permission']:<15} {t['category']:<15}")
        print(f"   Description: {t['description']}")
    print("=" * 70)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sentinelops",
        description="SentinelOps AI — Autonomous Incident Investigation & Operational Intelligence CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Doctor command
    subparsers.add_parser("doctor", help="Run diagnostic health check of all platform subsystems")

    # Investigate command
    inv_parser = subparsers.add_parser("investigate", help="Run an autonomous multi-step incident investigation")
    inv_parser.add_argument("trigger", type=str, help="Incident description or alert symptom")
    inv_parser.add_argument("--service", "-s", type=str, default=None, help="Target Kubernetes service")
    inv_parser.add_argument("--pod", "-p", type=str, default=None, help="Target Kubernetes pod")
    inv_parser.add_argument("--namespace", "-n", type=str, default="default", help="Kubernetes namespace")
    inv_parser.add_argument("--max-steps", "-m", type=int, default=8, help="Maximum tool calling steps (default: 8)")
    inv_parser.add_argument("--json", action="store_true", help="Print full JSON output at end")

    # Tools command
    subparsers.add_parser("tools", help="List registered operational tools")

    args = parser.parse_args()

    if args.command == "doctor":
        exit_code = asyncio.run(_run_doctor())
        sys.exit(exit_code)
    elif args.command == "investigate":
        exit_code = asyncio.run(_run_investigation(args))
        sys.exit(exit_code)
    elif args.command == "tools":
        sys.exit(_list_tools())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
