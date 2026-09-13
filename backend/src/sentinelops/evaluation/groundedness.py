"""
Groundedness, Citation Verification, and Hallucination Detection Engine.
Validates that every claim in the generated RCA is grounded in collected evidence,
classifies claims into FACT, INFERENCE, and UNCERTAINTY, and catches hallucinations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, List, Optional


class ClaimType(str, Enum):
    FACT = "FACT"              # Directly stated in tool results/evidence
    INFERENCE = "INFERENCE"    # Logical conclusion drawn from observed facts
    UNCERTAINTY = "UNCERTAINTY"# Explicit admission of missing/conflicting data
    HALLUCINATION = "HALLUCINATION" # Claim not supported by any evidence


@dataclass
class ClaimAssessment:
    text: str
    claim_type: ClaimType
    supporting_evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class GroundednessReport:
    groundedness_score: float # Ratio of (FACT + INFERENCE + UNCERTAINTY) to total claims
    hallucination_rate: float # Ratio of HALLUCINATION to total claims
    citation_correctness: float # Ratio of valid citation IDs to total citations
    claims: list[ClaimAssessment] = field(default_factory=list)
    fabricated_citations: list[str] = field(default_factory=list)
    uncertainty_detected: bool = False


class GroundednessEvaluator:
    """Evaluates the epistemic integrity of an investigation's RCA."""

    UNCERTAINTY_KEYWORDS = [
        "insufficient evidence",
        "missing data",
        "unknown",
        "telemetry unavailable",
        "unverified",
        "inconclusive",
        "could not determine",
        "not found",
    ]

    @classmethod
    def evaluate(
        cls,
        rca_text: str,
        evidence_list: list[dict[str, Any]],
        citations: list[str],
    ) -> GroundednessReport:
        if not rca_text or not rca_text.strip():
            return GroundednessReport(
                groundedness_score=0.0,
                hallucination_rate=0.0,
                citation_correctness=1.0,
                claims=[],
            )

        # 1. Check citations validity against actual evidence IDs
        valid_evidence_ids = {e.get("evidence_id") for e in evidence_list if e.get("evidence_id")}
        cited_set = set(citations)
        fabricated_citations = [c for c in cited_set if c not in valid_evidence_ids]
        citation_correctness = (
            (len(cited_set) - len(fabricated_citations)) / len(cited_set)
            if cited_set
            else 1.0
        )

        # 2. Extract textual evidence corpus
        corpus = ""
        for ev in evidence_list:
            corpus += f" {ev.get('source', '')} {str(ev.get('data', ''))} {ev.get('description', '')}".lower()

        # 3. Split RCA into sentence-level claims
        raw_claims = [c.strip() for c in re.split(r"[.\n;]", rca_text) if len(c.strip()) > 8]
        if not raw_claims:
            raw_claims = [rca_text.strip()]

        claims_assessment: list[ClaimAssessment] = []
        has_uncertainty = False

        for claim in raw_claims:
            claim_lower = claim.lower()

            # Check for explicit uncertainty
            if any(uk in claim_lower for uk in cls.UNCERTAINTY_KEYWORDS):
                claims_assessment.append(ClaimAssessment(text=claim, claim_type=ClaimType.UNCERTAINTY))
                has_uncertainty = True
                continue

            INFERENCE_INDICATORS = [
                "therefore", "consequently", "likely", "indicates", "suggests",
                "resulting in", "impacted", "because", "due to", "inferred",
                "analysis suggests", "failed for", "downstream",
            ]
            has_inference_indicator = any(ind in claim_lower for ind in INFERENCE_INDICATORS)

            # Check if keywords in claim are grounded in evidence corpus
            # Extract non-trivial words (length > 4)
            stop_words = {"the", "that", "this", "from", "with", "have", "been", "were", "where", "which", "about", "therefore"}
            words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{4,}\b", claim_lower) if w not in stop_words]
            if not words:
                claims_assessment.append(ClaimAssessment(text=claim, claim_type=ClaimType.INFERENCE))
                continue

            matches = sum(1 for w in words if (w in corpus or w.rstrip('s') in corpus or (len(w) > 4 and w[:4] in corpus)))
            match_ratio = matches / len(words)

            if match_ratio >= 0.50:
                # Direct fact
                matching_ev_ids = [
                    ev.get("evidence_id")
                    for ev in evidence_list
                    if any(w in str(ev.get("data", "")).lower() for w in words[:3])
                ]
                claims_assessment.append(
                    ClaimAssessment(
                        text=claim,
                        claim_type=ClaimType.FACT,
                        supporting_evidence_ids=[str(e) for e in matching_ev_ids if e],
                    )
                )
            elif match_ratio >= 0.20 or (has_inference_indicator and matches >= 1):
                # Plausible inference grounded in evidence
                claims_assessment.append(ClaimAssessment(text=claim, claim_type=ClaimType.INFERENCE))
            else:
                # Unsupported claim / potential hallucination
                claims_assessment.append(ClaimAssessment(text=claim, claim_type=ClaimType.HALLUCINATION))


        total_claims = len(claims_assessment)
        hallucinations = sum(1 for c in claims_assessment if c.claim_type == ClaimType.HALLUCINATION)
        grounded_claims = total_claims - hallucinations

        groundedness_score = grounded_claims / total_claims if total_claims > 0 else 1.0
        hallucination_rate = hallucinations / total_claims if total_claims > 0 else 0.0

        return GroundednessReport(
            groundedness_score=groundedness_score,
            hallucination_rate=hallucination_rate,
            citation_correctness=citation_correctness,
            claims=claims_assessment,
            fabricated_citations=fabricated_citations,
            uncertainty_detected=has_uncertainty,
        )
