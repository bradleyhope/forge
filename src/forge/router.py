"""AI Router for intelligent model selection"""
import logging
from enum import Enum
from dataclasses import dataclass
from forge.config.settings import ForgeSettings

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

@dataclass
class RoutingDecision:
    model: str
    provider: str
    reasoning: str
    estimated_cost: float

class AIRouter:
    """Routes tasks to optimal LLM based on complexity and requirements."""
    
    COMPLEXITY_TO_MODEL = {
        TaskComplexity.SIMPLE: "claude-haiku-3.5",
        TaskComplexity.MODERATE: "claude-sonnet-4",
        TaskComplexity.COMPLEX: "claude-sonnet-4",
        TaskComplexity.EXPERT: "claude-opus-4",
    }
    
    def __init__(self, settings: ForgeSettings):
        self.settings = settings
    
    def route(self, task_description: str, complexity: TaskComplexity = TaskComplexity.MODERATE) -> RoutingDecision:
        model_name = self.COMPLEXITY_TO_MODEL.get(complexity, self.settings.default_model)
        model_config = self.settings.models.get(model_name)
        
        return RoutingDecision(
            model=model_name,
            provider=model_config.provider if model_config else "anthropic",
            reasoning=f"Selected {model_name} for {complexity.value} task",
            estimated_cost=0.01,
        )
