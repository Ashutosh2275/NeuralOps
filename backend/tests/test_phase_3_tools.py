"""
Phase 3 Tool Calling Unit Tests.
Verifies tool registration, execution, timeout enforcement, argument validation, and error normalization.
"""
from __future__ import annotations

import asyncio
import pytest

from sentinelops.tools.base import BaseTool, PermissionLevel, ToolMetadata, ToolResult
from sentinelops.tools.incident_tools import SearchPastIncidentsTool
from sentinelops.tools.k8s_tools import (
    GetDeploymentStatusTool,
    GetK8sEventsTool,
    GetPodLogsTool,
    GetPodStatusTool,
)
from sentinelops.tools.observability_tools import QueryLokiLogsTool, QueryPrometheusMetricTool
from sentinelops.tools.rag_tool import SearchKnowledgeBaseTool
from sentinelops.tools.registry import ToolRegistry, get_tool_registry
from sentinelops.tools.topology_tools import CalculateBlastRadiusTool, GetServiceDependenciesTool


class SlowTool(BaseTool):
    """Test tool that simulates a hung or slow operation."""
    def __init__(self) -> None:
        super().__init__(
            ToolMetadata(
                name="slow_tool",
                description="Simulates slow execution",
                parameters={},
                timeout_seconds=0.2,
            )
        )

    async def run(self, **kwargs):
        await asyncio.sleep(1.0)
        return ToolResult(tool_name=self.name, success=True, data="finished")


class FailingTool(BaseTool):
    """Test tool that raises an unexpected exception."""
    def __init__(self) -> None:
        super().__init__(
            ToolMetadata(
                name="failing_tool",
                description="Simulates internal error",
                parameters={},
            )
        )

    async def run(self, **kwargs):
        raise RuntimeError("Disk connection dropped")


@pytest.mark.asyncio
async def test_tool_registry_registration_and_listing():
    reg = ToolRegistry()
    tool = GetPodStatusTool()
    reg.register(tool)

    assert reg.get("get_pod_status") is not None
    assert len(reg.list_tools()) == 1
    assert reg.list_tools()[0]["name"] == "get_pod_status"

    definitions = reg.get_tool_definitions_for_llm()
    assert len(definitions) == 1
    assert definitions[0]["function"]["name"] == "get_pod_status"


@pytest.mark.asyncio
async def test_tool_registry_argument_validation():
    reg = ToolRegistry()
    reg.register(GetPodStatusTool())

    # Missing pod_name
    record = await reg.execute("get_pod_status", {"namespace": "default"})
    assert record.result.success is False
    assert any("Missing required parameter 'pod_name'" in e for e in record.result.errors)


@pytest.mark.asyncio
async def test_tool_registry_timeout_handling():
    reg = ToolRegistry()
    reg.register(SlowTool())

    record = await reg.execute("slow_tool", {})
    assert record.result.success is False
    assert any("timed out" in e for e in record.result.errors)


@pytest.mark.asyncio
async def test_tool_registry_exception_normalization():
    reg = ToolRegistry()
    reg.register(FailingTool())

    record = await reg.execute("failing_tool", {})
    assert record.result.success is False
    assert any("RuntimeError: Disk connection dropped" in e for e in record.result.errors)


@pytest.mark.asyncio
async def test_k8s_tools_execution():
    pod_tool = GetPodStatusTool()
    res = await pod_tool.run(namespace="default", pod_name="auth-service-pod-1")
    assert isinstance(res, ToolResult)
    assert res.tool_name == "get_pod_status"

    events_tool = GetK8sEventsTool()
    res_events = await events_tool.run(namespace="default")
    assert res_events.success is True
    assert "events" in res_events.data

    dep_tool = GetDeploymentStatusTool()
    res_dep = await dep_tool.run(namespace="default", deployment_name="auth-service")
    assert isinstance(res_dep, ToolResult)


@pytest.mark.asyncio
async def test_observability_tools_execution():
    prom_tool = QueryPrometheusMetricTool()
    res_prom = await prom_tool.run(namespace="default", metric_name="cpu_percent")
    assert res_prom.success is True
    assert "metrics" in res_prom.data

    loki_tool = QueryLokiLogsTool()
    res_loki = await loki_tool.run(namespace="default", search_pattern="error")
    assert res_loki.success is True
    assert "logs" in res_loki.data


@pytest.mark.asyncio
async def test_topology_and_rag_tools():
    topo_tool = GetServiceDependenciesTool()
    res_topo = await topo_tool.run(namespace="default", service_name="payment-service")
    assert isinstance(res_topo, ToolResult)

    rag_tool = SearchKnowledgeBaseTool()
    res_rag = await rag_tool.run(query="CrashLoopBackOff container failing")
    assert res_rag.success is True
    assert "context_text" in res_rag.data
