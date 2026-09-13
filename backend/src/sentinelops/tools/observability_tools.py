"""
Observability read-only tools for Prometheus and Loki.
Queries real metrics/logs or returns structured degradation info with explicit provenance.
"""
from __future__ import annotations

from typing import Any, Optional

from sentinelops.collectors.loki_collector import LokiCollector
from sentinelops.collectors.prometheus_collector import PrometheusCollector
from sentinelops.core.logging import get_logger
from sentinelops.rag.context import PromptSanitizer
from sentinelops.tools.base import BaseTool, PermissionLevel, ToolMetadata, ToolResult

log = get_logger(__name__)


class QueryPrometheusMetricTool(BaseTool):
    """Executes a PromQL query or retrieves standard pod/node metrics."""

    def __init__(self, collector: Optional[PrometheusCollector] = None) -> None:
        super().__init__(
            ToolMetadata(
                name="query_prometheus_metric",
                description="Queries Prometheus metrics (e.g. CPU, memory, restart rate, PVC saturation) for a target resource.",
                parameters={
                    "namespace": {"type": "string", "description": "Kubernetes namespace"},
                    "metric_name": {"type": "string", "description": "Metric name (cpu_percent, memory_percent, restart_total, pvc_usage_percent)"},
                    "target_resource": {"type": "string", "description": "Optional pod or node name filter"},
                },
                required_params=["namespace", "metric_name"],
                category="observability",
                permission=PermissionLevel.READ_ONLY,
                timeout_seconds=8.0,
            )
        )
        self._collector = collector or PrometheusCollector()

    async def run(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query") or kwargs.get("promql")
        if query:
            try:
                results = await self._collector.query_promql(str(query))
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data={"query": str(query), "results": results, "count": len(results)},
                    source="prometheus_collector",
                )
            except Exception as e:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    data=None,
                    errors=[f"PromQL query failed: {str(e)}"],
                    source="prometheus_collector",
                )

        namespace = str(kwargs.get("namespace", "default")).strip()
        metric_name = str(kwargs.get("metric_name", "")).strip()
        target = kwargs.get("target_resource")

        try:
            metrics = await self._collector.collect(namespace)
            matched = [
                m for m in metrics
                if m.get("metric_name") == metric_name or metric_name in m.get("metric_name", "")
            ]

            if target:
                matched = [
                    m for m in matched
                    if m.get("resource") == target
                    or m.get("pod") == target
                    or m.get("pod_name") == target
                    or m.get("service_name") == target
                    or (target and target in str(m.get("pod_name", "")))
                ]

            if not matched:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data={"metrics": [], "count": 0, "status": "no_data_for_criteria"},
                    source="prometheus_collector",
                )

            formatted = [
                {
                    "metric": m.get("metric_name"),
                    "resource": m.get("resource") or m.get("pod") or m.get("pod_name") or m.get("service_name"),
                    "value": m.get("value"),
                    "unit": m.get("unit", ""),
                    "timestamp": str(m.get("timestamp")),
                    "breached": m.get("breached", False),
                }
                for m in matched
            ]

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"metrics": formatted, "count": len(formatted)},
                source="prometheus_collector",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                errors=[f"Prometheus query failed: {str(e)}"],
                source="prometheus_collector",
            )


class QueryLokiLogsTool(BaseTool):
    """Executes a LogQL search or queries error logs for a service/namespace."""

    def __init__(self, collector: Optional[LokiCollector] = None) -> None:
        super().__init__(
            ToolMetadata(
                name="query_loki_logs",
                description="Queries Loki logs for error/exception patterns, panic traces, or specific search keywords.",
                parameters={
                    "namespace": {"type": "string", "description": "Kubernetes namespace"},
                    "search_pattern": {"type": "string", "description": "Log search term or regex (e.g. error, OOMKilled, timeout)"},
                    "limit": {"type": "integer", "description": "Maximum number of log entries to retrieve (default: 30)"},
                },
                required_params=["namespace"],
                category="observability",
                permission=PermissionLevel.READ_ONLY,
                timeout_seconds=8.0,
            )
        )
        self._collector = collector or LokiCollector()

    async def run(self, **kwargs: Any) -> ToolResult:
        namespace = str(kwargs.get("namespace", "default")).strip()
        search_pattern = str(kwargs.get("search_pattern", "error")).strip()
        limit = min(int(kwargs.get("limit", 30)), 100)

        try:
            logs = await self._collector.collect(namespace)
            matched = []

            for l in logs:
                msg = l.get("message") or l.get("log_line", "")
                if search_pattern.lower() in msg.lower() or not search_pattern:
                    sanitized_msg = PromptSanitizer.sanitize(msg)
                    matched.append({
                        "timestamp": str(l.get("timestamp")),
                        "severity": l.get("severity") or l.get("log_level", "info"),
                        "service": l.get("service") or l.get("pod") or l.get("pod_name"),
                        "pattern": l.get("pattern") or (l.get("matched_patterns", [""])[0] if l.get("matched_patterns") else None),
                        "message": sanitized_msg[:500],
                    })

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"logs": matched[:limit], "count": len(matched[:limit]), "total_found": len(matched)},
                source="loki_collector",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                errors=[f"Loki log search failed: {str(e)}"],
                source="loki_collector",
            )
