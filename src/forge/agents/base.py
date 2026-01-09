"""Base Agent Classes"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class AgentDefinition:
    name: str
    description: str
    prompt_template: str = ""
    model: str = "claude-sonnet-4-20250514"
    tools: list[str] = field(default_factory=list)
    max_turns: int = 50
    capabilities: list[str] = field(default_factory=list)
    focus_areas: list[str] = field(default_factory=list)
    
    def render_prompt(self, context: dict[str, Any] | None = None) -> str:
        from jinja2 import Template
        template = Template(self.prompt_template)
        return template.render(**(context or {}))

@dataclass
class Task:
    id: str
    description: str
    agent_name: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)

@dataclass
class AgentResult:
    success: bool
    output: str
    error: str | None = None
    artifacts: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    tokens_used: int = 0
    turns_used: int = 0

class BaseAgent(ABC):
    def __init__(self, definition: AgentDefinition):
        self.definition = definition
        self.name = definition.name
        self.logger = logging.getLogger(f"forge.agents.{self.name}")
    
    @abstractmethod
    async def execute(self, task: Task) -> AgentResult:
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"
