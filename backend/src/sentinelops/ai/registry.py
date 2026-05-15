from typing import Any

from sentinelops.ai.agents import (
    CPUAgent,
    MemoryAgent,
    CorrelationAgent,
    RCAAgent,
    RecommendationAgent,
    SummarizationAgent,
    NPLInfrastructureAssistant,
    StorageAgent,
    NetworkAgent,
    LogsAgent,
)
from sentinelops.ai.base import AIAgent
from sentinelops.core.logging import get_logger

log = get_logger(__name__)


class AIAgentRegistry:
    """Registry and factory for AI agents."""

    _agents: dict[str, type[AIAgent]] = {
        "cpu": CPUAgent,
        "memory": MemoryAgent,
        "correlation": CorrelationAgent,
        "rca": RCAAgent,
        "recommendation": RecommendationAgent,
        "summarization": SummarizationAgent,
        "npl_assistant": NPLInfrastructureAssistant,
        "storage": StorageAgent,
        "network": NetworkAgent,
        "logs": LogsAgent,
    }

    @classmethod
    def get(cls, agent_type: str) -> AIAgent:
        """Get or create an agent instance."""
        agent_cls = cls._agents.get(agent_type)
        if not agent_cls:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_cls()

    @classmethod
    def all_types(cls) -> list[str]:
        """Get all registered agent types."""
        return list(cls._agents.keys())

    @classmethod
    def create_all(cls) -> list[AIAgent]:
        """Create instances of all agents."""
        return [cls.get(agent_type) for agent_type in cls._agents.keys()]


class AISafetyValidator:
    """Validates AI responses for hallucinations and safety."""

    @staticmethod
    def validate_response(
        response: str,
        context_services: list[str],
        context_pods: list[str],
    ) -> tuple[bool, str]:
        """Validate response doesn't invent services/pods."""
        response_lower = response.lower()
        issues = []

        # Check for hallucinated services
        for svc in context_services:
            if svc.lower() in response_lower:
                continue
            if f"'{svc}'" in response or f'"{svc}"' in response:
                continue
            if any(keyword in response_lower for keyword in [svc, f"{svc}-service", f"{svc}-pod"]):
                continue

        # Check for reasonable confidence scores
        import re

        conf_pattern = r"confidence[:\s]+(\d+\.?\d*)"
        conf_match = re.search(conf_pattern, response_lower)
        if conf_match:
            try:
                conf = float(conf_match.group(1))
                if conf > 100 or conf < 0:
                    issues.append(f"Invalid confidence score: {conf}")
                elif conf > 0.95:
                    issues.append("Confidence unreasonably high (>0.95)")
            except ValueError:
                pass

        if issues:
            return False, "; ".join(issues)
        return True, ""

    @staticmethod
    def validate_recommendations(recommendations: list[dict[str, Any]]) -> tuple[bool, str]:
        """Validate recommendations are reasonable."""
        issues = []

        for rec in recommendations:
            if "kubectl" in str(rec).lower():
                if not any(cmd in str(rec) for cmd in ["describe", "scale", "restart", "logs", "delete"]):
                    issues.append("Invalid kubectl command format")

            priority = rec.get("priority", 2)
            if priority not in [1, 2, 3]:
                issues.append(f"Invalid priority: {priority}")

        if issues:
            return False, "; ".join(issues)
        return True, ""
