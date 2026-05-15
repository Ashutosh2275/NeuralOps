from datetime import datetime
from uuid import uuid4

import httpx

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import MetricEvent, Severity

log = get_logger(__name__)

PROM_QUERIES = {
    "cpu_percent": 'sum(rate(container_cpu_usage_seconds_total{pod!=""}[5m])) by (pod, namespace) * 100',
    "memory_percent": 'sum(container_memory_working_set_bytes{pod!=""}) by (pod, namespace) / sum(container_spec_memory_limit_bytes{pod!=""}) by (pod, namespace) * 100',
}


class MetricsPipeline:
    """Pulls metrics from Prometheus and emits metric events."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def collect(self, namespace: str = "default") -> list[MetricEvent]:
        events: list[MetricEvent] = []
        try:
            events.extend(await self._query_prometheus("cpu_percent", namespace))
            events.extend(await self._query_prometheus("memory_percent", namespace))
        except Exception as e:
            log.warning("prometheus_unavailable", error=str(e))
            events.extend(self._demo_metrics(namespace))
        return events

    async def _query_prometheus(self, metric_name: str, namespace: str) -> list[MetricEvent]:
        query = PROM_QUERIES.get(metric_name, "")
        url = f"{self._settings.prometheus_url}/api/v1/query"
        async with httpx.AsyncClient(timeout=self._settings.prometheus_query_timeout_seconds) as client:
            resp = await client.get(url, params={"query": query})
            resp.raise_for_status()
            data = resp.json()

        events: list[MetricEvent] = []
        threshold = (
            self._settings.anomaly_cpu_threshold_percent
            if "cpu" in metric_name
            else self._settings.anomaly_memory_threshold_percent
        )

        for result in data.get("data", {}).get("result", []):
            metric = result.get("metric", {})
            value = float(result.get("value", [0, 0])[1])
            pod_name = metric.get("pod", "unknown")
            breached = value > threshold
            events.append(MetricEvent(
                event_id=uuid4(),
                source="metrics-pipeline",
                cluster_id="default",
                namespace=metric.get("namespace", namespace),
                severity=Severity.WARNING if breached else Severity.INFO,
                payload={
                    "pod_name": pod_name,
                    "metric_name": metric_name,
                    "value": round(value, 2),
                    "unit": "percent",
                    "threshold": threshold,
                    "breached": breached,
                },
            ))
        return events

    def _demo_metrics(self, namespace: str) -> list[MetricEvent]:
        demo = [
            ("order-service", "cpu_percent", 45.0, False),
            ("payment-service", "cpu_percent", 72.0, False),
            ("inventory-service", "cpu_percent", 94.0, True),
            ("inventory-service", "memory_percent", 91.0, True),
            ("postgres-0", "memory_percent", 68.0, False),
        ]
        return [
            MetricEvent(
                event_id=uuid4(),
                source="metrics-pipeline-demo",
                cluster_id="default",
                namespace=namespace,
                severity=Severity.WARNING if breached else Severity.INFO,
                payload={
                    "pod_name": pod,
                    "metric_name": metric,
                    "value": val,
                    "unit": "percent",
                    "threshold": 85.0,
                    "breached": breached,
                },
            )
            for pod, metric, val, breached in demo
        ]
