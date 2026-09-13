"""Scale and performance benchmark test for SentinelOps AI RAG vector store."""
from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
import time
import pytest
import numpy as np

from sentinelops.rag.chunker import DocumentMetadata, OperationalDocumentChunker
from sentinelops.rag.embeddings import DeterministicFallbackEmbeddingProvider
from sentinelops.rag.engine import RAGEngine
from sentinelops.rag.vector_store import PersistentVectorStore


@pytest.fixture
def temp_perf_dir():
    temp_dir = tempfile.mkdtemp(prefix="sentinelops_perf_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestRAGScaleAndPerformance:
    """Evaluates indexing throughput, query latency, and high concurrency."""

    @pytest.mark.asyncio
    async def test_indexing_and_query_benchmark(self, temp_perf_dir):
        db_path = os.path.join(temp_perf_dir, "perf_vectors.db")
        provider = DeterministicFallbackEmbeddingProvider(dimension=256)
        store = PersistentVectorStore(storage_path=db_path, embedding_provider=provider)
        chunker = OperationalDocumentChunker(target_chunk_size=1000)

        # 1. Generate 100 realistic operational documents
        docs = []
        services = ["auth", "payment", "checkout", "order", "notification", "inventory", "search", "shipping", "user", "api-gw"]
        failure_modes = ["crashloop", "oomkilled", "pvc-full", "net-latency", "connection-pool-exhausted"]

        for i in range(100):
            svc = services[i % len(services)]
            f_mode = failure_modes[i % len(failure_modes)]
            meta = DocumentMetadata(
                document_id=f"doc-scale-{i}",
                title=f"Runbook for {svc}-service {f_mode} incident",
                source=f"runbooks/{svc}/{f_mode}.md",
                document_type="runbook",
                service=f"{svc}-service",
                namespace="production",
            )
            content = f"""# {svc.capitalize()} Service {f_mode.capitalize()} Runbook

## Symptoms & Triage
The {svc}-service microservice has triggered alert {f_mode} at severity critical.
Pod restarts incremented past threshold with latency spikes on downstream dependencies.

## Immediate Action
```bash
kubectl describe pod -l app={svc}-service -n production
kubectl logs deploy/{svc}-service -n production --tail=200
kubectl rollout restart deploy/{svc}-service -n production
```

## Post-Incident Diagnostics
Check connection pool limits and verify database capacity.
"""
            docs.append((meta, content))

        # Chunk documents
        all_chunks = []
        for meta, content in docs:
            chunks = chunker.chunk_document(content, meta)
            all_chunks.extend(chunks)

        total_chunks = len(all_chunks)
        assert total_chunks >= 100

        # 2. Benchmark Indexing Throughput
        start_idx = time.perf_counter()
        indexed_count = await store.upsert_chunks(all_chunks, provider)
        idx_duration = time.perf_counter() - start_idx

        indexing_throughput = indexed_count / idx_duration if idx_duration > 0 else 0
        assert store.count() == total_chunks

        # 3. Benchmark Query Latency across 50 concurrent queries
        queries = [
            f"How to fix {services[i % len(services)]}-service {failure_modes[i % len(failure_modes)]} issue?"
            for i in range(50)
        ]

        latencies = []
        start_queries = time.perf_counter()

        async def run_query(q: str):
            t0 = time.perf_counter()
            res = await store.search(q, top_k=3, min_score=0.1)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)  # ms
            return res

        query_tasks = [run_query(q) for q in queries]
        query_results = await asyncio.gather(*query_tasks)
        total_query_duration = time.perf_counter() - start_queries

        p50 = float(np.percentile(latencies, 50))
        p95 = float(np.percentile(latencies, 95))
        p99 = float(np.percentile(latencies, 99))
        qps = len(queries) / total_query_duration if total_query_duration > 0 else 0

        # Assertions on retrieval accuracy and latency
        assert all(len(r) > 0 for r in query_results)
        assert p95 < 200.0  # P95 query latency under 200ms
        assert qps > 10.0   # Throughput > 10 QPS