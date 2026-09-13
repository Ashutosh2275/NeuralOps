"""
Default tool suite initialization and factory functions for SentinelOps AI.
"""
from __future__ import annotations

from sentinelops.tools.base import PermissionLevel
from sentinelops.tools.incident_tools import SearchPastIncidentsTool
from sentinelops.tools.k8s_tools import (
    GetContainerStatusTool,
    GetDeploymentStatusTool,
    GetK8sEventsTool,
    GetNamespaceResourcesTool,
    GetPodDetailsTool,
    GetPodLogsTool,
    GetPodStatusTool,
    GetResourceUsageTool,
    GetServiceDetailsTool,
    GetWorkloadHealthTool,
)
from sentinelops.tools.observability_tools import QueryLokiLogsTool, QueryPrometheusMetricTool
from sentinelops.tools.rag_tool import SearchKnowledgeBaseTool
from sentinelops.tools.registry import ToolRegistry, get_tool_registry
from sentinelops.tools.topology_tools import CalculateBlastRadiusTool, GetServiceDependenciesTool


def register_default_tools(registry: ToolRegistry | None = None) -> ToolRegistry:
    """Register all standard read-only operational tools into the registry."""
    reg = registry or get_tool_registry()

    # K8s
    reg.register(GetPodStatusTool())
    reg.register(GetPodDetailsTool())
    reg.register(GetContainerStatusTool())
    reg.register(GetPodLogsTool())
    reg.register(GetK8sEventsTool())
    reg.register(GetDeploymentStatusTool())
    reg.register(GetServiceDetailsTool())
    reg.register(GetNamespaceResourcesTool())
    reg.register(GetResourceUsageTool())
    reg.register(GetWorkloadHealthTool())

    # Observability
    reg.register(QueryPrometheusMetricTool())
    reg.register(QueryLokiLogsTool())

    # Topology
    reg.register(GetServiceDependenciesTool())
    reg.register(CalculateBlastRadiusTool())

    # Incidents & Knowledge
    reg.register(SearchPastIncidentsTool())
    reg.register(SearchKnowledgeBaseTool())

    return reg

