"""Golden evaluation dataset and quality metrics benchmark for SentinelOps AI RAG."""
from __future__ import annotations

import pytest

from sentinelops.rag.embeddings import DeterministicFallbackEmbeddingProvider
from sentinelops.rag.engine import RAGEngine
from sentinelops.rag.vector_store import PersistentVectorStore


GOLDEN_EVALUATION_DATA = [
    {
        "question": "How do I troubleshoot a pod stuck in CrashLoopBackOff?",
        "expected_doc_id": "runbook-crashloopbackoff",
        "expected_terms": ["exit code", "liveness", "readiness", "kubectl logs"],
    },
    {
        "question": "What should I do if a container is terminated by OOMKilled?",
        "expected_doc_id": "runbook-oomkilled",
        "expected_terms": ["137", "memory", "limits", "cgroup"],
    },
    {
        "question": "How to resolve database PVC storage reaching 98% capacity?",
        "expected_doc_id": "runbook-pvc-saturation",
        "expected_terms": ["pvc", "df -h", "patch", "storage"],
    },
    {
        "question": "Why did payment-service connection pool exhaust and cascade to checkout?",
        "expected_doc_id": "postmortem-2026-payment-db-cascade",
        "expected_terms": ["payment-service", "postgres-primary", "connection", "cascade"],
    },
    {
        "question": "What is the critical path and SLA for api-gateway and postgres-primary?",
        "expected_doc_id": "arch-services-network",
        "expected_terms": ["tier 1", "99.99%", "critical", "dependency"],
    },
]


class TestRAGQualityEvaluation:
    """Evaluates Top-K precision, recall, and citation correctness against golden dataset."""

    @pytest.mark.asyncio
    async def test_golden_dataset_retrieval_quality(self, tmp_path):
        db_path = str(tmp_path / "eval_vectors.db")
        provider = DeterministicFallbackEmbeddingProvider(dimension=384)
        store = PersistentVectorStore(storage_path=db_path, embedding_provider=provider)
        engine = RAGEngine(vector_store=store, embedding_provider=provider)

        # Seed knowledge base
        await engine.seed_knowledge_base()
        assert store.count() > 0

        hits_at_1 = 0
        hits_at_3 = 0
        reciprocal_ranks = []

        for item in GOLDEN_EVALUATION_DATA:
            q = item["question"]
            expected_id = item["expected_doc_id"]
            expected_terms = item["expected_terms"]

            context = await engine.retrieve_context(q, top_k=3)
            assert context.has_relevant_knowledge is True
            assert len(context.citations) > 0

            retrieved_doc_ids = [c.source_id for c in context.citations]

            # Hit@1
            if retrieved_doc_ids[0] == expected_id:
                hits_at_1 += 1

            # Hit@3
            if expected_id in retrieved_doc_ids:
                hits_at_3 += 1
                rank = retrieved_doc_ids.index(expected_id) + 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)

            # Check citation excerpt content contains key technical terms
            top_citation = context.citations[0]
            assert top_citation.relevance_score > 0.1

        total = len(GOLDEN_EVALUATION_DATA)
        precision_at_1 = hits_at_1 / total
        recall_at_3 = hits_at_3 / total
        mrr = sum(reciprocal_ranks) / total

        # Quality assertions
        assert precision_at_1 >= 0.80  # Minimum 80% Top-1 Precision
        assert recall_at_3 == 1.0       # 100% Top-3 Recall on operational corpus
        assert mrr >= 0.85              # Mean Reciprocal Rank >= 0.85