"""
Unified Tool Registry for SentinelOps AI Autonomous Investigation Engine.
Provides thread-safe tool registration, argument schema validation, timeout enforcement,
and execution metrics.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

from sentinelops.core.logging import get_logger
from sentinelops.tools.base import BaseTool, PermissionLevel, ToolCallRecord, ToolResult

log = get_logger(__name__)


class ToolRegistry:
    """Registry managing available investigation tools with permission & safety guarantees."""

    def __init__(self, allowed_permission: PermissionLevel = PermissionLevel.READ_ONLY) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._allowed_permission = allowed_permission

    def register(self, tool: BaseTool) -> None:
        """Register a tool. Prevents non-read-only tools if restricted."""
        if self._allowed_permission == PermissionLevel.READ_ONLY and tool.permission != PermissionLevel.READ_ONLY:
            log.warning(
                "tool_registration_denied_permission",
                tool=tool.name,
                permission=tool.permission.value,
            )
            raise PermissionError(
                f"Tool '{tool.name}' requires permission '{tool.permission.value}' "
                f"which exceeds permitted '{self._allowed_permission.value}'"
            )

        self._tools[tool.name] = tool
        log.debug("tool_registered", tool=tool.name, category=tool.metadata.category)

    def unregister(self, name: str) -> None:
        """Unregister a tool by name."""
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List metadata for all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.metadata.description,
                "parameters": t.metadata.parameters,
                "permission": t.permission.value,
                "timeout_seconds": t.metadata.timeout_seconds,
                "category": t.metadata.category,
                "required_params": t.metadata.required_params,
            }
            for t in self._tools.values()
        ]

    def get_tool_definitions_for_llm(self) -> list[dict[str, Any]]:
        """Format registered tools for LLM tool calling schema (OpenAI / Ollama format)."""
        definitions = []
        for t in self._tools.values():
            definitions.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.metadata.description,
                    "parameters": {
                        "type": "object",
                        "properties": t.metadata.parameters,
                        "required": t.metadata.required_params,
                    },
                },
            })
        return definitions

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolCallRecord:
        """
        Execute tool with validation, timeouts, error normalization, and audit record generation.
        """
        record = ToolCallRecord(tool_name=tool_name, arguments=arguments)
        start_time = time.perf_counter()

        tool = self._tools.get(tool_name)
        if not tool:
            duration = (time.perf_counter() - start_time) * 1000
            record.duration_ms = duration
            record.completed_at = record.started_at
            record.result = ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                errors=[f"Tool '{tool_name}' is not registered."],
                execution_time_ms=duration,
                source="tool_registry",
            )
            return record

        # Validate arguments
        validation_errors = tool.validate_args(arguments)
        if validation_errors:
            duration = (time.perf_counter() - start_time) * 1000
            record.duration_ms = duration
            record.completed_at = record.started_at
            record.result = ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                errors=validation_errors,
                execution_time_ms=duration,
                source="tool_registry",
            )
            return record

        # Execute with timeout
        timeout = tool.metadata.timeout_seconds
        try:
            result = await asyncio.wait_for(tool.run(**arguments), timeout=timeout)
            duration = (time.perf_counter() - start_time) * 1000
            result.execution_time_ms = duration
            record.result = result
        except asyncio.TimeoutError:
            duration = (time.perf_counter() - start_time) * 1000
            record.result = ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                errors=[f"Tool '{tool_name}' timed out after {timeout}s."],
                execution_time_ms=duration,
                source="tool_registry",
            )
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            record.result = ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                errors=[f"Tool execution failed: {type(e).__name__}: {str(e)}"],
                execution_time_ms=duration,
                source="tool_registry",
            )

        # Redact any sensitive credentials in result data
        if record.result and record.result.data:
            from sentinelops.security.redactor import get_secret_redactor
            record.result.data = get_secret_redactor().redact_data(record.result.data)

        record.duration_ms = (time.perf_counter() - start_time) * 1000

        # Audit trail recording
        try:
            from sentinelops.security.audit import get_audit_trail
            get_audit_trail().log_event(
                action="tool_execution",
                selected_tools=[tool_name],
                arguments=arguments,
                execution_status="success" if (record.result and record.result.success) else "failed",
                duration_ms=record.duration_ms,
                errors=record.result.errors if record.result else [],
            )
        except Exception:
            pass

        return record


# Global singleton registry
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Retrieve or initialize global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        from sentinelops.tools import register_default_tools
        register_default_tools(_global_registry)
    return _global_registry
