"""
Forge Cross-Agent Communication Schemas

This module defines standardized schemas for communication between Forge agents.
These schemas enable:
- Consistent data exchange between agents
- Type-safe agent interactions
- Workflow orchestration
- Audit trails and debugging

Schema Categories:
1. Finding - Analysis results from any agent
2. ChangePlan - Proposed modifications to code/config
3. EvalResult - Evaluation and testing outcomes
4. WorkflowStep - Orchestration primitives
5. AgentMessage - Inter-agent communication
"""

from .finding import Finding, FindingSeverity, FindingCategory
from .change_plan import ChangePlan, Change, ChangeType
from .eval_result import EvalResult, EvalMetric, EvalStatus
from .workflow import WorkflowStep, WorkflowDefinition, WorkflowStatus
from .message import AgentMessage, MessageType

__all__ = [
    # Finding schemas
    "Finding",
    "FindingSeverity", 
    "FindingCategory",
    # Change plan schemas
    "ChangePlan",
    "Change",
    "ChangeType",
    # Evaluation schemas
    "EvalResult",
    "EvalMetric",
    "EvalStatus",
    # Workflow schemas
    "WorkflowStep",
    "WorkflowDefinition",
    "WorkflowStatus",
    # Message schemas
    "AgentMessage",
    "MessageType",
]
