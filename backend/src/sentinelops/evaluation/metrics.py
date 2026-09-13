"""
Evaluation Metrics Engine for SentinelOps AI Autonomous Investigation Engine.
Measures Tool Selection Accuracy, RCA Correctness, Groundedness, Hallucination Rate,
Citation Correctness, and Confidence Calibration (Brier Score).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import List, Optional


@dataclass
class ScenarioEvaluationMetric:
    scenario_id: str
    tool_precision: float = 0.0
    tool_recall: float = 0.0
    tool_f1: float = 0.0
    unnecessary_tools_count: int = 0
    rca_correctness: bool = False
    groundedness_score: float = 0.0
    hallucination_rate: float = 0.0
    citation_correctness: float = 0.0
    confidence: float = 0.0
    calibration_error: float = 0.0
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "tool_precision": round(self.tool_precision, 3),
            "tool_recall": round(self.tool_recall, 3),
            "tool_f1": round(self.tool_f1, 3),
            "unnecessary_tools_count": self.unnecessary_tools_count,
            "rca_correctness": self.rca_correctness,
            "groundedness_score": round(self.groundedness_score, 3),
            "hallucination_rate": round(self.hallucination_rate, 3),
            "citation_correctness": round(self.citation_correctness, 3),
            "confidence": round(self.confidence, 3),
            "calibration_error": round(self.calibration_error, 3),
            "duration_ms": round(self.duration_ms, 2),
        }


@dataclass
class EvaluationSuiteSummary:
    total_scenarios: int = 0
    mean_tool_precision: float = 0.0
    mean_tool_recall: float = 0.0
    mean_tool_f1: float = 0.0
    mean_groundedness: float = 0.0
    mean_hallucination_rate: float = 0.0
    mean_citation_correctness: float = 0.0
    overall_rca_accuracy: float = 0.0
    brier_score: float = 0.0
    metrics: list[ScenarioEvaluationMetric] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_scenarios": self.total_scenarios,
            "mean_tool_precision": round(self.mean_tool_precision, 3),
            "mean_tool_recall": round(self.mean_tool_recall, 3),
            "mean_tool_f1": round(self.mean_tool_f1, 3),
            "mean_groundedness": round(self.mean_groundedness, 3),
            "mean_hallucination_rate": round(self.mean_hallucination_rate, 3),
            "mean_citation_correctness": round(self.mean_citation_correctness, 3),
            "overall_rca_accuracy": round(self.overall_rca_accuracy, 3),
            "brier_score": round(self.brier_score, 4),
            "scenario_count": len(self.metrics),
        }


class MetricsEvaluator:
    """Computes rigorous quantitative metrics over investigation runs."""

    @staticmethod
    def evaluate_tool_selection(
        selected_tools: list[str],
        expected_tools: list[str],
    ) -> tuple[float, float, float, int]:
        """Compute precision, recall, F1, and unnecessary tools count."""
        if not expected_tools and not selected_tools:
            return 1.0, 1.0, 1.0, 0
        if not selected_tools:
            return 0.0, 0.0, 0.0, 0

        selected_set = set(selected_tools)
        expected_set = set(expected_tools)

        true_positives = len(selected_set.intersection(expected_set))
        precision = true_positives / len(selected_set) if selected_set else 0.0
        recall = true_positives / len(expected_set) if expected_set else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        unnecessary = len(selected_set - expected_set)

        return precision, recall, f1, unnecessary

    @staticmethod
    def evaluate_calibration(confidence: float, is_correct: bool) -> float:
        """
        Compute calibration error (squared difference between confidence and binary outcome).
        Brier component = (confidence - actual)^2
        """
        actual = 1.0 if is_correct else 0.0
        return (confidence - actual) ** 2

    @staticmethod
    def summarize(metrics: list[ScenarioEvaluationMetric]) -> EvaluationSuiteSummary:
        """Compute aggregates across evaluated scenarios."""
        if not metrics:
            return EvaluationSuiteSummary()

        n = len(metrics)
        mean_p = sum(m.tool_precision for m in metrics) / n
        mean_r = sum(m.tool_recall for m in metrics) / n
        mean_f1 = sum(m.tool_f1 for m in metrics) / n
        mean_groundedness = sum(m.groundedness_score for m in metrics) / n
        mean_hallucination = sum(m.hallucination_rate for m in metrics) / n
        mean_citation = sum(m.citation_correctness for m in metrics) / n
        rca_acc = sum(1 for m in metrics if m.rca_correctness) / n
        brier = sum(m.calibration_error for m in metrics) / n

        return EvaluationSuiteSummary(
            total_scenarios=n,
            mean_tool_precision=mean_p,
            mean_tool_recall=mean_r,
            mean_tool_f1=mean_f1,
            mean_groundedness=mean_groundedness,
            mean_hallucination_rate=mean_hallucination,
            mean_citation_correctness=mean_citation,
            overall_rca_accuracy=rca_acc,
            brier_score=brier,
            metrics=metrics,
        )
