"""Evaluation and benchmarking suite for SentinelOps AI."""

from sentinelops.evaluation.dataset import (
    GOLDEN_SCENARIOS,
    GoldenScenario,
    get_scenario_by_id,
)
from sentinelops.evaluation.metrics import (
    MetricsEvaluator,
    ScenarioEvaluationMetric,
    EvaluationSuiteSummary,
)
from sentinelops.evaluation.groundedness import (
    ClaimAssessment,
    ClaimType,
    GroundednessEvaluator,
    GroundednessReport,
)
from sentinelops.evaluation.retrieval_eval import (
    QueryRetrievalResult,
    RetrievalBenchmarkQuery,
    RetrievalBenchmarkSummary,
    RetrievalEvaluator,
)

__all__ = [
    "GOLDEN_SCENARIOS",
    "GoldenScenario",
    "get_scenario_by_id",
    "MetricsEvaluator",
    "ScenarioEvaluationMetric",
    "EvaluationSuiteSummary",
    "ClaimAssessment",
    "ClaimType",
    "GroundednessEvaluator",
    "GroundednessReport",
    "QueryRetrievalResult",
    "RetrievalBenchmarkQuery",
    "RetrievalBenchmarkSummary",
    "RetrievalEvaluator",
]
