import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from sentinelops.config import Settings, get_settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import EventType
from sentinelops.pipeline.normalized_event import StreamKind
from sentinelops.pipeline.normalizer import EventNormalizer

log = get_logger(__name__)

LOG_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("crash_loop", re.compile(r"CrashLoopBackOff|Back-off restarting", re.I), "critical"),
    ("oom_killed", re.compile(r"OOMKilled|out of memory|killed.*memory", re.I), "critical"),
    ("timeout", re.compile(r"timeout|deadline exceeded|context deadline", re.I), "warning"),
    ("exception", re.compile(r"exception|traceback|panic|fatal error", re.I), "critical"),
    ("http_failure", re.compile(r'HTTP/\d\.\d"\s+[45]\d{2}|status[=:]\s*[45]\d{2}', re.I), "warning"),
    ("connection_refused", re.compile(r"connection refused|no route to host|connection reset", re.I), "warning"),
    ("restart_pattern", re.compile(r"restarted|restart count|container.*started", re.I), "info"),
]


class LokiCollector:
    """Async Loki log ingestion with regex anomaly detection."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._normalizer = EventNormalizer()
        self._last_query_end: datetime | None = None

    async def collect(self, namespace: str | None = None) -> list[dict[str, Any]]:
        ns = namespace or self._settings.k8s_namespace
        try:
            return await self._query_loki(ns)
        except Exception as e:
            log.warning("loki_collect_failed", error=str(e))
            return self._demo_logs(ns)

    async def _query_loki(self, namespace: str) -> list[dict[str, Any]]:
        now_ts = time.time()
        start_ts = now_ts - 300  # Default 5 min lookback window
        if self._last_query_end is not None:
            # Overlap by 10s to ensure no dropped events
            start_ts = max(self._last_query_end - 10, now_ts - 3600)
        self._last_query_end = now_ts

        ns_filter = f'{{namespace="{namespace}"}}' if namespace != "*" else '{namespace=~".+"}'
        query = f'{ns_filter} |~ "(?i)(error|exception|oom|crash|timeout|failed|panic)"'

        url = f"{self._settings.loki_url.rstrip('/')}/loki/api/v1/query_range"
        params = {
            "query": query,
            "start": str(int(start_ts * 1e9)),
            "end": str(int(now_ts * 1e9)),
            "limit": self._settings.loki_query_limit,
        }

        async with httpx.AsyncClient(timeout=self._settings.loki_query_timeout_seconds) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        raw_events: list[dict[str, Any]] = []
        for stream in data.get("data", {}).get("result", []):
            stream_labels = stream.get("stream", {})
            pod_name = stream_labels.get("pod", "unknown")
            item_ns = stream_labels.get("namespace", namespace)

            for ts, line in stream.get("values", []):
                patterns = self._match_patterns(line)
                if not patterns:
                    continue
                highest = max(patterns, key=lambda p: ["info", "warning", "critical"].index(p[2]))
                raw_events.append({
                    "timestamp": datetime.utcfromtimestamp(int(ts) / 1e9),
                    "namespace": item_ns,
                    "pod_name": pod_name,
                    "service_name": stream_labels.get("app") or stream_labels.get("service"),
                    "log_line": line,
                    "anomaly_type": highest[0],
                    "log_level": highest[2],
                    "matched_patterns": [p[0] for p in patterns],
                    "labels": stream_labels,
                })

        log.info("loki_collected", count=len(raw_events), namespace=namespace)
        return raw_events

    def _match_patterns(self, line: str) -> list[tuple[str, re.Pattern[str], str]]:
        return [(name, pat, level) for name, pat, level in LOG_PATTERNS if pat.search(line)]

    def normalize_batch(self, raw_events: list[dict[str, Any]], trace_id: str) -> list:
        from sentinelops.pipeline.normalized_event import NormalizedEvent

        normalized: list[NormalizedEvent] = []
        for raw in raw_events:
            event = self._normalizer.normalize(
                raw,
                event_type=EventType.LOG,
                source="loki-collector",
                stream_kind=StreamKind.ANOMALY if raw.get("anomaly_type") else StreamKind.METRICS,
                trace_id=trace_id,
            )
            if raw.get("anomaly_type"):
                event.stream_kind = StreamKind.ANOMALY
            normalized.append(event)
        return normalized

    def _demo_logs(self, namespace: str) -> list[dict[str, Any]]:
        now = datetime.utcnow()
        lines = [
            ("inventory-service", "OOMKilled container inventory-service — memory limit exceeded", "oom_killed"),
            ("inventory-service", "Back-off restarting failed container", "crash_loop"),
            ("payment-service", "HTTP/1.1 503 Service Unavailable upstream timeout", "http_failure"),
            ("order-service", "connection refused to postgres:5432", "connection_refused"),
            ("inventory-service", "java.lang.OutOfMemoryError: Java heap space", "exception"),
        ]
        return [
            {
                "timestamp": now,
                "namespace": namespace,
                "pod_name": pod,
                "log_line": line,
                "anomaly_type": atype,
                "log_level": "critical" if atype in ("oom_killed", "crash_loop", "exception") else "warning",
                "matched_patterns": [atype],
            }
            for pod, line, atype in lines
        ]
