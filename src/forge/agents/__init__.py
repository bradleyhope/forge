"""Forge agents module."""
from forge.agents.base import AgentDefinition, AgentResult, BaseAgent, Task
from forge.agents.claude_agent import ClaudeAgent
from forge.agents.direct_llm_agent import DirectLLMAgent, MultiLLMOrchestrator
from forge.agents.specialists import SPECIALIST_AGENTS, get_specialist, list_specialists
from forge.agents.actions import ACTION_AGENTS, get_action_agent, list_action_agents
from forge.agents.infrastructure import INFRASTRUCTURE_AGENTS, get_infrastructure_agent, list_infrastructure_agents
from forge.agents.api_architect import API_ARCHITECT
from forge.agents.solution_architect import (
    SOLUTION_ARCHITECT,
    SolutionArchitect,
    WORKFLOW_TEMPLATES,
    get_workflow_template,
    list_workflow_templates,
)
from forge.agents.persona_tester import PERSONA_TESTING_AGENTS, get_persona_testing_agent, list_persona_testing_agents

# Add API Architect to specialists (it's a Tier 1 agent)
EXTENDED_SPECIALISTS = {**SPECIALIST_AGENTS, "api_architect": API_ARCHITECT}

# Meta-agents (orchestration layer)
META_AGENTS = {"solution_architect": SOLUTION_ARCHITECT}

ALL_AGENTS = {**EXTENDED_SPECIALISTS, **ACTION_AGENTS, **INFRASTRUCTURE_AGENTS, **META_AGENTS, **PERSONA_TESTING_AGENTS}

def get_agent(name: str) -> AgentDefinition | None:
    return ALL_AGENTS.get(name)

def list_all_agents() -> list[str]:
    return list(ALL_AGENTS.keys())

__all__ = [
    "AgentDefinition", "AgentResult", "BaseAgent", "Task", "ClaudeAgent",
    "DirectLLMAgent", "MultiLLMOrchestrator",
    "SPECIALIST_AGENTS", "EXTENDED_SPECIALISTS", "ACTION_AGENTS", "INFRASTRUCTURE_AGENTS", 
    "META_AGENTS", "PERSONA_TESTING_AGENTS", "ALL_AGENTS",
    "API_ARCHITECT", "SOLUTION_ARCHITECT", "SolutionArchitect",
    "WORKFLOW_TEMPLATES", "get_workflow_template", "list_workflow_templates",
    "get_specialist", "list_specialists", "get_action_agent", "list_action_agents",
    "get_infrastructure_agent", "list_infrastructure_agents",
    "get_persona_testing_agent", "list_persona_testing_agents",
    "get_agent", "list_all_agents",
]
