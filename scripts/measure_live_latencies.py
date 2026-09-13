"""
Measure Latency Profiles (P50, P95, P99) for all Live Components.
"""
import asyncio
import time
import numpy as np
import httpx
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def bench_postgres(n=20):
    engine = create_async_engine("postgresql+asyncpg://sentinelops:sentinelops@127.0.0.1:5433/sentinelops")
    latencies = []
    async with engine.connect() as conn:
        for _ in range(n):
            t0 = time.perf_counter()
            await conn.execute(text("SELECT 1;"))
            latencies.append((time.perf_counter() - t0) * 1000.0)
    await engine.dispose()
    return np.percentile(latencies, 50), np.percentile(latencies, 95), np.percentile(latencies, 99)


async def bench_redis(n=20):
    r = aioredis.Redis(host="127.0.0.1", port=6380, db=0)
    latencies = []
    for _ in range(n):
        t0 = time.perf_counter()
        await r.ping()
        latencies.append((time.perf_counter() - t0) * 1000.0)
    await r.aclose()
    return np.percentile(latencies, 50), np.percentile(latencies, 95), np.percentile(latencies, 99)


async def bench_prometheus(n=20):
    url = "http://127.0.0.1:9090/api/v1/query?query=up"
    latencies = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for _ in range(n):
            t0 = time.perf_counter()
            resp = await client.get(url)
            assert resp.status_code == 200
            latencies.append((time.perf_counter() - t0) * 1000.0)
    return np.percentile(latencies, 50), np.percentile(latencies, 95), np.percentile(latencies, 99)


async def bench_loki(n=20):
    url = "http://127.0.0.1:3100/loki/api/v1/query_range?query={app=\"payment-service\"}"
    latencies = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for _ in range(n):
            t0 = time.perf_counter()
            resp = await client.get(url)
            assert resp.status_code == 200
            latencies.append((time.perf_counter() - t0) * 1000.0)
    return np.percentile(latencies, 50), np.percentile(latencies, 95), np.percentile(latencies, 99)


async def bench_ollama_embedding(n=10):
    url = "http://127.0.0.1:11434/api/embeddings"
    latencies = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(n):
            t0 = time.perf_counter()
            resp = await client.post(url, json={"model": "nomic-embed-text", "prompt": "Kubernetes troubleshooting runbook"})
            assert resp.status_code == 200
            latencies.append((time.perf_counter() - t0) * 1000.0)
    return np.percentile(latencies, 50), np.percentile(latencies, 95), np.percentile(latencies, 99)


async def bench_ollama_llm(n=5):
    url = "http://127.0.0.1:11434/api/generate"
    latencies = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for _ in range(n):
            t0 = time.perf_counter()
            resp = await client.post(url, json={"model": "llama3.2", "prompt": "Respond with OK", "stream": False})
            assert resp.status_code == 200
            latencies.append((time.perf_counter() - t0) * 1000.0)
    return np.percentile(latencies, 50), np.percentile(latencies, 95), np.percentile(latencies, 99)


async def main():
    print("Benchmarking live components...")
    pg50, pg95, pg99 = await bench_postgres()
    rd50, rd95, rd99 = await bench_redis()
    pr50, pr95, pr99 = await bench_prometheus()
    lk50, lk95, lk99 = await bench_loki()
    em50, em95, em99 = await bench_ollama_embedding()
    lm50, lm95, lm99 = await bench_ollama_llm()

    print("\n| Component | P50 (ms) | P95 (ms) | P99 (ms) |")
    print("|---|---|---|---|")
    print(f"| PostgreSQL 18 (Async Query) | {pg50:.2f} | {pg95:.2f} | {pg99:.2f} |")
    print(f"| Redis 5.0.14.1 (Ping) | {rd50:.2f} | {rd95:.2f} | {rd99:.2f} |")
    print(f"| Prometheus v3.14 (PromQL API) | {pr50:.2f} | {pr95:.2f} | {pr99:.2f} |")
    print(f"| Loki v3.7 (Range Query API) | {lk50:.2f} | {lk95:.2f} | {lk99:.2f} |")
    print(f"| Ollama nomic-embed-text (CUDA) | {em50:.2f} | {em95:.2f} | {em99:.2f} |")
    print(f"| Ollama llama3.2 LLM (CUDA) | {lm50:.2f} | {lm95:.2f} | {lm99:.2f} |")


if __name__ == "__main__":
    asyncio.run(main())
