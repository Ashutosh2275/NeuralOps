"""
Phase 4 Test Suite: Evaluation Framework, Golden Dataset, and Groundedness.
Tests 20 golden operational scenarios, tool selection metrics, Brier score calibration,
groundedness classification, hallucination detection, and RAG retrieval quality.
"""
import pytest

from sentinelops.evaluation.dataset import GOLDEN_SCENARIOS, get_scenario_by_id
from sentinelops.evaluation.metrics import MetricsEvaluator, ScenarioEvaluationMetric
from sentinelops.evaluation.groundedness import GroundednessEvaluator, ClaimType
from sentinelops.evaluation.retrieval_eval import (
    RetrievalBenchmarkQuery,
    RetrievalEvaluator,
)


def test_golden_dataset_structure_and_completeness():
    """Verify all 20 required golden operational scenarios exist with valid schemas."""
    assert len(GOLDEN_SCENARIOS) == 20

    scenario_ids = [s.scenario_id for s in GOLDEN_SCENARIOS]
    assert len(scenario_ids) == len(set(scenario_ids)), "Duplicate scenario IDs detected"

    for s in GOLDEN_SCENARIOS:
        assert s.scenario_id.startswith("GS-")
        assert len(s.name) > 0
        assert len(s.target_service) > 0
        assert len(s.expected_tools) > 0
        assert len(s.expected_root_cause_keywords) > 0
        assert len(s.expected_affected_services) > 0
        assert 0.0 <= s.min_confidence <= 1.0


def test_tool_selection_and_calibration_metrics():
    """Test quantitative evaluation metrics (Precision, Recall, F1, Brier score)."""
    # Perfect selection
    p, r, f1, unnec = MetricsEvaluator.evaluate_tool_selection(
        selected_tools=["k8s_get_pod_status", "k8s_get_pod_logs"],
        expected_tools=["k8s_get_pod_status", "k8s_get_pod_logs"],
    )
    assert p == 1.0 and r == 1.0 and f1 == 1.0 and unnec == 0

    # Partial selection with unnecessary tool
    p, r, f1, unnec = MetricsEvaluator.evaluate_tool_selection(
        selected_tools=["k8s_get_pod_status", "unrelated_tool"],
        expected_tools=["k8s_get_pod_status", "k8s_get_pod_logs"],
    )
    assert p == 0.5
    assert r == 0.5
    assert unnec == 1

    # Calibration error
    brier_correct = MetricsEvaluator.evaluate_calibration(confidence=0.9, is_correct=True)
    assert round(brier_correct, 4) == 0.0100  # (0.9 - 1.0)^2 = 0.01

    brier_wrong = MetricsEvaluator.evaluate_calibration(confidence=0.8, is_correct=False)
    assert round(brier_wrong, 4) == 0.6400  # (0.8 - 0.0)^2 = 0.64

    # Summarizer
    metrics = [
        ScenarioEvaluationMetric(
            scenario_id="GS-01",
            tool_precision=1.0,
            tool_recall=1.0,
            tool_f1=1.0,
            rca_correctness=True,
            groundedness_score=1.0,
            hallucination_rate=0.0,
            citation_correctness=1.0,
            confidence=0.90,
            calibration_error=brier_correct,
        ),
        ScenarioEvaluationMetric(
            scenario_id="GS-02",
            tool_precision=0.8,
            tool_recall=0.8,
            tool_f1=0.8,
            rca_correctness=True,
            groundedness_score=0.9,
            hallucination_rate=0.1,
            citation_correctness=1.0,
            confidence=0.85,
            calibration_error=0.0225,
        ),
    ]
    summary = MetricsEvaluator.summarize(metrics)
    assert summary.total_scenarios == 2
    assert summary.mean_tool_f1 == 0.9
    assert summary.overall_rca_accuracy == 1.0
    assert summary.brier_score < 0.05


def test_groundedness_evaluation_fact_inference_uncertainty():
    """Verify that RCA claims are strictly classified as FACT, INFERENCE, or UNCERTAINTY."""
    evidence = [
        {
            "evidence_id": "ev-1",
            "source": "k8s_get_pod_status",
            "data": {"phase": "CrashLoopBackOff", "exit_code": 137, "pod": "payment-service"},
            "description": "Pod payment-service exited with code 137 OOMKilled",
        },
        {
            "evidence_id": "ev-2",
            "source": "query_prometheus_metric",
            "data": {"metric": "container_memory_usage_bytes", "value": "1048576000"},
            "description": "Memory exceeded 1GB limit",
        },
    ]

    rca_text = (
        "Pod payment-service exited with code 137 OOMKilled. "
        "Memory exceeded 1GB limit causing termination. "
        "Therefore payment processing failed for downstream services. "
        "Network latency metrics were missing or telemetry unavailable."
    )
    citations = ["ev-1", "ev-2"]

    report = GroundednessEvaluator.evaluate(rca_text, evidence, citations)

    assert report.groundedness_score >= 0.80
    assert report.hallucination_rate == 0.0
    assert report.citation_correctness == 1.0
    assert len(report.fabricated_citations) == 0
    assert report.uncertainty_detected is True

    claim_types = [c.claim_type for c in report.claims]
    assert ClaimType.FACT in claim_types
    assert ClaimType.INFERENCE in claim_types
    assert ClaimType.UNCERTAINTY in claim_types


def test_hallucination_and_fabricated_citation_detection():
    """Verify evaluator catches claims with zero evidence support and fabricated citations."""
    evidence = [
        {
            "evidence_id": "ev-real-1",
            "source": "k8s_get_pod_status",
            "data": {"status": "Running"},
        }
    ]

    # Malicious/hallucinated RCA asserting fabricated facts
    hallucinated_rca = (
        "Database Cassandra node exploded in rack 4 with kernel panic. "
        "Hard drive firmware corrupted by solar flare."
    )
    # Fabricated citations
    fake_citations = ["ev-real-1", "ev-fake-999"]

    report = GroundednessEvaluator.evaluate(hallucinated_rca, evidence, fake_citations)

    # Hallucination rate must be high
    assert report.hallucination_rate > 0.50
    assert report.citation_correctness == 0.50
    assert "ev-fake-999" in report.fabricated_citations


@pytest.mark.asyncio
async def test_rag_retrieval_evaluation_metrics(tmp_path):
    """Evaluate vector store retrieval quality: Precision@K, Recall@K, and MRR."""
    from sentinelops.rag.vector_store import PersistentVectorStore
    from sentinelops.rag.embeddings import DeterministicFallbackEmbeddingProvider
    from sentinelops.rag.chunker import OperationalDocumentChunker, DocumentMetadata

    db_path = str(tmp_path / "test_eval_rag.db")
    provider = DeterministicFallbackEmbeddingProvider(dimension=128)
    vector_store = PersistentVectorStore(storage_path=db_path, embedding_provider=provider)
    chunker = OperationalDocumentChunker()

    docs = [
        ("doc-oom", "Troubleshooting Kubernetes OOMKilled containers and memory limits exceeded in cgroups"),
        ("doc-crashloop", "Handling CrashLoopBackOff incidents due to application panic or bad env var"),
        ("doc-kafka", "Kafka broker rebalancing and partition consumer lag diagnostics"),
    ]

    for doc_id, text in docs:
        meta = DocumentMetadata(document_id=doc_id, title=doc_id, source=f"runbooks/{doc_id}.md", document_type="runbook")
        chunks = chunker.chunk_document(text, meta)
        await vector_store.upsert_chunks(chunks, provider)

    benchmarks = [
        RetrievalBenchmarkQuery(
            query="Why did my container get OOMKilled with out of memory error?",
            expected_doc_ids=["doc-oom"],
        ),
        RetrievalBenchmarkQuery(
            query="Pod is in CrashLoopBackOff restarting continuously",
            expected_doc_ids=["doc-crashloop"],
        ),
        RetrievalBenchmarkQuery(
            query="Unrelated query about cooking pasta in boiling water",
            expected_doc_ids=[],  # Irrelevant query
            category="irrelevant",
        ),
    ]

    summary = await RetrievalEvaluator.run_benchmark_suite(vector_store, benchmarks, k=2)

    assert summary.total_queries == 3
    assert summary.mean_reciprocal_rank >= 0.60
    assert summary.p50_latency_ms < 50.0

