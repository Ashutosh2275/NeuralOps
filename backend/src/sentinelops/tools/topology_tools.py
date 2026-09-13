"""
Topology and dependency graph inspection tools for SentinelOps AI Autonomous Investigation.
Reuses DependencyIntelligenceEngine to inspect callers, callees, blast radius, and failure propagation.
"""
from __future__ import annotations

from typing import Any, Optional

from sentinelops.core.logging import get_logger
from sentinelops.engines.dependency import DependencyIntelligenceEngine
from sentinelops.tools.base import BaseTool, PermissionLevel, ToolMetadata, ToolResult

log = get_logger(__name__)


class GetServiceDependenciesTool(BaseTool):
    """Retrieves direct upstream callers and downstream dependencies for a given service."""

    def __init__(self, engine: Optional[DependencyIntelligenceEngine] = None) -> None:
        super().__init__(
            ToolMetadata(
                name="get_service_dependencies",
                description="Retrieves direct upstream callers and downstream dependencies for a service in the topology graph.",
                parameters={
                    "namespace": {"type": "string", "description": "Kubernetes namespace"},
                    "service_name": {"type": "string", "description": "Service name to inspect"},
                },
                required_params=["namespace", "service_name"],
                category="topology",
                permission=PermissionLevel.READ_ONLY,
                timeout_seconds=5.0,
            )
        )
        self._engine = engine or DependencyIntelligenceEngine()

    async def run(self, **kwargs: Any) -> ToolResult:
        namespace = str(kwargs.get("namespace", "default")).strip()
        service_name = str(kwargs.get("service_name", "")).strip()

        try:
            node_id = self._engine.node_id(namespace, "Service", service_name)
            if node_id not in self._engine._graph:
                # Try finding without exact type match
                matched = [n for n in self._engine._graph.nodes if service_name in n]
                if matched:
                    node_id = matched[0]
                else:
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        data=None,
                        errors=[f"Service '{service_name}' not found in dependency graph."],
                        source="dependency_engine",
                    )

            deps = self._engine.get_dependencies(node_id)
            upstream = self._engine.get_dependents(node_id)

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "service": service_name,
                    "namespace": namespace,
                    "downstream_dependencies": deps,
                    "upstream_callers": upstream,
                    "downstream_count": len(deps),
                    "upstream_count": len(upstream),
                },
                source="dependency_engine",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                errors=[f"Failed to get service dependencies: {str(e)}"],
                source="dependency_engine",
            )


class CalculateBlastRadiusTool(BaseTool):
    """Calculates potential blast radius and cascade impact if a service or pod fails."""

    def __init__(self, engine: Optional[DependencyIntelligenceEngine] = None) -> None:
        super().__init__(
            ToolMetadata(
                name="calculate_blast_radius",
                description="Calculates blast radius, affected services, impact score, and cascade paths for a failing component.",
                parameters={
                    "namespace": {"type": "string", "description": "Kubernetes namespace"},
                    "resource_name": {"type": "string", "description": "Name of the service or pod"},
                    "kind": {"type": "string", "description": "Resource kind (Service or Pod, default Service)"},
                },
                required_params=["namespace", "resource_name"],
                category="topology",
                permission=PermissionLevel.READ_ONLY,
                timeout_seconds=6.0,
            )
        )
        self._engine = engine or DependencyIntelligenceEngine()

    async def run(self, **kwargs: Any) -> ToolResult:
        namespace = str(kwargs.get("namespace", "default")).strip()
        resource_name = str(kwargs.get("resource_name", "")).strip()
        kind = str(kwargs.get("kind", "Service")).capitalize()

        try:
            node_id = self._engine.node_id(namespace, kind, resource_name)
            if node_id not in self._engine._graph:
                # Try fallback matching
                matched = [n for n in self._engine._graph.nodes if resource_name in n]
                if matched:
                    node_id = matched[0]
                else:
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        data=None,
                        errors=[f"Node for {kind} '{resource_name}' not found in topology."],
                        source="dependency_engine",
                    )

            blast = self._engine.blast_radius(node_id)
            cascade_path = self._engine.find_cascade_path(node_id)

            blast_dict = blast if isinstance(blast, dict) else blast.__dict__

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "target_node": node_id,
                    "blast_radius": blast_dict,
                    "cascade_path": cascade_path,
                },
                source="dependency_engine",
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                data=None,
                errors=[f"Blast radius calculation failed: {str(e)}"],
                source="dependency_engine",
            )
