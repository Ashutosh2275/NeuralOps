import json
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from sentinelops.core.logging import get_logger
from sentinelops.engines.correlation import CorrelationEngine
from sentinelops.engines.dependency import DependencyIntelligenceEngine
from sentinelops.engines.rca import RCAEngine, RCAResult
from sentinelops.engines.replay import ReplayEngine
from sentinelops.engines.topology import TopologySnapshotEngine
from sentinelops.events.schemas import BaseEvent, CorrelationEvent, EventType
from sentinelops.models.intelligence import AIInsight, CorrelationGroup
from sentinelops.services.incident_service import IncidentService
from sentinelops.services.topology_service import TopologyService

log = get_logger(__name__)


class IntelligenceService:
    """Orchestrates correlation, RCA, topology, replay, and AI insights."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._dependency = DependencyIntelligenceEngine()
        self._correlation = CorrelationEngine(dependency=self._dependency)
        self._rca = RCAEngine(dependency=self._dependency)
        self._topology = TopologySnapshotEngine(self._dependency)
        self._topology_svc = TopologyService(session)
        self._replay = ReplayEngine()
        self._incidents = IncidentService(session)

    @property
    def dependency_engine(self) -> DependencyIntelligenceEngine:
        return self._dependency

    @property
    def replay_engine(self) -> ReplayEngine:
        return self._replay

    @property
    def topology_service(self) -> TopologyService:
        return self._topology_svc

    def ingest_topology(self, k8s_data: dict) -> int:
        return self._dependency.discover_from_collector_data(
            k8s_data.get("pods", []),
            k8s_data.get("services", []),
            k8s_data.get("dependencies", []),
        )

    async def process_correlation(
        self,
        correlation: CorrelationEvent | BaseEvent,
        events: list[BaseEvent],
        cluster_id: UUID,
    ) -> tuple[UUID, RCAResult]:
        corr_id = getattr(correlation, "correlation_id", None) or uuid4()
        group = CorrelationGroup(
            id=corr_id if isinstance(corr_id, UUID) else uuid4(),
            cluster_id=cluster_id,
            namespace=correlation.namespace,
            trigger=correlation.payload.get("trigger", "unknown"),
            severity=correlation.severity.value,
            event_count=len(events),
            related_event_ids_json=json.dumps(correlation.payload.get("related_event_ids", [])),
            dependency_context_json=json.dumps(correlation.payload.get("dependency_context", {})),
            confidence_score=correlation.payload.get("confidence_score", 0.5),
        )
        self._session.add(group)

        incident_event = self._correlation.build_incident_from_correlation(correlation)
        rca_result = self._rca.analyze(events, dependency_engine=self._dependency)
        incident_event = self._rca.enrich_incident(incident_event, rca_result)

        incident = await self._incidents.create_from_event(incident_event, cluster_id)
        group.incident_id = incident.id

        graph = self._dependency.to_snapshot_json()
        await self._topology.capture(self._session, cluster_id, incident.id)

        # Create versioned snapshot
        try:
            await self._topology_svc.create_version_snapshot(cluster_id, graph)
        except Exception as e:
            log.warning("topology_version_creation_failed", error=str(e))

        for e in events:
            self._replay.buffer_event(incident.id, e, graph)
        await self._replay.persist_replay(self._session, incident.id, graph)

        await self._incidents.update_rca(
            incident.id,
            rca_result.root_cause,
            rca_result.root_service,
            rca_result.confidence,
            rca_result.cascade_chain,
        )

        # Update dependency scores based on cascading failure
        try:
            if rca_result.origin_pod:
                origin_node = self._dependency.node_id(
                    correlation.namespace,
                    "Pod",
                    rca_result.origin_pod,
                )
                await self._topology_svc.update_dependency_scores(cluster_id, origin_node)
        except Exception as e:
            log.warning("dependency_score_update_failed", error=str(e))

        return incident.id, rca_result

    async def save_ai_insights(self, incident_id: UUID, agent_results: list) -> list[AIInsight]:
        insights: list[AIInsight] = []
        for result in agent_results:
            for finding in result.findings[:5]:
                insight = AIInsight(
                    id=uuid4(),
                    incident_id=incident_id,
                    agent_type=result.agent_type,
                    insight_type="finding",
                    title=f"{result.agent_type} analysis",
                    content=finding,
                    confidence=result.confidence,
                )
                self._session.add(insight)
                insights.append(insight)
        await self._session.flush()
        return insights

    def blast_radius(self, namespace: str, pod_name: str) -> dict:
        node_id = self._dependency.node_id(namespace, "Pod", pod_name)
        result = self._dependency.blast_radius(node_id)
        return {
            "root": result.root_node,
            "affected": result.affected_nodes,
            "count": result.affected_count,
            "influence_scores": result.influence_scores,
        }

    async def get_cascading_failure_details(self, namespace: str, pod_name: str) -> dict:
        """Get detailed cascading failure information."""
        node_id = self._dependency.node_id(namespace, "Pod", pod_name)
        cascade = self._dependency.detect_cascading_failure(node_id)
        health_propagations = self._dependency.propagate_health(node_id, "critical")

        return {
            "cascade": {
                "origin": cascade.origin_node,
                "chain": cascade.cascade_chain,
                "affected_count": cascade.affected_count,
                "propagation_depth": cascade.propagation_depth,
                "escalation_factor": round(cascade.escalation_factor, 2),
            },
            "health_propagations": [
                {
                    "node": hp.node_id,
                    "original": hp.original_health,
                    "propagated": hp.propagated_health,
                    "influence": hp.influence_score,
                    "path_length": len(hp.propagation_path),
                }
                for hp in health_propagations
            ],
        }
