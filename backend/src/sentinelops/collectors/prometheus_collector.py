import asyncio
from datetime import datetime
from typing import Any

import httpx

from sentinelops.config import Settings, get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import EventType
from sentinelops.pipeline.normalized_event import StreamKind
from sentinelops.pipeline.normalizer import EventNormalizer

log = get_logger(__name__)

PROMETHEUS_QUERIES: dict[str, str] = {
    "cpu_usage_cores": 'sum(rate(container_cpu_usage_seconds_total{pod!=""}[5m])) by (pod, namespace, node)',
    "cpu_percent": (
        'sum(rate(container_cpu_usage_seconds_total{pod!=""}[5m])) by (pod, namespace) '
        "/ clamp_min(sum(kube_pod_container_resource_limits{resource=\"cpu\", pod!=\"\"}) by (pod, namespace), 0.001) * 100"
    ),
    "memory_usage_bytes": 'sum(container_memory_working_set_bytes{pod!=""}) by (pod, namespace, node)',
    "memory_percent": (
        "sum(container_memory_working_set_bytes{pod!=\"\"}) by (pod, namespace) "
        "/ clamp_min(sum(container_spec_memory_limit_bytes{pod!=\"\"}) by (pod, namespace), 1) * 100"
    ),
    "restart_total": "sum(kube_pod_container_status_restarts_total) by (pod, namespace, container)",
    "network_rx_bytes": "sum(rate(container_network_receive_bytes_total{pod!=\"\"}[5m])) by (pod, namespace)",
    "network_tx_bytes": "sum(rate(container_network_transmit_bytes_total{pod!=\"\"}[5m])) by (pod, namespace)",
    "pod_ready": 'kube_pod_status_ready{condition="true"}',
    "container_cpu_usage": 'sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod, namespace, container)',
    "node_cpu_percent": '100 - (avg by (node) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    "node_memory_percent": (
        "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100"
    ),
    "pvc_usage_percent": (
        "kubelet_volume_stats_used_bytes / clamp_min(kubelet_volume_stats_capacity_bytes, 1) * 100"
    ),
}


class PrometheusCollector:
    """Async Prometheus collector via HTTP API (fast fallback to demo data)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._normalizer = EventNormalizer()
        self._base_url = self._settings.prometheus_url.rstrip("/")

    async def collect(self, namespace: str | None = None) -> list[dict[str, Any]]:
        ns = namespace or self._settings.k8s_namespace
        try:
            raw = await self._collect_async(ns)
            if raw:
                return raw
            return self._demo_metrics(ns)
        except Exception as e:
            log.warning("prometheus_collect_failed", error=str(e))
            return self._demo_metrics(ns)

    async def _collect_async(self, namespace: str) -> list[dict[str, Any]]:
        timeout = httpx.Timeout(self._settings.prometheus_query_timeout_seconds)
        raw_events: list[dict[str, Any]] = []
        now = datetime.utcnow()

        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [
                self._query_one(client, metric_name, query, namespace, now)
                for metric_name, query in PROMETHEUS_QUERIES.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    raw_events.extend(result)

        log.info("prometheus_collected", count=len(raw_events), namespace=namespace)
        return raw_events

    async def _query_one(
        self,
        client: httpx.AsyncClient,
        metric_name: str,
        query: str,
        namespace: str,
        now: datetime,
    ) -> list[dict[str, Any]]:
        url = f"{self._base_url}/api/v1/query"
        try:
            resp = await client.get(url, params={"query": query})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.debug("prom_query_skip", metric=metric_name, error=str(e))
            return []

        events: list[dict[str, Any]] = []
        for item in data.get("data", {}).get("result", []):
            metric = item.get("metric", {})
            value_raw = item.get("value", [None, "0"])
            try:
                value = float(value_raw[1])
            except (IndexError, TypeError, ValueError):
                value = 0.0

            item_ns = metric.get("namespace", namespace)
            if namespace != "*" and "namespace" in metric and item_ns != namespace:
                continue

            pod_name = metric.get("pod") or metric.get("persistentvolumeclaim")
            threshold = self._threshold_for(metric_name)
            breached = threshold is not None and value > threshold

            events.append({
                "timestamp": now,
                "namespace": item_ns,
                "pod_name": pod_name,
                "node_name": metric.get("node"),
                "service_name": metric.get("service") or metric.get("app"),
                "metric_name": metric_name,
                "metric_value": round(value, 4),
                "metric_unit": self._unit_for(metric_name),
                "value": round(value, 4),
                "threshold": threshold,
                "breached": breached,
                "container": metric.get("container"),
                "labels": {k: v for k, v in metric.items() if k not in ("pod", "namespace", "node")},
            })
        return events

    def normalize_batch(self, raw_events: list[dict[str, Any]], trace_id: str) -> list:
        from sentinelops.pipeline.normalized_event import NormalizedEvent

        return [
            self._normalizer.normalize(
                raw,
                event_type=EventType.METRIC,
                source="prometheus-collector",
                stream_kind=StreamKind.METRICS,
                trace_id=trace_id,
            )
            for raw in raw_events
        ]

    def _threshold_for(self, metric_name: str) -> float | None:
        if "cpu" in metric_name and "percent" in metric_name:
            return self._settings.anomaly_cpu_threshold_percent
        if "memory" in metric_name and "percent" in metric_name:
            return self._settings.anomaly_memory_threshold_percent
        if "pvc" in metric_name:
            return 85.0
        return None

    def _unit_for(self, metric_name: str) -> str:
        if "percent" in metric_name:
            return "percent"
        if "bytes" in metric_name:
            return "bytes"
        if "restart" in metric_name:
            return "count"
        return "value"

    def _demo_metrics(self, namespace: str) -> list[dict[str, Any]]:
        now = datetime.utcnow()
        demo = [
            ("order-service", "cpu_percent", 45.0),
            ("payment-service", "cpu_percent", 72.0),
            ("inventory-service", "cpu_percent", 94.0),
            ("inventory-service", "memory_percent", 91.0),
            ("inventory-service", "restart_total", 5.0),
            ("postgres-0", "memory_percent", 68.0),
            ("postgres-0", "pvc_usage_percent", 82.0),
        ]
        return [
            {
                "timestamp": now,
                "namespace": namespace,
                "pod_name": pod,
                "metric_name": metric,
                "metric_value": val,
                "value": val,
                "breached": val > 85,
                "threshold": 85.0,
                "metric_unit": "percent",
            }
            for pod, metric, val in demo
        ]
