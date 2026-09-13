import asyncio
import json
import signal
from uuid import UUID

from sentinelops.ai import AIOrchestrator
from sentinelops.agents.orchestrator import AgentOrchestrator
from sentinelops.collectors import get_event_collector
from sentinelops.config import get_settings
from sentinelops.core.database import async_session_factory
from sentinelops.core.logging import configure_logging, get_logger
from sentinelops.events.schemas import BaseEvent, EventType
from sentinelops.models.ai import AIInsight, AIReasoningLog
from sentinelops.services.intelligence_service import IntelligenceService
from sentinelops.services.recommendation_service import RecommendationService
from sentinelops.streams.bus import EventBus
from sentinelops.websocket.hub import ws_hub

log = get_logger(__name__)
from sentinelops.engines.correlation import CorrelationEngine
DEFAULT_CLUSTER_ID = UUID("00000000-0000-0000-0000-000000000001")


class WorkerRunner:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._bus = EventBus()
        self._collector = get_event_collector(self._bus)
        self._orchestrator = AgentOrchestrator()
        self._ai_orchestrator = AIOrchestrator()
        self._correlation_engine = CorrelationEngine(settings=self._settings)
        self._event_buffer: dict[str, list[BaseEvent]] = {}
        self._shutdown = False

    async def start(self) -> None:
        configure_logging()
        await self._bus.initialize()
        log.info("workers_started")
        await asyncio.gather(
            self._collector.start(),
            self._consume_raw_events(),
            self._consume_correlation(),
            self._consume_anomalies(),
        )

    async def _consume_raw_events(self) -> None:
        async def handler(event: BaseEvent, message_id: str) -> None:
            key = f"{event.cluster_id}:{event.namespace}"
            self._event_buffer.setdefault(key, []).append(event)
            await self._bus.publisher.publish_to_enriched(event)
            await ws_hub.broadcast("event", {
                "event_type": event.event_type.value,
                "namespace": event.namespace,
                "severity": event.severity.value,
            })
            try:
                corr_events = self._correlation_engine.ingest(event)
                for corr in corr_events:
                    await self._bus.publisher.publish(self._settings.stream_correlation, corr)
                    log.info("correlation_event_published", correlation_id=str(corr.correlation_id), trigger=corr.payload.get("trigger"))
            except Exception as e:
                log.warning("correlation_ingest_failed", error=str(e))

        await self._bus.consumer.consume(
            self._settings.stream_events_raw,
            self._settings.consumer_group_collector,
            "worker-collector-1",
            handler,
        )

    async def _consume_anomalies(self) -> None:
        async def handler(event: BaseEvent, message_id: str) -> None:
            await ws_hub.broadcast("anomaly", {
                "namespace": event.namespace,
                "pod": event.payload.get("pod_name"),
                "type": event.payload.get("anomaly_type"),
                "severity": event.severity.value,
            })
            try:
                corr_events = self._correlation_engine.ingest(event)
                for corr in corr_events:
                    await self._bus.publisher.publish(self._settings.stream_correlation, corr)
                    log.info("correlation_event_published_from_anomaly", correlation_id=str(corr.correlation_id), trigger=corr.payload.get("trigger"))
            except Exception as e:
                log.warning("correlation_anomaly_ingest_failed", error=str(e))

        await self._bus.consumer.consume(
            self._settings.stream_anomaly_events,
            self._settings.consumer_group_correlation,
            "worker-anomaly-1",
            handler,
        )

    async def _consume_correlation(self) -> None:
        async def handler(event: BaseEvent, message_id: str) -> None:
            if event.event_type != EventType.CORRELATION:
                return

            key = f"{event.cluster_id}:{event.namespace}"
            related_events = self._event_buffer.get(key, [event])

            async with async_session_factory() as session:
                intel = IntelligenceService(session)
                incident_id, rca_result = await intel.process_correlation(
                    event, related_events, DEFAULT_CLUSTER_ID
                )

                # Run legacy agent orchestrator
                agent_results = await self._orchestrator.run_incident_analysis(
                    incident_id=incident_id,
                    cluster_id=event.cluster_id,
                    namespace=event.namespace,
                    events=related_events,
                    topology=intel.dependency_engine.to_snapshot_json(),
                    rca_result=rca_result,
                )

                # Run new AI orchestrator
                try:
                    ai_results = await self._ai_orchestrator.orchestrate(
                        incident_id=incident_id,
                        cluster_id=event.cluster_id,
                        namespace=event.namespace,
                        events=related_events,
                        topology=intel.dependency_engine.to_snapshot_json(),
                        cascade_chain=rca_result.cascade_chain if rca_result else [],
                        rca_summary=rca_result.root_cause if rca_result else None,
                    )

                    # Store AI insights
                    for agent_type, ai_result in ai_results.items():
                        insight = AIInsight(
                            incident_id=incident_id,
                            agent_type=agent_type,
                            insight_type="ai_analysis",
                            title=f"{agent_type.upper()} Analysis",
                            content="; ".join(ai_result.findings),
                            confidence=ai_result.confidence,
                            reasoning=ai_result.reasoning,
                        )
                        session.add(insight)

                        # Log reasoning for debugging
                        log_entry = AIReasoningLog(
                            incident_id=incident_id,
                            agent_type=agent_type,
                            prompt="[AI Analysis]",
                            response=ai_result.raw_response or "",
                            tokens_used=ai_result.tokens_used,
                            latency_ms=ai_result.latency_ms,
                            model_used=ai_result.model_used,
                            success=ai_result.success,
                        )
                        session.add(log_entry)

                        # Broadcast AI insights
                        await ws_hub.broadcast("ai_insight", {
                            "agent": agent_type,
                            "findings": ai_result.findings,
                            "confidence": ai_result.confidence,
                            "reasoning": ai_result.reasoning,
                        })

                except Exception as e:
                    log.error("ai_orchestration_failed", error=str(e))

                await intel.save_ai_insights(incident_id, agent_results)
                rec_svc = RecommendationService(session)
                det_recs = rec_svc.generate_deterministic(rca_result, event.namespace)
                recs = await rec_svc.persist(incident_id, det_recs, agent_results)
                await session.commit()

            await self._bus.publisher.publish_incident(event)

            # Broadcast topology update
            topology_data = intel.dependency_engine.to_snapshot_json()
            await ws_hub.broadcast_topology_update(topology_data)

            # Broadcast incident information
            await ws_hub.broadcast("incident", {
                "incident_id": str(incident_id),
                "title": event.payload.get("title", "Correlated incident"),
                "root_cause": rca_result.root_cause,
                "confidence": rca_result.confidence,
                "agents": [r.agent_type for r in agent_results],
            })

            # Broadcast RCA details
            await ws_hub.broadcast("rca", rca_result.report)

            # Broadcast cascade information
            if rca_result.origin_pod:
                cascade = intel.dependency_engine.detect_cascading_failure(
                    intel.dependency_engine.node_id(event.namespace, "Pod", rca_result.origin_pod)
                )
                await ws_hub.broadcast_cascading_failure({
                    "origin": cascade.origin_node,
                    "affected_count": cascade.affected_count,
                    "propagation_depth": cascade.propagation_depth,
                    "escalation_factor": cascade.escalation_factor,
                    "chain": cascade.cascade_chain,
                })

                # Broadcast health propagation
                health_propagations = intel.dependency_engine.propagate_health(
                    intel.dependency_engine.node_id(event.namespace, "Pod", rca_result.origin_pod),
                    "critical",
                )
                await ws_hub.broadcast_health_propagation({
                    "source": rca_result.origin_pod,
                    "propagations": [
                        {
                            "node_id": hp.node_id,
                            "original": hp.original_health,
                            "propagated": hp.propagated_health,
                            "influence": hp.influence_score,
                        }
                        for hp in health_propagations
                    ],
                })

            # Broadcast recommendations
            await ws_hub.broadcast("recommendations", [
                {"title": r.title, "priority": r.priority} for r in recs[:5]
            ])

        await self._bus.consumer.consume(
            self._settings.stream_correlation,
            self._settings.consumer_group_correlation,
            "worker-correlation-1",
            handler,
        )


def main() -> None:
    runner = WorkerRunner()

    def shutdown_handler(*_: object) -> None:
        runner._shutdown = True

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    asyncio.run(runner.start())


if __name__ == "__main__":
    main()


