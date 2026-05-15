from sentinelops.config import Settings, get_settings
from sentinelops.events.schemas import Severity
from sentinelops.pipeline.normalized_event import NormalizedEvent


class SeverityEngine:
    """Threshold scoring, cascading escalation, dependency-aware amplification."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._dependency_failures: dict[str, int] = {}

    def score(self, event: NormalizedEvent) -> NormalizedEvent:
        severity = self._threshold_score(event)
        severity = self._cascade_escalation(severity)
        event.severity = severity
        event.severity = self._dependency_escalation(event)
        event.severity = self._anomaly_amplification(event)
        return event

    def _threshold_score(self, event: NormalizedEvent) -> Severity:
        if event.metric_name and event.metric_value is not None:
            if "cpu" in event.metric_name.lower():
                if event.metric_value >= self._settings.anomaly_cpu_threshold_percent:
                    return Severity.CRITICAL
                if event.metric_value >= self._settings.anomaly_cpu_threshold_percent * 0.75:
                    return Severity.WARNING
            if "memory" in event.metric_name.lower():
                if event.metric_value >= self._settings.anomaly_memory_threshold_percent:
                    return Severity.CRITICAL
                if event.metric_value >= self._settings.anomaly_memory_threshold_percent * 0.8:
                    return Severity.WARNING

        restarts = event.payload.get("restart_count", 0)
        if restarts >= self._settings.anomaly_restart_burst_count:
            return Severity.CRITICAL
        if restarts >= 1:
            return Severity.WARNING

        reason = str(event.payload.get("reason", "")).lower()
        if any(p in reason for p in ("crashloop", "oomkilled", "error", "failed")):
            return Severity.CRITICAL
        if any(p in reason for p in ("timeout", "warning", "backoff")):
            return Severity.WARNING

        log_level = str(event.payload.get("log_level", "")).lower()
        if log_level in ("error", "critical", "fatal"):
            return Severity.CRITICAL
        if log_level == "warning":
            return Severity.WARNING

        return event.severity if event.severity != Severity.DEBUG else Severity.INFO

    def _cascade_escalation(self, severity: Severity) -> Severity:
        order = [Severity.INFO, Severity.WARNING, Severity.ERROR, Severity.CRITICAL]
        idx = order.index(severity) if severity in order else 0
        return order[min(idx + 1, len(order) - 1)] if severity in (Severity.WARNING, Severity.ERROR) else severity

    def _dependency_escalation(self, event: NormalizedEvent) -> Severity:
        severity: Severity = event.severity
        upstream_failed = event.dependency_context.get("upstream_failed", 0)
        downstream_impact = event.dependency_context.get("downstream_count", 0)
        if upstream_failed > 0 and severity == Severity.WARNING:
            return Severity.CRITICAL
        if downstream_impact >= 3 and severity in (Severity.INFO, Severity.WARNING):
            return Severity.WARNING
        svc = event.service_name or event.pod_name
        if svc and event.payload.get("phase") in ("Failed", "CrashLoopBackOff"):
            self._dependency_failures[svc] = self._dependency_failures.get(svc, 0) + 1
            if self._dependency_failures[svc] >= 2:
                return Severity.CRITICAL
        return severity

    def _anomaly_amplification(self, event: NormalizedEvent) -> Severity:
        severity = event.severity
        if event.payload.get("anomaly_type") or event.event_type.value == "anomaly":
            if severity == Severity.WARNING:
                return Severity.CRITICAL
            if severity == Severity.INFO:
                return Severity.WARNING
        if event.payload.get("breached"):
            return Severity.CRITICAL
        return severity
