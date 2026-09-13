"""
Retrieval Evaluation Engine for SentinelOps AI RAG System.
Measures Precision@K, Recall@K, Mean Reciprocal Rank (MRR), and retrieval latency
across relevant, irrelevant, duplicate, conflicting, and empty knowledge bases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, List, Optional

from sentinelops.rag.vector_store import PersistentVectorStore
from sentinelops.rag.embeddings import BaseEmbeddingProvider


@dataclass
class RetrievalBenchmarkQuery:
    query: str
    expected_doc_ids: list[str]
    category: str = "standard"  # standard, irrelevant, conflict, malicious, empty


@dataclass
class QueryRetrievalResult:
    query: str
    k: int
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float
    latency_ms: float
    retrieved_doc_ids: list[str] = field(default_factory=list)


@dataclass
class RetrievalBenchmarkSummary:
    total_queries: int
    mean_precision_at_k: float
    mean_recall_at_k: float
    mean_reciprocal_rank: float  # MRR
    p50_latency_ms: float
    p95_latency_ms: float
    query_results: list[QueryRetrievalResult] = field(default_factory=list)


class RetrievalEvaluator:
    """Evaluates vector search quality and ranking metrics."""

    @classmethod
    async def evaluate_query(
        cls,
        vector_store: PersistentVectorStore,
        benchmark: RetrievalBenchmarkQuery,
        k: int = 3,
    ) -> QueryRetrievalResult:
        start_time = time.perf_counter()
        matches = await vector_store.search(benchmark.query, top_k=k, min_score=0.0)
        latency_ms = (time.perf_counter() - start_time) * 1000

        retrieved_ids = [m.document_id for m in matches]
        expected_set = set(benchmark.expected_doc_ids)
        retrieved_set = set(retrieved_ids[:k])

        # Compute Precision@K and Recall@K
        if not expected_set and not retrieved_set:
            p_at_k = 1.0
            r_at_k = 1.0
        elif not expected_set:
            p_at_k = 0.0
            r_at_k = 1.0
        else:
            tp = len(retrieved_set.intersection(expected_set))
            p_at_k = tp / k if k > 0 else 0.0
            r_at_k = tp / len(expected_set)

        # Compute Reciprocal Rank
        rr = 0.0
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in expected_set:
                rr = 1.0 / rank
                break

        return QueryRetrievalResult(
            query=benchmark.query,
            k=k,
            precision_at_k=p_at_k,
            recall_at_k=r_at_k,
            reciprocal_rank=rr,
            latency_ms=latency_ms,
            retrieved_doc_ids=retrieved_ids,
        )

    @classmethod
    async def run_benchmark_suite(
        cls,
        vector_store: PersistentVectorStore,
        benchmarks: list[RetrievalBenchmarkQuery],
        k: int = 3,
    ) -> RetrievalBenchmarkSummary:
        results: list[QueryRetrievalResult] = []
        for b in benchmarks:
            res = await cls.evaluate_query(vector_store, b, k=k)
            results.append(res)

        n = len(results)
        if n == 0:
            return RetrievalBenchmarkSummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, [])

        mean_p = sum(r.precision_at_k for r in results) / n
        mean_r = sum(r.recall_at_k for r in results) / n
        mrr = sum(r.reciprocal_rank for r in results) / n

        latencies = sorted(r.latency_ms for r in results)
        p50 = latencies[int(n * 0.50)]
        p95 = latencies[int(n * 0.95)] if n > 1 else latencies[0]

        return RetrievalBenchmarkSummary(
            total_queries=n,
            mean_precision_at_k=mean_p,
            mean_recall_at_k=mean_r,
            mean_reciprocal_rank=mrr,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            query_results=results,
        )
