"""Forge agents module."""
from forge.agents.base import AgentDefinition, AgentResult, BaseAgent, Task
from forge.agents.claude_agent import ClaudeAgent
from forge.agents.specialists import SPECIALIST_AGENTS, get_specialist, list_specialists
from forge.agents.actions import ACTION_AGENTS, get_action_agent, list_action_agents
from forge.agents.infrastructure import INFRASTRUCTURE_AGENTS, get_infrastructure_agent, list_infrastructure_agents

ALL_AGENTS = {**SPECIALIST_AGENTS, **ACTION_AGENTS, **INFRASTRUCTURE_AGENTS}

def get_agent(name: str) -> AgentDefinition | None:
    return ALL_AGENTS.get(name)

def list_all_agents() -> list[str]:
    return list(ALL_AGENTS.keys())

__all__ = [
    "AgentDefinition", "AgentResult", "BaseAgent", "Task", "ClaudeAgent",
    "SPECIALIST_AGENTS", "ACTION_AGENTS", "INFRASTRUCTURE_AGENTS", "ALL_AGENTS",
    "get_specialist", "list_specialists", "get_action_agent", "list_action_agents",
    "get_infrastructure_agent", "list_infrastructure_agents", "get_agent", "list_all_agents",
]
