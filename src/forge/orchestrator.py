"""Forge Orchestrator - Central brain for multi-agent coordination - BUG FIXED"""
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forge.agents.base import AgentDefinition, AgentResult, Task
from forge.agents.claude_agent import ClaudeAgent
from forge.agents import ALL_AGENTS
from forge.config.settings import ForgeSettings
from forge.utils.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.
    Uses a more accurate approximation: ~4 characters per token for English text.
    This is still an approximation - for exact counts, use tiktoken or the API.
    """
    if not text:
        return 0
    # More accurate: ~4 chars per token for English, ~2-3 for code
    # We use 3.5 as a middle ground
    return max(1, int(len(text) / 3.5))


@dataclass
class WorkflowResult:
    success: bool
    results: dict[str, AgentResult] = field(default_factory=dict)
    error: str | None = None
    steps_completed: int = 0
    total_steps: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0


class Forge:
    """Central orchestrator for the Forge multi-agent system."""
    
    def __init__(
        self,
        settings: ForgeSettings | None = None,
        working_dir: Path | None = None,
    ):
        self.settings = settings or ForgeSettings()
        self.working_dir = working_dir or self.settings.project_dir
        self.cost_tracker = CostTracker(budget_usd=self.settings.budget_usd)
        self.logger = logging.getLogger("forge.orchestrator")
        self._agents: dict[str, ClaudeAgent] = {}
    
    def list_agents(self) -> list[str]:
        """List all available agent names."""
        return list(ALL_AGENTS.keys())
    
    def get_agent(self, name: str) -> ClaudeAgent | None:
        """Get or create an agent by name."""
        if name not in ALL_AGENTS:
            self.logger.warning(f"Agent not found: {name}")
            return None
        
        if name not in self._agents:
            definition = ALL_AGENTS[name]
            self._agents[name] = ClaudeAgent(
                definition=definition,
                settings=self.settings,
                working_dir=self.working_dir,
            )
        
        return self._agents[name]
    
    async def analyze(self, target: Path) -> AgentResult:
        """Run analysis on a target directory."""
        agent = self.get_agent("backend_analyzer")
        if not agent:
            return AgentResult(success=False, output="", error="Agent not found")
        
        task = Task(
            id=str(uuid.uuid4()),
            description=f"Analyze the codebase at {target} for bugs, security issues, performance problems, and code quality issues. Provide a detailed report.",
            agent_name="backend_analyzer",
            context={"target": str(target)},
        )
        
        result = await agent.execute(task)
        
        # Track cost with proper token estimation
        if result.tokens_used == 0 and result.output:
            # Estimate tokens if not provided by SDK
            result.tokens_used = estimate_tokens(result.output)
        
        self.cost_tracker.record(
            model=agent.definition.model,
            input_tokens=result.tokens_used // 2,  # Rough split
            output_tokens=result.tokens_used // 2,
        )
        
        return result
    
    async def fix(self, issue: str, target: Path) -> AgentResult:
        """Fix a specific issue in the codebase."""
        agent = self.get_agent("debugger")
        if not agent:
            return AgentResult(success=False, output="", error="Agent not found")
        
        task = Task(
            id=str(uuid.uuid4()),
            description=f"Fix the following issue in {target}: {issue}",
            agent_name="debugger",
            context={"target": str(target), "issue": issue},
        )
        
        result = await agent.execute(task)
        
        if result.tokens_used == 0 and result.output:
            result.tokens_used = estimate_tokens(result.output)
        
        self.cost_tracker.record(
            model=agent.definition.model,
            input_tokens=result.tokens_used // 2,
            output_tokens=result.tokens_used // 2,
        )
        
        return result
    
    async def run(self, goal: str, target: Path) -> WorkflowResult:
        """Run a complete workflow based on a high-level goal."""
        self.logger.info(f"Starting workflow: {goal}")
        
        # Decompose goal into steps
        steps = self._decompose_goal(goal)
        
        workflow_result = WorkflowResult(
            success=True,
            total_steps=len(steps),
        )
        
        for i, (agent_name, task_description) in enumerate(steps):
            self.logger.info(f"Step {i+1}/{len(steps)}: {agent_name}")
            
            agent = self.get_agent(agent_name)
            if not agent:
                workflow_result.success = False
                workflow_result.error = f"Agent not found: {agent_name}"
                break
            
            task = Task(
                id=str(uuid.uuid4()),
                description=task_description,
                agent_name=agent_name,
                context={"target": str(target), "goal": goal},
            )
            
            result = await agent.execute(task)
            
            if result.tokens_used == 0 and result.output:
                result.tokens_used = estimate_tokens(result.output)
            
            workflow_result.results[agent_name] = result
            workflow_result.steps_completed += 1
            workflow_result.total_cost_usd += result.cost_usd
            workflow_result.total_tokens += result.tokens_used
            
            self.cost_tracker.record(
                model=agent.definition.model,
                input_tokens=result.tokens_used // 2,
                output_tokens=result.tokens_used // 2,
            )
            
            if not result.success:
                workflow_result.success = False
                workflow_result.error = result.error
                break
            
            # Check budget
            if self.cost_tracker.is_over_budget():
                workflow_result.success = False
                workflow_result.error = "Budget exceeded"
                break
        
        return workflow_result
    
    def _decompose_goal(self, goal: str) -> list[tuple[str, str]]:
        """Decompose a high-level goal into agent tasks."""
        goal_lower = goal.lower()
        
        steps = []
        
        # Analysis phase
        if any(word in goal_lower for word in ["analyze", "review", "check", "audit"]):
            steps.append(("backend_analyzer", f"Analyze the codebase: {goal}"))
        
        # Security check
        if any(word in goal_lower for word in ["security", "vulnerab", "safe"]):
            steps.append(("security_analyzer", f"Check for security issues: {goal}"))
        
        # Fix/improve phase
        if any(word in goal_lower for word in ["fix", "debug", "repair"]):
            steps.append(("debugger", f"Fix issues: {goal}"))
        
        if any(word in goal_lower for word in ["improve", "refactor", "optimize"]):
            steps.append(("improver", f"Improve code: {goal}"))
        
        # Testing phase
        if any(word in goal_lower for word in ["test", "verify"]):
            steps.append(("tester", f"Create and run tests: {goal}"))
        
        # Documentation phase
        if any(word in goal_lower for word in ["document", "readme", "comment"]):
            steps.append(("documenter", f"Update documentation: {goal}"))
        
        # Default: analyze then improve
        if not steps:
            steps = [
                ("backend_analyzer", f"Analyze the codebase for: {goal}"),
                ("improver", f"Implement improvements based on analysis: {goal}"),
            ]
        
        return steps
    
    def get_cost_summary(self) -> dict[str, Any]:
        """Get cost tracking summary."""
        return self.cost_tracker.get_summary()
    
    def cleanup(self):
        """Clean up resources."""
        self._agents.clear()
        self.logger.info("Forge cleanup complete")
