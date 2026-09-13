import json
from uuid import UUID

from sentinelops.models.predictive import AIConfidenceValidation


class AIConfidenceValidator:
    """Validates AI reasoning to prevent hallucinations."""

    def __init__(self):
        self.validation_checks = [
            "root_cause_exists_in_topology",
            "affected_services_valid",
            "cascade_chain_dependency_valid",
            "timeline_events_match_reasoning",
            "confidence_score_justified",
            "no_impossible_services",
            "recovery_time_realistic",
            "metrics_support_conclusion",
        ]

    async def validate_rca_reasoning(
        self,
        incident_id: UUID,
        rca_reasoning: str,
        confidence_score: float,
        incident_data: dict,
        topology: dict,
        incident_history: list[dict],
    ) -> AIConfidenceValidation:
        """Validate RCA reasoning for hallucinations."""

        validation = AIConfidenceValidation(
            incident_id=incident_id,
            rca_reasoning=rca_reasoning,
            confidence_score=confidence_score,
            validation_checks_json=json.dumps(self.validation_checks),
            passed_checks=0,
            failed_checks=0,
            is_hallucination=False,
            is_valid=True,
            validation_details_json=json.dumps({}),
        )

        results = {}

        # Check 1: Root cause service exists in topology
        root_service = incident_data.get("root_service")
        root_exists = root_service in topology.get("services", {})
        results["root_cause_exists_in_topology"] = root_exists
        if root_exists:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1

        # Check 2: All affected services exist
        affected_services = incident_data.get("affected_services", [])
        if isinstance(affected_services, str):
            try:
                affected_services = json.loads(affected_services)
            except:
                affected_services = []

        services_valid = all(s in topology.get("services", {}) for s in affected_services)
        results["affected_services_valid"] = services_valid
        if services_valid:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1

        # Check 3: Cascade chain follows topology dependencies
        cascade_chain = incident_data.get("cascade_chain", [])
        if isinstance(cascade_chain, str):
            try:
                cascade_chain = json.loads(cascade_chain)
            except:
                cascade_chain = []

        cascade_valid = await self._validate_cascade_chain(cascade_chain, topology)
        results["cascade_chain_dependency_valid"] = cascade_valid
        if cascade_valid:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1

        # Check 4: Timeline events exist and match reasoning
        timeline_events = incident_data.get("timeline_events", [])
        timeline_match = len(timeline_events) > 0
        results["timeline_events_match_reasoning"] = timeline_match
        if timeline_match:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1

        # Check 5: Confidence score is justified
        confidence_justified = await self._validate_confidence_score(
            confidence_score,
            cascade_valid,
            services_valid,
            incident_history,
        )
        results["confidence_score_justified"] = confidence_justified
        if confidence_justified:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1

        # Check 6: No impossible services mentioned
        impossible_services = await self._find_impossible_services(rca_reasoning, topology)
        no_impossible = len(impossible_services) == 0
        results["no_impossible_services"] = no_impossible
        if no_impossible:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1
            validation.is_hallucination = True

        # Check 7: Recovery time is realistic
        recovery_time = incident_data.get("expected_recovery_seconds", 300)
        recovery_realistic = 30 < recovery_time < 3600  # Between 30s and 1 hour
        results["recovery_time_realistic"] = recovery_realistic
        if recovery_realistic:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1

        # Check 8: Metrics support conclusion
        metrics_support = await self._validate_metrics_support(incident_data)
        results["metrics_support_conclusion"] = metrics_support
        if metrics_support:
            validation.passed_checks += 1
        else:
            validation.failed_checks += 1

        # Determine if valid
        validation.is_valid = validation.failed_checks <= 2
        validation.is_hallucination = not validation.is_valid and validation.failed_checks > 3

        validation.validation_details_json = json.dumps(results)

        return validation

    async def _validate_cascade_chain(
        self,
        cascade_chain: list,
        topology: dict,
    ) -> bool:
        """Validate that cascade chain follows known dependencies."""
        if not cascade_chain:
            return True

        dependencies = topology.get("dependencies", {})

        for idx, service in enumerate(cascade_chain):
            service_name = service.get("service") if isinstance(service, dict) else service

            if idx > 0:
                prev_service = cascade_chain[idx - 1]
                prev_name = prev_service.get("service") if isinstance(prev_service, dict) else prev_service

                # Check if dependency exists
                if prev_name not in dependencies:
                    return False

                if service_name not in dependencies.get(prev_name, []):
                    return False

        return True

    async def _validate_confidence_score(
        self,
        confidence: float,
        cascade_valid: bool,
        services_valid: bool,
        incident_history: list[dict],
    ) -> bool:
        """Validate confidence score against evidence."""
        # If cascade or services invalid, confidence should be < 0.5
        if not cascade_valid or not services_valid:
            return confidence < 0.5

        # If both valid and we have history, confidence can be higher
        if len(incident_history) > 5:
            return 0.5 <= confidence <= 0.95

        return 0.3 <= confidence <= 0.9

    async def _find_impossible_services(
        self,
        rca_reasoning: str,
        topology: dict,
    ) -> list[str]:
        """Find services mentioned that don't exist in topology."""
        impossible = []
        raw_services = topology.get("services", {})
        if isinstance(raw_services, dict):
            known_services = set(raw_services.keys())
        elif isinstance(raw_services, list):
            known_services = set(raw_services)
        else:
            known_services = set()

        # Extract service names from reasoning
        words = rca_reasoning.split()
        for i, word in enumerate(words):
            cleaned = word.lower().strip(".,;:\"'")
            if not cleaned or cleaned in ["service", "pod", "node", "the", "a", "an", "due", "to", "in"]:
                continue

            prev_word = words[i - 1].lower().strip(".,;:\"'") if i > 0 else ""
            is_quoted = (word.startswith("'") or word.startswith('"') or word.endswith("'") or word.endswith('"'))
            is_prefixed = cleaned.startswith("service-")
            is_following_service = prev_word in ["service", "services"]

            if is_quoted or is_prefixed or is_following_service:
                if cleaned not in known_services and cleaned not in [
                    "degraded", "failure", "unhealthy", "crash", "restart", "down", "overloading", "timeout"
                ]:
                    impossible.append(cleaned)

        return impossible

    async def _validate_metrics_support(
        self,
        incident_data: dict,
    ) -> bool:
        """Check if metrics support the incident conclusion."""
        # If we have metric anomalies, conclusion is supported
        metric_anomalies = incident_data.get("metric_anomalies", [])
        if metric_anomalies:
            return True

        # If no metrics at all, less support
        return False

    async def calculate_ai_hallucination_risk(
        self,
        validations: list[AIConfidenceValidation],
    ) -> float:
        """Calculate overall hallucination risk across multiple validations."""
        if not validations:
            return 0.0

        hallucination_count = sum(1 for v in validations if v.is_hallucination)
        return min(1.0, hallucination_count / len(validations))


confidence_validator = AIConfidenceValidator()
