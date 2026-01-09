"""Subagent spawning and orchestration"""
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable
from pathlib import Path

from forge.agents.base import AgentDefinition, AgentResult, Task
from forge.agents.claude_agent import ClaudeAgent
from forge.config.settings import ForgeSettings

logger = logging.getLogger(__name__)

@dataclass
class SubagentTask:
    """A task to be executed by a subagent."""
    id: str
    description: str
    agent_definition: AgentDefinition
    context: dict[str, Any] = field(default_factory=dict)
    parent_task_id: str | None = None

@dataclass
class SubagentResult:
    """Result from a subagent execution."""
    task_id: str
    success: bool
    output: str
    error: str | None = None
    cost_usd: float = 0.0
    tokens_used: int = 0

class SubagentOrchestrator:
    """Orchestrates multiple subagents for parallel or sequential execution."""
    
    def __init__(self, settings: ForgeSettings, working_dir: Path):
        self.settings = settings
        self.working_dir = working_dir
        self.active_subagents: dict[str, asyncio.Task] = {}
        self.results: dict[str, SubagentResult] = {}
        self.total_cost = 0.0
        self.total_tokens = 0
    
    async def spawn(self, subtask: SubagentTask) -> SubagentResult:
        """Spawn a single subagent and wait for completion."""
        logger.info(f"Spawning subagent for task: {subtask.id}")
        
        agent = ClaudeAgent(subtask.agent_definition, self.settings, self.working_dir)
        task = Task(
            id=subtask.id,
            description=subtask.description,
            agent_name=subtask.agent_definition.name,
            context=subtask.context,
        )
        
        try:
            result = await agent.execute(task)
            subagent_result = SubagentResult(
                task_id=subtask.id,
                success=result.success,
                output=result.output,
                error=result.error,
                cost_usd=result.cost_usd,
                tokens_used=result.tokens_used,
            )
        except Exception as e:
            logger.error(f"Subagent {subtask.id} failed: {e}")
            subagent_result = SubagentResult(
                task_id=subtask.id,
                success=False,
                output="",
                error=str(e),
            )
        
        self.results[subtask.id] = subagent_result
        self.total_cost += subagent_result.cost_usd
        self.total_tokens += subagent_result.tokens_used
        
        return subagent_result
    
    async def spawn_parallel(self, subtasks: list[SubagentTask], max_concurrent: int = 5) -> list[SubagentResult]:
        """Spawn multiple subagents in parallel with concurrency limit."""
        logger.info(f"Spawning {len(subtasks)} subagents in parallel (max {max_concurrent})")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_spawn(subtask: SubagentTask) -> SubagentResult:
            async with semaphore:
                return await self.spawn(subtask)
        
        tasks = [limited_spawn(subtask) for subtask in subtasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(SubagentResult(
                    task_id=subtasks[i].id,
                    success=False,
                    output="",
                    error=str(result),
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def spawn_sequential(self, subtasks: list[SubagentTask], stop_on_failure: bool = True) -> list[SubagentResult]:
        """Spawn subagents sequentially, optionally stopping on failure."""
        logger.info(f"Spawning {len(subtasks)} subagents sequentially")
        
        results = []
        for subtask in subtasks:
            result = await self.spawn(subtask)
            results.append(result)
            
            if stop_on_failure and not result.success:
                logger.warning(f"Stopping sequential execution due to failure in {subtask.id}")
                break
        
        return results
    
    async def spawn_with_dependencies(self, subtasks: list[SubagentTask], dependencies: dict[str, list[str]]) -> list[SubagentResult]:
        """Spawn subagents respecting dependencies between them."""
        logger.info(f"Spawning {len(subtasks)} subagents with dependencies")
        
        # Build a map of task_id to subtask
        task_map = {st.id: st for st in subtasks}
        completed: set[str] = set()
        results: list[SubagentResult] = []
        
        while len(completed) < len(subtasks):
            # Find tasks whose dependencies are all completed
            ready = []
            for subtask in subtasks:
                if subtask.id in completed:
                    continue
                deps = dependencies.get(subtask.id, [])
                if all(dep in completed for dep in deps):
                    ready.append(subtask)
            
            if not ready:
                # Deadlock or all done
                break
            
            # Execute ready tasks in parallel
            batch_results = await self.spawn_parallel(ready)
            results.extend(batch_results)
            
            for result in batch_results:
                completed.add(result.task_id)
        
        return results
    
    def get_cost_summary(self) -> dict[str, Any]:
        """Get cost summary for all subagent executions."""
        return {
            "total_cost_usd": self.total_cost,
            "total_tokens": self.total_tokens,
            "subagent_count": len(self.results),
            "success_count": sum(1 for r in self.results.values() if r.success),
            "failure_count": sum(1 for r in self.results.values() if not r.success),
        }


def create_subtask(
    description: str,
    agent_definition: AgentDefinition,
    context: dict[str, Any] | None = None,
    parent_task_id: str | None = None,
) -> SubagentTask:
    """Helper function to create a subtask."""
    return SubagentTask(
        id=str(uuid.uuid4()),
        description=description,
        agent_definition=agent_definition,
        context=context or {},
        parent_task_id=parent_task_id,
    )
