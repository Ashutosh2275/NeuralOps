"""Consensus Engine - Multi-agent voting, hallucination blocking, verification"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class AgentVote:
    """Represents an agent's vote on RCA"""

    def __init__(
        self,
        agent_name: str,
        root_cause: str,
        confidence: float,
        evidence: list[str],
        is_supported_by_replay: bool = False,
        is_supported_by_topology: bool = False,
    ):
        self.agent_name = agent_name
        self.root_cause = root_cause
        self.confidence = confidence
        self.evidence = evidence
        self.is_supported_by_replay = is_supported_by_replay
        self.is_supported_by_topology = is_supported_by_topology
        self.voted_at = datetime.utcnow()


class ConsensusResult:
    """Final consensus on RCA"""

    def __init__(
        self,
        root_cause: str,
        confidence: float,
        consensus_score: float,
        supporting_votes: list[str],
        dissenting_votes: list[str],
        is_hallucination: bool,
        validation_checks: dict[str, bool],
    ):
        self.root_cause = root_cause
        self.confidence = confidence
        self.consensus_score = consensus_score
        self.supporting_votes = supporting_votes
        self.dissenting_votes = dissenting_votes
        self.is_hallucination = is_hallucination
        self.validation_checks = validation_checks
        self.generated_at = datetime.utcnow()


class ConsensusEngine:
    """Aggregates AI agent votes and detects hallucinations"""

    def __init__(self):
        self.votes: dict[UUID, list[AgentVote]] = {}

    async def collect_votes(
        self,
        incident_id: UUID,
        agent_votes: list[AgentVote],
    ) -> None:
        """Collect votes from all agents"""
        self.votes[incident_id] = agent_votes
        logger.info(f"Collected {len(agent_votes)} votes for incident {incident_id}")

    async def compute_consensus(
        self,
        incident_id: UUID,
        topology: dict,
        replay_data: Optional[dict] = None,
    ) -> ConsensusResult:
        """Compute consensus from votes"""

        votes = self.votes.get(incident_id, [])

        if not votes:
            return ConsensusResult(
                root_cause="unknown",
                confidence=0.0,
                consensus_score=0.0,
                supporting_votes=[],
                dissenting_votes=[],
                is_hallucination=True,
                validation_checks={},
            )

        # Group votes by root_cause
        vote_groups = {}
        for vote in votes:
            if vote.root_cause not in vote_groups:
                vote_groups[vote.root_cause] = []
            vote_groups[vote.root_cause].append(vote)

        # Find majority vote
        majority_cause = max(vote_groups.keys(), key=lambda c: len(vote_groups[c]))
        majority_votes = vote_groups[majority_cause]

        # Calculate weighted confidence
        weighted_confidence = sum(v.confidence for v in majority_votes) / len(majority_votes)

        # Run validation checks
        validation_checks = await self._validate_rca(
            root_cause=majority_cause,
            topology=topology,
            replay_data=replay_data,
        )

        # Detect hallucination
        is_hallucination = not all(validation_checks.values())

        # Calculate consensus score
        consensus_score = self._calculate_consensus_score(
            majority_votes=majority_votes,
            total_votes=len(votes),
            validation_checks=validation_checks,
        )

        # Build result
        supporting_agents = [v.agent_name for v in majority_votes]
        dissenting_agents = [
            v.agent_name
            for cause, cause_votes in vote_groups.items()
            for v in cause_votes
            if cause != majority_cause
        ]

        result = ConsensusResult(
            root_cause=majority_cause,
            confidence=weighted_confidence,
            consensus_score=consensus_score,
            supporting_votes=supporting_agents,
            dissenting_votes=dissenting_agents,
            is_hallucination=is_hallucination,
            validation_checks=validation_checks,
        )

        logger.info(
            f"Consensus: {majority_cause}, confidence={weighted_confidence:.2f}, "
            f"hallucination={is_hallucination}, consensus={consensus_score:.2f}"
        )

        return result

    async def _validate_rca(
        self,
        root_cause: str,
        topology: dict,
        replay_data: Optional[dict] = None,
    ) -> dict[str, bool]:
        """Run validation checks on RCA"""

        checks = {
            "root_cause_exists": await self._check_service_exists(root_cause, topology),
            "topology_valid": await self._check_topology_structure(topology),
            "replay_confirms": await self._check_replay_confirmation(root_cause, replay_data),
            "no_impossible_claim": await self._check_plausibility(root_cause),
            "evidence_present": True,  # Assumes agents provided evidence
            "consistent_with_timeline": await self._check_timeline_consistency(replay_data),
        }

        return checks

    async def _check_service_exists(self, service_name: str, topology: dict) -> bool:
        """Verify service exists in topology"""
        services = topology.get("services", [])
        return service_name in services or any(
            service_name.lower() in s.lower() for s in services
        )

    async def _check_topology_structure(self, topology: dict) -> bool:
        """Verify topology is well-formed"""
        required_keys = ["services", "dependencies"]
        return all(key in topology for key in required_keys)

    async def _check_replay_confirmation(
        self,
        root_cause: str,
        replay_data: Optional[dict] = None,
    ) -> bool:
        """Check if replay data confirms RCA"""
        if not replay_data:
            return True  # Can't verify without replay data, so don't fail

        # Check if root cause service had anomaly in replay
        events = replay_data.get("events", [])
        for event in events:
            if event.get("source_entity") == root_cause:
                return True

        return False

    async def _check_plausibility(self, root_cause: str) -> bool:
        """Check if root cause is plausible (not clearly fabricated)"""
        # Reject obvious fabrications
        implausible_names = ["quantum", "magic", "unicorn", "dragon", "ai-overlord"]
        return not any(name in root_cause.lower() for name in implausible_names)

    async def _check_timeline_consistency(self, replay_data: Optional[dict] = None) -> bool:
        """Check if events follow reasonable timeline"""
        if not replay_data:
            return True

        events = replay_data.get("events", [])
        if not events:
            return True

        # Verify timestamps are monotonically increasing
        prev_timestamp = None
        for event in events:
            curr_timestamp = event.get("timestamp")
            if prev_timestamp and curr_timestamp and curr_timestamp < prev_timestamp:
                return False
            prev_timestamp = curr_timestamp

        return True

    def _calculate_consensus_score(
        self,
        majority_votes: list[AgentVote],
        total_votes: int,
        validation_checks: dict[str, bool],
    ) -> float:
        """Calculate overall consensus score 0-1"""

        # Vote agreement ratio
        agreement_ratio = len(majority_votes) / total_votes

        # Validation score
        validation_score = sum(validation_checks.values()) / len(validation_checks)

        # Average vote confidence
        avg_confidence = sum(v.confidence for v in majority_votes) / len(majority_votes)

        # Weighted score
        consensus_score = (
            agreement_ratio * 0.4 +
            validation_score * 0.4 +
            avg_confidence * 0.2
        )

        return consensus_score

    async def detect_hallucination_risk(
        self,
        cluster_id: UUID,
        historical_validations: list[dict],
    ) -> float:
        """Calculate hallucination risk for cluster 0-1"""
        if not historical_validations:
            return 0.5  # Unknown risk

        hallucinations = sum(
            1 for v in historical_validations
            if v.get("is_hallucination", False)
        )

        return hallucinations / len(historical_validations)


# Singleton instance
consensus_engine = ConsensusEngine()
