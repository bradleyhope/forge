"""
AgentMessage Schema - Inter-agent communication protocol.

AgentMessages enable direct communication between agents for:
- Requesting assistance from other agents
- Sharing context and insights
- Coordinating on complex tasks
- Escalating issues

Usage:
    message = AgentMessage(
        from_agent="backend_analyzer",
        to_agent="security_analyzer",
        type=MessageType.REQUEST,
        subject="Security review needed for authentication changes",
        body="Found potential security implications in auth module refactoring",
        payload={
            "findings": [...],
            "files_affected": ["api/auth.py", "api/users.py"],
        },
        priority="high",
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class MessageType(Enum):
    """Types of inter-agent messages."""
    # Requests
    REQUEST = "request"              # Request for action/analysis
    QUERY = "query"                  # Request for information
    DELEGATE = "delegate"            # Delegate a task
    
    # Responses
    RESPONSE = "response"            # Response to a request
    RESULT = "result"                # Task completion result
    ERROR = "error"                  # Error response
    
    # Notifications
    NOTIFICATION = "notification"    # Informational update
    ALERT = "alert"                  # Urgent notification
    PROGRESS = "progress"            # Progress update
    
    # Coordination
    HANDOFF = "handoff"              # Transfer responsibility
    SYNC = "sync"                    # Synchronization message
    ACK = "ack"                      # Acknowledgment


class MessagePriority(Enum):
    """Priority levels for messages."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(Enum):
    """Status of a message."""
    PENDING = "pending"              # Not yet delivered
    DELIVERED = "delivered"          # Delivered to recipient
    READ = "read"                    # Read by recipient
    PROCESSING = "processing"        # Being processed
    COMPLETED = "completed"          # Action completed
    FAILED = "failed"                # Processing failed


@dataclass
class AgentMessage:
    """
    A message between Forge agents.
    
    AgentMessages provide a standardized way for agents to:
    - Request help from other agents
    - Share findings and insights
    - Coordinate on multi-step tasks
    - Report progress and results
    """
    # Required fields
    from_agent: str                     # Sending agent
    to_agent: str                       # Receiving agent (or "broadcast" for all)
    type: MessageType                   # Message type
    subject: str                        # Brief description
    
    # Identification
    id: str = field(default_factory=lambda: f"MSG-{str(uuid.uuid4())[:8].upper()}")
    
    # Content
    body: str = ""                      # Detailed message content
    payload: dict[str, Any] = field(default_factory=dict)  # Structured data
    
    # References
    in_reply_to: Optional[str] = None   # ID of message being replied to
    thread_id: Optional[str] = None     # Conversation thread ID
    workflow_id: Optional[str] = None   # Related workflow
    step_id: Optional[str] = None       # Related workflow step
    
    # Related entities
    finding_ids: list[str] = field(default_factory=list)
    change_plan_ids: list[str] = field(default_factory=list)
    eval_result_ids: list[str] = field(default_factory=list)
    
    # Priority and timing
    priority: MessagePriority = MessagePriority.NORMAL
    expires_at: Optional[datetime] = None  # Message expiration
    
    # Status tracking
    status: MessageStatus = MessageStatus.PENDING
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Response handling
    expects_response: bool = False
    response_timeout_seconds: int = 300
    
    # Metadata
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def create_reply(
        self,
        from_agent: str,
        type: MessageType,
        subject: str,
        body: str = "",
        payload: dict = None,
    ) -> "AgentMessage":
        """Create a reply to this message."""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=self.from_agent,
            type=type,
            subject=subject,
            body=body,
            payload=payload or {},
            in_reply_to=self.id,
            thread_id=self.thread_id or self.id,
            workflow_id=self.workflow_id,
            step_id=self.step_id,
        )
    
    def create_forward(
        self,
        from_agent: str,
        to_agent: str,
        additional_context: str = "",
    ) -> "AgentMessage":
        """Forward this message to another agent."""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            type=MessageType.DELEGATE,
            subject=f"FWD: {self.subject}",
            body=f"{additional_context}\n\n--- Forwarded message ---\n{self.body}",
            payload=self.payload.copy(),
            thread_id=self.thread_id or self.id,
            workflow_id=self.workflow_id,
            finding_ids=self.finding_ids.copy(),
            change_plan_ids=self.change_plan_ids.copy(),
            eval_result_ids=self.eval_result_ids.copy(),
        )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "type": self.type.value,
            "subject": self.subject,
            "body": self.body,
            "payload": self.payload,
            "in_reply_to": self.in_reply_to,
            "thread_id": self.thread_id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "finding_ids": self.finding_ids,
            "change_plan_ids": self.change_plan_ids,
            "eval_result_ids": self.eval_result_ids,
            "priority": self.priority.value,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expects_response": self.expects_response,
            "response_timeout_seconds": self.response_timeout_seconds,
            "tags": self.tags,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "AgentMessage":
        return cls(
            id=data.get("id", f"MSG-{str(uuid.uuid4())[:8].upper()}"),
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            type=MessageType(data["type"]),
            subject=data["subject"],
            body=data.get("body", ""),
            payload=data.get("payload", {}),
            in_reply_to=data.get("in_reply_to"),
            thread_id=data.get("thread_id"),
            workflow_id=data.get("workflow_id"),
            step_id=data.get("step_id"),
            finding_ids=data.get("finding_ids", []),
            change_plan_ids=data.get("change_plan_ids", []),
            eval_result_ids=data.get("eval_result_ids", []),
            priority=MessagePriority(data.get("priority", "normal")),
            status=MessageStatus(data.get("status", "pending")),
            expects_response=data.get("expects_response", False),
            response_timeout_seconds=data.get("response_timeout_seconds", 300),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        return f"[{self.type.value.upper()}] {self.from_agent} → {self.to_agent}: {self.subject}"
