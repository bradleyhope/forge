"""
ChangePlan Schema - Standardized format for proposed code/config modifications.

A ChangePlan represents a set of coordinated changes to be applied to the codebase.
This schema is used by action agents:
- debugger (bug fixes)
- improver (refactoring)
- tester (adding tests)
- documenter (documentation updates)

Usage:
    plan = ChangePlan(
        id="CP-001",
        agent="improver",
        title="Refactor authentication module",
        description="Extract authentication logic into dedicated service",
        changes=[
            Change(
                type=ChangeType.MODIFY,
                file="api/auth.py",
                description="Extract AuthService class",
                before="def authenticate(user, password):\\n    ...",
                after="class AuthService:\\n    def authenticate(self, user, password):\\n    ...",
            ),
            Change(
                type=ChangeType.CREATE,
                file="services/auth_service.py",
                description="New authentication service module",
                after="from api.auth import AuthService\\n...",
            ),
        ],
        tests_to_run=["tests/test_auth.py"],
        rollback_steps=["git checkout api/auth.py"],
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ChangeType(Enum):
    """Types of changes that can be made to files."""
    CREATE = "create"      # New file
    MODIFY = "modify"      # Edit existing file
    DELETE = "delete"      # Remove file
    RENAME = "rename"      # Rename/move file
    CHMOD = "chmod"        # Change permissions


class ChangeStatus(Enum):
    """Status of a change plan."""
    DRAFT = "draft"              # Being prepared
    PENDING_REVIEW = "pending_review"  # Awaiting approval
    APPROVED = "approved"        # Ready to apply
    IN_PROGRESS = "in_progress"  # Being applied
    APPLIED = "applied"          # Successfully applied
    FAILED = "failed"            # Application failed
    ROLLED_BACK = "rolled_back"  # Changes were reverted


@dataclass
class Change:
    """
    A single file change within a ChangePlan.
    
    Represents one atomic modification to a file. Multiple Changes
    are grouped into a ChangePlan for coordinated application.
    """
    type: ChangeType
    file: str                           # Path to the file
    description: str                    # What this change does
    
    # Content (for CREATE and MODIFY)
    before: Optional[str] = None        # Original content (for MODIFY)
    after: Optional[str] = None         # New content (for CREATE and MODIFY)
    
    # For partial modifications (line-based edits)
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    
    # For RENAME operations
    new_file: Optional[str] = None
    
    # For CHMOD operations
    permissions: Optional[str] = None
    
    # Metadata
    reason: Optional[str] = None        # Why this change is needed
    finding_id: Optional[str] = None    # Related Finding ID if applicable
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "file": self.file,
            "description": self.description,
            "before": self.before,
            "after": self.after,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "new_file": self.new_file,
            "permissions": self.permissions,
            "reason": self.reason,
            "finding_id": self.finding_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Change":
        return cls(
            type=ChangeType(data["type"]),
            file=data["file"],
            description=data["description"],
            before=data.get("before"),
            after=data.get("after"),
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
            new_file=data.get("new_file"),
            permissions=data.get("permissions"),
            reason=data.get("reason"),
            finding_id=data.get("finding_id"),
        )


@dataclass
class ChangePlan:
    """
    A coordinated set of changes to be applied to the codebase.
    
    ChangePlans enable:
    - Atomic application of related changes
    - Review and approval workflows
    - Rollback capabilities
    - Audit trails
    - Integration with testing
    """
    # Required fields
    agent: str                          # Agent proposing the changes
    title: str                          # Short description
    description: str                    # Detailed explanation
    changes: list[Change]               # List of changes to apply
    
    # Identification
    id: str = field(default_factory=lambda: f"CP-{str(uuid.uuid4())[:8].upper()}")
    
    # Related findings
    finding_ids: list[str] = field(default_factory=list)  # Findings this plan addresses
    
    # Testing
    tests_to_run: list[str] = field(default_factory=list)      # Test files/patterns
    tests_to_create: list[str] = field(default_factory=list)   # New tests needed
    
    # Rollback
    rollback_steps: list[str] = field(default_factory=list)    # How to undo
    backup_created: bool = False
    backup_location: Optional[str] = None
    
    # Dependencies
    depends_on: list[str] = field(default_factory=list)        # Other ChangePlan IDs
    blocks: list[str] = field(default_factory=list)            # Plans blocked by this
    
    # Risk assessment
    risk_level: str = "low"             # low, medium, high, critical
    breaking_change: bool = False
    requires_migration: bool = False
    
    # Status
    status: ChangeStatus = ChangeStatus.DRAFT
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    applied_at: Optional[datetime] = None
    
    # Approval
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    
    # Execution results
    execution_log: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    @property
    def file_count(self) -> int:
        """Number of files affected."""
        return len(set(c.file for c in self.changes))
    
    @property
    def is_safe_to_apply(self) -> bool:
        """Check if plan can be safely applied."""
        return (
            self.status == ChangeStatus.APPROVED and
            len(self.changes) > 0 and
            all(c.type != ChangeType.DELETE or c.before is not None for c in self.changes)
        )
    
    def add_change(self, change: Change) -> None:
        """Add a change to the plan."""
        self.changes.append(change)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "title": self.title,
            "description": self.description,
            "changes": [c.to_dict() for c in self.changes],
            "finding_ids": self.finding_ids,
            "tests_to_run": self.tests_to_run,
            "tests_to_create": self.tests_to_create,
            "rollback_steps": self.rollback_steps,
            "backup_created": self.backup_created,
            "backup_location": self.backup_location,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "risk_level": self.risk_level,
            "breaking_change": self.breaking_change,
            "requires_migration": self.requires_migration,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "approved_by": self.approved_by,
            "approval_notes": self.approval_notes,
            "execution_log": self.execution_log,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ChangePlan":
        plan = cls(
            id=data.get("id", f"CP-{str(uuid.uuid4())[:8].upper()}"),
            agent=data["agent"],
            title=data["title"],
            description=data["description"],
            changes=[Change.from_dict(c) for c in data.get("changes", [])],
            finding_ids=data.get("finding_ids", []),
            tests_to_run=data.get("tests_to_run", []),
            tests_to_create=data.get("tests_to_create", []),
            rollback_steps=data.get("rollback_steps", []),
            backup_created=data.get("backup_created", False),
            backup_location=data.get("backup_location"),
            depends_on=data.get("depends_on", []),
            blocks=data.get("blocks", []),
            risk_level=data.get("risk_level", "low"),
            breaking_change=data.get("breaking_change", False),
            requires_migration=data.get("requires_migration", False),
            status=ChangeStatus(data.get("status", "draft")),
            approved_by=data.get("approved_by"),
            approval_notes=data.get("approval_notes"),
            execution_log=data.get("execution_log", []),
            error_message=data.get("error_message"),
        )
        return plan
    
    def __str__(self) -> str:
        return f"[{self.status.value.upper()}] {self.id}: {self.title} ({self.file_count} files)"
