from sentinelops.collectors.k8s_collector import KubernetesCollector
from sentinelops.collectors.loki_collector import LokiCollector
from sentinelops.collectors.metrics_pipeline import MetricsPipeline
from sentinelops.collectors.prometheus_collector import PrometheusCollector

__all__ = [
    "KubernetesCollector",
    "LokiCollector",
    "MetricsPipeline",
    "PrometheusCollector",
]


def get_event_collector(bus):  # noqa: ANN001
    from sentinelops.collectors.event_collector import EventCollector
    return EventCollector(bus)
