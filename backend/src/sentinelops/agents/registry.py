from sentinelops.agents.base import BaseAgent
from sentinelops.agents.cpu_agent import CPUAgent
from sentinelops.agents.correlation_agent import CorrelationAgent
from sentinelops.agents.log_agent import LogIntelligenceAgent
from sentinelops.agents.memory_agent import MemoryAgent
from sentinelops.agents.rca_agent import RCAAgent
from sentinelops.agents.recommendation_agent import RecommendationAgent
from sentinelops.agents.storage_agent import StorageAgent


class AgentRegistry:
    _agents: dict[str, type[BaseAgent]] = {
        "cpu": CPUAgent,
        "memory": MemoryAgent,
        "storage": StorageAgent,
        "log": LogIntelligenceAgent,
        "correlation": CorrelationAgent,
        "rca": RCAAgent,
        "recommendation": RecommendationAgent,
    }

    @classmethod
    def get(cls, agent_type: str) -> BaseAgent:
        agent_cls = cls._agents.get(agent_type)
        if not agent_cls:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_cls()

    @classmethod
    def all_types(cls) -> list[str]:
        return list(cls._agents.keys())

    @classmethod
    def create_all(cls) -> list[BaseAgent]:
        return [cls() for cls in cls._agents.values()]
