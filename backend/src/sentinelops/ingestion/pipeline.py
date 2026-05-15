import asyncio
from uuid import uuid4

from sentinelops.collectors.k8s_collector import KubernetesCollector
from sentinelops.collectors.loki_collector import LokiCollector
from sentinelops.collectors.prometheus_collector import PrometheusCollector
from sentinelops.config import Settings, get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import EventType
from sentinelops.pipeline.correlation_metadata import CorrelationMetadataLayer
from sentinelops.pipeline.normalized_event import NormalizedEvent, StreamKind
from sentinelops.pipeline.normalizer import EventNormalizer
from sentinelops.pipeline.severity_engine import SeverityEngine
from sentinelops.pipeline.validator import EventValidationPipeline
from sentinelops.streams.bus import EventBus

log = get_logger(__name__)


class IngestionPipeline:
    """Orchestrates collectors, normalization, severity, validation, and stream publish."""

    def __init__(self, bus: EventBus, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._bus = bus
        self._prometheus = PrometheusCollector(self._settings)
        self._loki = LokiCollector(self._settings)
        self._k8s = KubernetesCollector()
        self._normalizer = EventNormalizer()
        self._severity = SeverityEngine(self._settings)
        self._validator = EventValidationPipeline()
        self._correlation = CorrelationMetadataLayer(
            window_seconds=self._settings.ingestion_correlation_window_seconds
        )
        self._running = False

    async def start(self) -> None:
        self._running = True
        log.info("ingestion_pipeline_started", interval=self._settings.k8s_collect_interval_seconds)
        while self._running:
            try:
                count = await self.run_once()
                log.info("ingestion_cycle_done", published=count)
            except Exception as e:
                log.error("ingestion_cycle_error", error=str(e))
            await asyncio.sleep(self._settings.k8s_collect_interval_seconds)

    async def stop(self) -> None:
        self._running = False

    async def run_once(self) -> int:
        trace_id = str(uuid4())
        namespace = self._settings.k8s_namespace

        prom_raw, loki_raw, k8s_data = await asyncio.gather(
            self._prometheus.collect(namespace),
            self._loki.collect(namespace),
            self._k8s.collect_all(namespace),
        )

        events: list[NormalizedEvent] = []
        events.extend(self._prometheus.normalize_batch(prom_raw, trace_id))
        events.extend(self._loki.normalize_batch(loki_raw, trace_id))

        for pod in k8s_data.get("pods", []):
            events.append(self._normalizer.normalize(
                pod, event_type=EventType.POD, source="k8s-collector",
                stream_kind=StreamKind.METRICS, trace_id=trace_id,
            ))

        for topo in k8s_data.get("topology", []):
            events.append(self._normalizer.normalize(
                topo, event_type=EventType.TOPOLOGY, source="k8s-collector",
                stream_kind=StreamKind.TOPOLOGY, trace_id=trace_id,
            ))

        for dep in k8s_data.get("dependencies", []):
            events.append(self._normalizer.normalize(
                dep, event_type=EventType.TOPOLOGY, source="k8s-collector",
                stream_kind=StreamKind.TOPOLOGY, trace_id=trace_id,
            ))

        events = self._detect_anomalies(events, prom_raw, k8s_data.get("pods", []))
        events = [self._severity.score(e) for e in events]
        events = self._correlation.enrich_batch(events)
        events = self._validator.validate_batch(events)

        if not hasattr(self, "_dep_engine"):
            from sentinelops.engines.dependency import DependencyIntelligenceEngine
            self._dep_engine = DependencyIntelligenceEngine()
        self._dep_engine.discover_from_collector_data(
            k8s_data.get("pods", []),
            k8s_data.get("services", []),
            k8s_data.get("dependencies", []),
        )

        published = 0
        for event in events:
            msg_id = await self._bus.publisher.publish_normalized(event)
            await self._bus.publisher.publish_to_raw(event.to_base_event())
            published += 1
            log.debug("ingestion_published", stream=event.stream_kind.value, msg_id=msg_id)

        try:
            from sentinelops.websocket.hub import ws_hub
            graph = self._dep_engine.to_snapshot_json()
            await ws_hub.broadcast("topology", graph)
        except Exception:
            pass
        return published

    def _detect_anomalies(
        self,
        events: list[NormalizedEvent],
        prom_raw: list[dict],
        pods: list[dict],
    ) -> list[NormalizedEvent]:
        anomalies: list[NormalizedEvent] = []
        for raw in prom_raw:
            if raw.get("breached"):
                anomalies.append(self._normalizer.normalize(
                    {**raw, "anomaly_type": "metric_threshold_breach"},
                    event_type=EventType.ANOMALY,
                    source="anomaly-detector",
                    stream_kind=StreamKind.ANOMALY,
                ))
        for pod in pods:
            if pod.get("restart_count", 0) >= self._settings.anomaly_restart_burst_count:
                anomalies.append(self._normalizer.normalize(
                    {**pod, "anomaly_type": "restart_burst"},
                    event_type=EventType.ANOMALY,
                    source="anomaly-detector",
                    stream_kind=StreamKind.ANOMALY,
                ))
            if pod.get("phase") in ("Failed",) or "CrashLoop" in str(pod.get("reason", "")):
                anomalies.append(self._normalizer.normalize(
                    {**pod, "anomaly_type": "pod_failure"},
                    event_type=EventType.ANOMALY,
                    source="anomaly-detector",
                    stream_kind=StreamKind.ANOMALY,
                ))
        return events + anomalies
