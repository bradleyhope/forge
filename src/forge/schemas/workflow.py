"""
Workflow Schema - Orchestration primitives for multi-agent coordination.

A Workflow defines a sequence of agent tasks with dependencies, conditions,
and data flow. This schema enables the solution_architect to coordinate
complex multi-agent operations.

Usage:
    workflow = WorkflowDefinition(
        id="WF-001",
        name="Full Stack Feature Development",
        description="End-to-end workflow for implementing a new feature",
        steps=[
            WorkflowStep(
                id="analyze",
                agent="backend_analyzer",
                task="Analyze existing codebase for integration points",
                inputs={"target": "$workflow.target_path"},
            ),
            WorkflowStep(
                id="design_db",
                agent="database_architect", 
                task="Design database schema for new feature",
                depends_on=["analyze"],
                inputs={"analysis": "$analyze.findings"},
            ),
            WorkflowStep(
                id="implement",
                agent="improver",
                task="Implement the feature based on design",
                depends_on=["design_db"],
                inputs={"schema": "$design_db.change_plan"},
            ),
            WorkflowStep(
                id="test",
                agent="tester",
                task="Create and run tests",
                depends_on=["implement"],
                inputs={"changes": "$implement.change_plan"},
            ),
        ],
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"          # Not yet started
    RUNNING = "running"          # Currently executing
    PAUSED = "paused"            # Paused, awaiting input
    COMPLETED = "completed"      # Successfully finished
    FAILED = "failed"            # Failed with error
    CANCELLED = "cancelled"      # Manually cancelled
    TIMEOUT = "timeout"          # Exceeded time limit


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    WAITING = "waiting"          # Waiting for dependencies
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepConditionType(Enum):
    """Types of conditions for step execution."""
    ALWAYS = "always"            # Always execute
    ON_SUCCESS = "on_success"    # Only if previous steps succeeded
    ON_FAILURE = "on_failure"    # Only if previous steps failed
    CONDITIONAL = "conditional"  # Based on expression


@dataclass
class StepCondition:
    """Condition for executing a workflow step."""
    type: StepConditionType
    expression: Optional[str] = None    # For CONDITIONAL type
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "expression": self.expression,
        }


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.
    
    Each step represents a task to be executed by a specific agent.
    Steps can have dependencies on other steps and pass data between them.
    """
    # Required fields
    id: str                             # Unique step identifier (used for references)
    agent: str                          # Agent to execute this step
    task: str                           # Task description for the agent
    
    # Dependencies
    depends_on: list[str] = field(default_factory=list)  # Step IDs this depends on
    
    # Data flow
    inputs: dict[str, Any] = field(default_factory=dict)   # Input parameters
    outputs: dict[str, Any] = field(default_factory=dict)  # Output data (populated after execution)
    
    # Execution control
    condition: Optional[StepCondition] = None
    timeout_seconds: int = 300          # Max execution time
    retry_count: int = 0                # Number of retries on failure
    retry_delay_seconds: int = 5        # Delay between retries
    
    # Parallel execution
    parallel_group: Optional[str] = None  # Steps in same group run in parallel
    
    # Status tracking
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    result: Optional[Any] = None        # Agent result
    findings: list[dict] = field(default_factory=list)     # Findings produced
    change_plan: Optional[dict] = None  # ChangePlan produced
    eval_result: Optional[dict] = None  # EvalResult produced
    
    # Error handling
    error_message: Optional[str] = None
    retry_attempts: int = 0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "task": self.task,
            "depends_on": self.depends_on,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "condition": self.condition.to_dict() if self.condition else None,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "retry_delay_seconds": self.retry_delay_seconds,
            "parallel_group": self.parallel_group,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "result": self.result,
            "findings": self.findings,
            "change_plan": self.change_plan,
            "eval_result": self.eval_result,
            "error_message": self.error_message,
            "retry_attempts": self.retry_attempts,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowStep":
        condition_data = data.get("condition")
        condition = None
        if condition_data:
            condition = StepCondition(
                type=StepConditionType(condition_data["type"]),
                expression=condition_data.get("expression"),
            )
        
        return cls(
            id=data["id"],
            agent=data["agent"],
            task=data["task"],
            depends_on=data.get("depends_on", []),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            condition=condition,
            timeout_seconds=data.get("timeout_seconds", 300),
            retry_count=data.get("retry_count", 0),
            retry_delay_seconds=data.get("retry_delay_seconds", 5),
            parallel_group=data.get("parallel_group"),
            status=StepStatus(data.get("status", "pending")),
            result=data.get("result"),
            findings=data.get("findings", []),
            change_plan=data.get("change_plan"),
            eval_result=data.get("eval_result"),
            error_message=data.get("error_message"),
            retry_attempts=data.get("retry_attempts", 0),
        )


@dataclass
class WorkflowDefinition:
    """
    A complete workflow definition for multi-agent coordination.
    
    Workflows enable:
    - Sequential and parallel agent execution
    - Data flow between agents
    - Conditional execution
    - Error handling and retries
    - Progress tracking
    """
    # Required fields
    name: str                           # Workflow name
    steps: list[WorkflowStep]           # Ordered list of steps
    
    # Identification
    id: str = field(default_factory=lambda: f"WF-{str(uuid.uuid4())[:8].upper()}")
    
    # Metadata
    description: Optional[str] = None
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    
    # Global inputs/outputs
    inputs: dict[str, Any] = field(default_factory=dict)    # Workflow-level inputs
    outputs: dict[str, Any] = field(default_factory=dict)   # Workflow-level outputs
    
    # Execution settings
    timeout_seconds: int = 3600         # Total workflow timeout
    max_parallel_steps: int = 3         # Max concurrent steps
    stop_on_failure: bool = True        # Stop workflow on first failure
    
    # Status tracking
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_id: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Cost tracking
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    
    # Results aggregation
    all_findings: list[dict] = field(default_factory=list)
    all_change_plans: list[dict] = field(default_factory=list)
    all_eval_results: list[dict] = field(default_factory=list)
    
    # Error handling
    error_message: Optional[str] = None
    failed_step_id: Optional[str] = None
    
    @property
    def step_count(self) -> int:
        return len(self.steps)
    
    @property
    def completed_steps(self) -> int:
        return sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
    
    @property
    def progress_percent(self) -> float:
        if self.step_count == 0:
            return 0.0
        return (self.completed_steps / self.step_count) * 100
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_ready_steps(self) -> list[WorkflowStep]:
        """Get steps that are ready to execute (dependencies met)."""
        ready = []
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_met = all(
                self.get_step(dep_id).status == StepStatus.COMPLETED
                for dep_id in step.depends_on
                if self.get_step(dep_id) is not None
            )
            
            if deps_met:
                ready.append(step)
        
        return ready
    
    def resolve_input(self, value: Any) -> Any:
        """
        Resolve input references like $step_id.output_key.
        
        Supports:
        - $workflow.input_key - Reference workflow inputs
        - $step_id.findings - Reference step findings
        - $step_id.change_plan - Reference step change plan
        - $step_id.result - Reference step result
        """
        if not isinstance(value, str) or not value.startswith("$"):
            return value
        
        parts = value[1:].split(".")
        if len(parts) < 2:
            return value
        
        source = parts[0]
        key = parts[1]
        
        if source == "workflow":
            return self.inputs.get(key)
        
        step = self.get_step(source)
        if step is None:
            return value
        
        if key == "findings":
            return step.findings
        elif key == "change_plan":
            return step.change_plan
        elif key == "eval_result":
            return step.eval_result
        elif key == "result":
            return step.result
        else:
            return step.outputs.get(key)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "steps": [s.to_dict() for s in self.steps],
            "inputs": self.inputs,
            "outputs": self.outputs,
            "timeout_seconds": self.timeout_seconds,
            "max_parallel_steps": self.max_parallel_steps,
            "stop_on_failure": self.stop_on_failure,
            "status": self.status.value,
            "current_step_id": self.current_step_id,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
            "progress_percent": self.progress_percent,
            "all_findings": self.all_findings,
            "all_change_plans": self.all_change_plans,
            "all_eval_results": self.all_eval_results,
            "error_message": self.error_message,
            "failed_step_id": self.failed_step_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowDefinition":
        return cls(
            id=data.get("id", f"WF-{str(uuid.uuid4())[:8].upper()}"),
            name=data["name"],
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            steps=[WorkflowStep.from_dict(s) for s in data.get("steps", [])],
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            timeout_seconds=data.get("timeout_seconds", 3600),
            max_parallel_steps=data.get("max_parallel_steps", 3),
            stop_on_failure=data.get("stop_on_failure", True),
            status=WorkflowStatus(data.get("status", "pending")),
            current_step_id=data.get("current_step_id"),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            total_tokens=data.get("total_tokens", 0),
            all_findings=data.get("all_findings", []),
            all_change_plans=data.get("all_change_plans", []),
            all_eval_results=data.get("all_eval_results", []),
            error_message=data.get("error_message"),
            failed_step_id=data.get("failed_step_id"),
        )
    
    def __str__(self) -> str:
        return f"[{self.status.value.upper()}] {self.id}: {self.name} ({self.progress_percent:.0f}% complete)"
