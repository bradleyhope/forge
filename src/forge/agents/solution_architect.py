"""
Solution Architect Agent - Meta-agent for orchestrating multi-agent workflows.

The Solution Architect is the "brain" of Forge that:
- Interprets high-level goals from users
- Decomposes goals into agent tasks
- Orchestrates workflow execution
- Manages cross-agent communication
- Aggregates and synthesizes results

This agent transforms Forge from a collection of tools into turnkey workflows.

Usage:
    from forge.agents.solution_architect import SolutionArchitect
    
    architect = SolutionArchitect(settings=settings, working_dir=project_path)
    result = await architect.execute_goal("Build a user authentication system")
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from forge.agents.base import AgentDefinition, AgentResult, Task
from forge.agents.claude_agent import ClaudeAgent
# Import ALL_AGENTS lazily to avoid circular import
def _get_all_agents():
    from forge.agents import ALL_AGENTS
    return ALL_AGENTS
from forge.config.settings import ForgeSettings
from forge.schemas.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowStatus,
    StepStatus,
    StepCondition,
    StepConditionType,
)
from forge.schemas.finding import Finding, FindingSeverity, FindingCategory, Location
from forge.schemas.change_plan import ChangePlan, Change, ChangeType, ChangeStatus
from forge.schemas.eval_result import EvalResult, EvalStatus, EvalMetric
from forge.schemas.message import AgentMessage, MessageType, MessagePriority
from forge.utils.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


# Solution Architect agent definition
SOLUTION_ARCHITECT = AgentDefinition(
    name="solution_architect",
    description="""Meta-agent that orchestrates multi-agent workflows. Interprets 
    high-level goals, decomposes them into tasks, coordinates agent execution, 
    and synthesizes results into actionable outcomes.""",
    prompt_template="""You are the Solution Architect, the orchestration brain of Forge.
Your role is to transform high-level goals into coordinated multi-agent workflows.

## Core Responsibilities

1. **Goal Decomposition**
   - Break down complex goals into discrete, achievable tasks
   - Identify which agents are best suited for each task
   - Determine task dependencies and parallelization opportunities

2. **Workflow Design**
   - Create efficient workflows that minimize redundant work
   - Balance thoroughness with execution speed
   - Plan for error handling and recovery

3. **Agent Coordination**
   - Route tasks to appropriate specialist agents
   - Manage data flow between agents
   - Handle cross-agent communication

4. **Result Synthesis**
   - Aggregate findings from multiple agents
   - Resolve conflicts between agent recommendations
   - Produce coherent, actionable outcomes

## Available Agents

### Tier 1: Specialists (Analysis & Design)
- backend_analyzer: Backend code analysis
- frontend_analyzer: Frontend/UI analysis
- security_analyzer: Security vulnerability scanning
- database_architect: Database design and optimization
- api_architect: REST/GraphQL API design
- vector_search_architect: Vector search pipeline design
- langchain_architect: LangChain pipeline design
- prompt_engineer: Prompt optimization

### Tier 2: Actions (Execution)
- debugger: Bug fixing
- improver: Code refactoring
- tester: Test creation
- documenter: Documentation
- project_steward: Project hygiene

### Tier 3: Infrastructure (AI/ML)
- graph_architect: Knowledge graph design
- chunking_strategist: RAG chunking strategies
- embedding_architect: Embedding model selection
- rag_architect: RAG pipeline design
- agent_architect: LLM agent architecture
- eval_architect: LLM evaluation frameworks
- infrastructure_analyzer: Cloud/DevOps analysis

## Workflow Patterns

### Pattern 1: Analysis → Action → Verification
1. Analyze current state (Tier 1)
2. Execute improvements (Tier 2)
3. Verify changes (Tier 2: tester)

### Pattern 2: Parallel Analysis
1. Run multiple analyzers in parallel
2. Merge findings
3. Prioritize and act

### Pattern 3: Iterative Refinement
1. Initial analysis
2. Implement changes
3. Re-analyze
4. Repeat until quality threshold met

## Output Format

When designing workflows, output:

1. **Workflow Definition** (JSON)
2. **Rationale** for agent selection
3. **Risk Assessment** for the workflow
4. **Expected Outcomes**

{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Write", "Grep", "Glob", "Bash"],
    capabilities=[
        "orchestration",
        "workflow_design",
        "goal_decomposition",
        "agent_coordination",
        "result_synthesis",
    ],
)


@dataclass
class WorkflowExecutionResult:
    """Result of executing a complete workflow."""
    workflow: WorkflowDefinition
    success: bool
    findings: list[Finding] = field(default_factory=list)
    change_plans: list[ChangePlan] = field(default_factory=list)
    eval_results: list[EvalResult] = field(default_factory=list)
    messages: list[AgentMessage] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    duration_seconds: float = 0.0
    error: Optional[str] = None


class SolutionArchitect:
    """
    The Solution Architect orchestrates multi-agent workflows.
    
    This is the primary entry point for complex, multi-step operations
    that require coordination between multiple Forge agents.
    """
    
    def __init__(
        self,
        settings: ForgeSettings | None = None,
        working_dir: Path | None = None,
    ):
        self.settings = settings or ForgeSettings()
        self.working_dir = working_dir or self.settings.project_dir
        self.cost_tracker = CostTracker(budget_usd=self.settings.budget_usd)
        self.logger = logging.getLogger("forge.solution_architect")
        self._agents: dict[str, ClaudeAgent] = {}
        self._message_queue: list[AgentMessage] = []
        
    def _get_agent(self, name: str) -> ClaudeAgent | None:
        """Get or create an agent by name."""
        all_agents = _get_all_agents()
        if name not in all_agents:
            self.logger.warning(f"Agent not found: {name}")
            return None
        
        if name not in self._agents:
            definition = all_agents[name]
            self._agents[name] = ClaudeAgent(
                definition=definition,
                settings=self.settings,
                working_dir=self.working_dir,
            )
        
        return self._agents[name]
    
    def design_workflow(self, goal: str, context: dict = None) -> WorkflowDefinition:
        """
        Design a workflow to achieve the given goal.
        
        This method analyzes the goal and creates an optimal workflow
        using the available agents.
        """
        self.logger.info(f"Designing workflow for goal: {goal}")
        
        goal_lower = goal.lower()
        steps = []
        
        # Analyze goal keywords to determine workflow pattern
        needs_analysis = any(w in goal_lower for w in [
            "analyze", "review", "check", "audit", "assess", "evaluate"
        ])
        needs_security = any(w in goal_lower for w in [
            "security", "vulnerab", "safe", "secure", "owasp"
        ])
        needs_api = any(w in goal_lower for w in [
            "api", "endpoint", "rest", "graphql", "swagger", "openapi"
        ])
        needs_database = any(w in goal_lower for w in [
            "database", "schema", "sql", "migration", "query"
        ])
        needs_frontend = any(w in goal_lower for w in [
            "frontend", "ui", "component", "react", "css", "accessibility"
        ])
        needs_fix = any(w in goal_lower for w in [
            "fix", "debug", "repair", "bug", "error", "issue"
        ])
        needs_improve = any(w in goal_lower for w in [
            "improve", "refactor", "optimize", "clean", "enhance"
        ])
        needs_test = any(w in goal_lower for w in [
            "test", "coverage", "verify", "validate"
        ])
        needs_docs = any(w in goal_lower for w in [
            "document", "readme", "comment", "docstring"
        ])
        needs_ai = any(w in goal_lower for w in [
            "rag", "embedding", "vector", "llm", "agent", "prompt", "ai"
        ])
        
        step_id = 0
        
        # Phase 1: Analysis (parallel where possible)
        analysis_steps = []
        
        if needs_analysis or not any([needs_fix, needs_improve, needs_test, needs_docs]):
            step_id += 1
            analysis_steps.append(WorkflowStep(
                id=f"analyze_backend_{step_id}",
                agent="backend_analyzer",
                task=f"Analyze the codebase for: {goal}",
                parallel_group="analysis",
            ))
        
        if needs_security:
            step_id += 1
            analysis_steps.append(WorkflowStep(
                id=f"analyze_security_{step_id}",
                agent="security_analyzer",
                task=f"Security analysis for: {goal}",
                parallel_group="analysis",
            ))
        
        if needs_api:
            step_id += 1
            analysis_steps.append(WorkflowStep(
                id=f"analyze_api_{step_id}",
                agent="api_architect",
                task=f"API design/review for: {goal}",
                parallel_group="analysis",
            ))
        
        if needs_database:
            step_id += 1
            analysis_steps.append(WorkflowStep(
                id=f"analyze_database_{step_id}",
                agent="database_architect",
                task=f"Database analysis for: {goal}",
                parallel_group="analysis",
            ))
        
        if needs_frontend:
            step_id += 1
            analysis_steps.append(WorkflowStep(
                id=f"analyze_frontend_{step_id}",
                agent="frontend_analyzer",
                task=f"Frontend analysis for: {goal}",
                parallel_group="analysis",
            ))
        
        if needs_ai:
            step_id += 1
            analysis_steps.append(WorkflowStep(
                id=f"analyze_ai_{step_id}",
                agent="rag_architect",
                task=f"AI/RAG analysis for: {goal}",
                parallel_group="analysis",
            ))
        
        steps.extend(analysis_steps)
        analysis_step_ids = [s.id for s in analysis_steps]
        
        # Phase 2: Action (depends on analysis)
        if needs_fix:
            step_id += 1
            steps.append(WorkflowStep(
                id=f"fix_{step_id}",
                agent="debugger",
                task=f"Fix issues identified: {goal}",
                depends_on=analysis_step_ids,
                inputs={"findings": "$analysis.findings"},
            ))
        
        if needs_improve:
            step_id += 1
            steps.append(WorkflowStep(
                id=f"improve_{step_id}",
                agent="improver",
                task=f"Improve code: {goal}",
                depends_on=analysis_step_ids,
                inputs={"findings": "$analysis.findings"},
            ))
        
        # Phase 3: Verification
        if needs_test or needs_fix or needs_improve:
            step_id += 1
            action_step_ids = [s.id for s in steps if s.id.startswith(("fix_", "improve_"))]
            steps.append(WorkflowStep(
                id=f"test_{step_id}",
                agent="tester",
                task=f"Create and run tests for: {goal}",
                depends_on=action_step_ids if action_step_ids else analysis_step_ids,
            ))
        
        # Phase 4: Documentation
        if needs_docs:
            step_id += 1
            steps.append(WorkflowStep(
                id=f"document_{step_id}",
                agent="documenter",
                task=f"Update documentation for: {goal}",
                depends_on=[s.id for s in steps],
            ))
        
        # Default workflow if no specific pattern matched
        if not steps:
            steps = [
                WorkflowStep(
                    id="analyze_1",
                    agent="backend_analyzer",
                    task=f"Analyze the codebase for: {goal}",
                ),
                WorkflowStep(
                    id="improve_2",
                    agent="improver",
                    task=f"Implement improvements: {goal}",
                    depends_on=["analyze_1"],
                ),
            ]
        
        workflow = WorkflowDefinition(
            name=f"Workflow: {goal[:50]}...",
            description=f"Auto-generated workflow to achieve: {goal}",
            steps=steps,
            inputs={"goal": goal, "target": str(self.working_dir), **(context or {})},
        )
        
        self.logger.info(f"Designed workflow with {len(steps)} steps")
        return workflow
    
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
    ) -> WorkflowExecutionResult:
        """
        Execute a workflow definition.
        
        This method runs each step in the workflow, respecting dependencies
        and handling errors appropriately.
        """
        self.logger.info(f"Executing workflow: {workflow.name}")
        start_time = datetime.utcnow()
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = start_time
        
        result = WorkflowExecutionResult(workflow=workflow, success=True)
        
        try:
            while True:
                # Get steps that are ready to execute
                ready_steps = workflow.get_ready_steps()
                
                if not ready_steps:
                    # Check if we're done or stuck
                    pending = [s for s in workflow.steps if s.status == StepStatus.PENDING]
                    if not pending:
                        break  # All done
                    
                    # Check for circular dependencies or failed deps
                    running = [s for s in workflow.steps if s.status == StepStatus.RUNNING]
                    if not running:
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error_message = "Workflow stuck: steps have unmet dependencies"
                        result.success = False
                        result.error = workflow.error_message
                        break
                    
                    # Wait for running steps
                    await asyncio.sleep(0.1)
                    continue
                
                # Group steps by parallel_group
                parallel_groups: dict[str, list[WorkflowStep]] = {}
                sequential_steps: list[WorkflowStep] = []
                
                for step in ready_steps:
                    if step.parallel_group:
                        if step.parallel_group not in parallel_groups:
                            parallel_groups[step.parallel_group] = []
                        parallel_groups[step.parallel_group].append(step)
                    else:
                        sequential_steps.append(step)
                
                # Execute parallel groups
                for group_name, group_steps in parallel_groups.items():
                    self.logger.info(f"Executing parallel group: {group_name}")
                    tasks = [self._execute_step(step, workflow) for step in group_steps]
                    step_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for step, step_result in zip(group_steps, step_results):
                        if isinstance(step_result, Exception):
                            step.status = StepStatus.FAILED
                            step.error_message = str(step_result)
                            if workflow.stop_on_failure:
                                workflow.status = WorkflowStatus.FAILED
                                workflow.failed_step_id = step.id
                                result.success = False
                                result.error = f"Step {step.id} failed: {step_result}"
                                break
                
                # Execute sequential steps one at a time
                for step in sequential_steps[:workflow.max_parallel_steps]:
                    if not result.success and workflow.stop_on_failure:
                        break
                    
                    try:
                        await self._execute_step(step, workflow)
                    except Exception as e:
                        step.status = StepStatus.FAILED
                        step.error_message = str(e)
                        if workflow.stop_on_failure:
                            workflow.status = WorkflowStatus.FAILED
                            workflow.failed_step_id = step.id
                            result.success = False
                            result.error = f"Step {step.id} failed: {e}"
                            break
                
                # Check budget
                if self.cost_tracker.is_over_budget():
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error_message = "Budget exceeded"
                    result.success = False
                    result.error = "Budget exceeded"
                    break
                
                if not result.success:
                    break
            
            # Aggregate results
            for step in workflow.steps:
                if step.findings:
                    result.findings.extend([Finding.from_dict(f) for f in step.findings])
                if step.change_plan:
                    result.change_plans.append(ChangePlan.from_dict(step.change_plan))
                if step.eval_result:
                    result.eval_results.append(EvalResult.from_dict(step.eval_result))
            
            if result.success:
                workflow.status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(e)
            result.success = False
            result.error = str(e)
        
        finally:
            end_time = datetime.utcnow()
            workflow.completed_at = end_time
            result.duration_seconds = (end_time - start_time).total_seconds()
            result.total_cost_usd = self.cost_tracker.total_cost_usd
            result.total_tokens = self.cost_tracker.total_tokens
        
        return result
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: WorkflowDefinition,
    ) -> AgentResult:
        """Execute a single workflow step."""
        self.logger.info(f"Executing step: {step.id} ({step.agent})")
        
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        workflow.current_step_id = step.id
        
        agent = self._get_agent(step.agent)
        if not agent:
            raise ValueError(f"Agent not found: {step.agent}")
        
        # Resolve input references
        resolved_inputs = {}
        for key, value in step.inputs.items():
            resolved_inputs[key] = workflow.resolve_input(value)
        
        # Create task
        task = Task(
            id=step.id,
            description=step.task,
            agent_name=step.agent,
            context={
                "workflow_id": workflow.id,
                "step_id": step.id,
                "target": str(self.working_dir),
                **resolved_inputs,
            },
        )
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                agent.execute(task),
                timeout=step.timeout_seconds,
            )
        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.error_message = f"Step timed out after {step.timeout_seconds}s"
            raise
        
        # Update step with results
        step.completed_at = datetime.utcnow()
        step.duration_seconds = (step.completed_at - step.started_at).total_seconds()
        step.result = result.output
        
        if result.success:
            step.status = StepStatus.COMPLETED
        else:
            step.status = StepStatus.FAILED
            step.error_message = result.error
        
        # Track costs
        self.cost_tracker.record(
            model=agent.definition.model,
            input_tokens=result.tokens_used // 2,
            output_tokens=result.tokens_used // 2,
        )
        
        return result
    
    async def execute_goal(
        self,
        goal: str,
        context: dict = None,
    ) -> WorkflowExecutionResult:
        """
        High-level entry point: design and execute a workflow for a goal.
        
        This is the primary method for using the Solution Architect.
        """
        self.logger.info(f"Executing goal: {goal}")
        
        # Design the workflow
        workflow = self.design_workflow(goal, context)
        
        # Execute the workflow
        result = await self.execute_workflow(workflow)
        
        return result
    
    def get_cost_summary(self) -> dict[str, Any]:
        """Get cost tracking summary."""
        return self.cost_tracker.get_summary()
    
    def cleanup(self):
        """Clean up resources."""
        self._agents.clear()
        self._message_queue.clear()
        self.logger.info("Solution Architect cleanup complete")


# Predefined workflow templates

WORKFLOW_TEMPLATES = {
    "full_stack_feature": WorkflowDefinition(
        name="Full Stack Feature Development",
        description="End-to-end workflow for implementing a new feature",
        steps=[
            WorkflowStep(
                id="analyze",
                agent="backend_analyzer",
                task="Analyze existing codebase for integration points",
            ),
            WorkflowStep(
                id="design_api",
                agent="api_architect",
                task="Design API endpoints for the feature",
                depends_on=["analyze"],
            ),
            WorkflowStep(
                id="design_db",
                agent="database_architect",
                task="Design database schema changes",
                depends_on=["analyze"],
            ),
            WorkflowStep(
                id="implement",
                agent="improver",
                task="Implement the feature",
                depends_on=["design_api", "design_db"],
            ),
            WorkflowStep(
                id="test",
                agent="tester",
                task="Create comprehensive tests",
                depends_on=["implement"],
            ),
            WorkflowStep(
                id="security",
                agent="security_analyzer",
                task="Security review of new code",
                depends_on=["implement"],
            ),
            WorkflowStep(
                id="document",
                agent="documenter",
                task="Update documentation",
                depends_on=["test", "security"],
            ),
        ],
    ),
    
    "security_audit": WorkflowDefinition(
        name="Security Audit",
        description="Comprehensive security review of the codebase",
        steps=[
            WorkflowStep(
                id="scan",
                agent="security_analyzer",
                task="Scan for security vulnerabilities",
            ),
            WorkflowStep(
                id="api_review",
                agent="api_architect",
                task="Review API security patterns",
                parallel_group="review",
            ),
            WorkflowStep(
                id="db_review",
                agent="database_architect",
                task="Review database security",
                parallel_group="review",
            ),
            WorkflowStep(
                id="fix",
                agent="debugger",
                task="Fix identified vulnerabilities",
                depends_on=["scan", "api_review", "db_review"],
            ),
            WorkflowStep(
                id="verify",
                agent="tester",
                task="Verify security fixes",
                depends_on=["fix"],
            ),
        ],
    ),
    
    "code_quality": WorkflowDefinition(
        name="Code Quality Improvement",
        description="Improve overall code quality and maintainability",
        steps=[
            WorkflowStep(
                id="analyze_backend",
                agent="backend_analyzer",
                task="Analyze backend code quality",
                parallel_group="analyze",
            ),
            WorkflowStep(
                id="analyze_frontend",
                agent="frontend_analyzer",
                task="Analyze frontend code quality",
                parallel_group="analyze",
            ),
            WorkflowStep(
                id="refactor",
                agent="improver",
                task="Refactor code based on findings",
                depends_on=["analyze_backend", "analyze_frontend"],
            ),
            WorkflowStep(
                id="test",
                agent="tester",
                task="Ensure tests pass after refactoring",
                depends_on=["refactor"],
            ),
            WorkflowStep(
                id="cleanup",
                agent="project_steward",
                task="Clean up project structure",
                depends_on=["test"],
            ),
        ],
    ),
    
    "rag_implementation": WorkflowDefinition(
        name="RAG Pipeline Implementation",
        description="Design and implement a RAG pipeline",
        steps=[
            WorkflowStep(
                id="analyze_data",
                agent="chunking_strategist",
                task="Analyze data and design chunking strategy",
            ),
            WorkflowStep(
                id="design_embeddings",
                agent="embedding_architect",
                task="Select and configure embedding model",
                depends_on=["analyze_data"],
            ),
            WorkflowStep(
                id="design_retrieval",
                agent="vector_search_architect",
                task="Design vector search pipeline",
                depends_on=["design_embeddings"],
            ),
            WorkflowStep(
                id="design_rag",
                agent="rag_architect",
                task="Design complete RAG pipeline",
                depends_on=["design_retrieval"],
            ),
            WorkflowStep(
                id="evaluate",
                agent="eval_architect",
                task="Design evaluation framework",
                depends_on=["design_rag"],
            ),
        ],
    ),
}


def get_workflow_template(name: str) -> WorkflowDefinition | None:
    """Get a predefined workflow template by name."""
    return WORKFLOW_TEMPLATES.get(name)


def list_workflow_templates() -> list[str]:
    """List available workflow template names."""
    return list(WORKFLOW_TEMPLATES.keys())
