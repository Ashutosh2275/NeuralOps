"""
Base tool interfaces and data models for SentinelOps AI Autonomous Investigation Engine.
Strictly read-only operational tools with permission checks, timeout control, and structured outputs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class PermissionLevel(str, Enum):
    READ_ONLY = "read_only"
    SAFE_ACTION = "safe_action"
    HIGH_PRIVILEGE = "high_privilege"


@dataclass
class ToolMetadata:
    """Metadata describing tool capabilities and input parameter schema."""
    name: str
    description: str
    parameters: dict[str, Any]
    permission: PermissionLevel = PermissionLevel.READ_ONLY
    timeout_seconds: float = 10.0
    category: str = "operational"  # k8s, observability, topology, incidents, rag
    required_params: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """Standardized output structure for any tool call in SentinelOps AI."""
    tool_name: str
    success: bool
    data: Any
    errors: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    source: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": self.data,
            "errors": self.errors,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "source": self.source,
            "metadata": self.metadata,
            "cached": self.cached,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolResult":
        return cls(
            tool_name=data.get("tool_name", ""),
            success=data.get("success", False),
            data=data.get("data"),
            errors=data.get("errors", []),
            execution_time_ms=data.get("execution_time_ms", 0.0),
            source=data.get("source", "system"),
            metadata=data.get("metadata", {}),
            cached=data.get("cached", False),
        )


@dataclass
class ToolCallRecord:
    """Audit log item representing an invoked tool during an investigation."""
    call_id: str = field(default_factory=lambda: str(uuid4()))
    tool_name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    result: Optional[ToolResult] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result.to_dict() if self.result else None,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": round(self.duration_ms, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCallRecord":
        started_at = datetime.fromisoformat(data["started_at"]) if "started_at" in data else datetime.now(timezone.utc)
        completed_at = datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        res_data = data.get("result")
        result = ToolResult.from_dict(res_data) if res_data else None
        return cls(
            call_id=data.get("call_id", str(uuid4())),
            tool_name=data.get("tool_name", ""),
            arguments=data.get("arguments", {}),
            result=result,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=data.get("duration_ms", 0.0),
        )


class BaseTool(ABC):
    """Abstract base class for all SentinelOps investigation tools."""

    def __init__(self, metadata: ToolMetadata) -> None:
        self.metadata = metadata

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def permission(self) -> PermissionLevel:
        return self.metadata.permission

    def validate_args(self, kwargs: dict[str, Any]) -> list[str]:
        """Validate provided arguments against required parameters and schema."""
        errors: list[str] = []
        for req in self.metadata.required_params:
            if req not in kwargs or kwargs[req] is None or kwargs[req] == "":
                errors.append(f"Missing required parameter '{req}' for tool '{self.name}'")

        # Security validation: reject command injection and path traversal sequences
        dangerous_patterns = [";", "&&", "||", "|", "`", "$(", "${", "../", "..\\", "\n", "\r", ">", "<"]
        for k, v in kwargs.items():
            if isinstance(v, str):
                if any(p in v for p in dangerous_patterns):
                    errors.append(f"Security validation failed: argument '{k}' contains prohibited injection sequence or path traversal.")
        return errors


    @abstractmethod
    async def run(self, **kwargs: Any) -> ToolResult:
        """Execute tool with supplied arguments. Must be idempotent and safe."""
        pass
