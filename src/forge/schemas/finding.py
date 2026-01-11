"""
Finding Schema - Standardized format for analysis results across all agents.

A Finding represents any issue, observation, or recommendation discovered
during code analysis. This schema is used by:
- backend_analyzer
- frontend_analyzer  
- security_analyzer
- database_architect
- All other analysis agents

Usage:
    finding = Finding(
        id="SEC-001",
        agent="security_analyzer",
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.HIGH,
        title="SQL Injection Vulnerability",
        description="User input is directly interpolated into SQL query",
        location=Location(file="api/users.py", line_start=45, line_end=47),
        evidence="query = f\"SELECT * FROM users WHERE id = {user_id}\"",
        recommendation="Use parameterized queries with SQLAlchemy",
        references=["https://owasp.org/www-community/attacks/SQL_Injection"],
        confidence=0.95,
        effort_to_fix="low",
        tags=["owasp-top-10", "injection", "database"]
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class FindingSeverity(Enum):
    """Severity levels for findings, aligned with industry standards."""
    CRITICAL = "critical"  # Immediate action required, security breach or data loss risk
    HIGH = "high"          # Should be fixed before deployment
    MEDIUM = "medium"      # Should be addressed in current sprint
    LOW = "low"            # Technical debt, can be scheduled
    INFO = "info"          # Observation, no action required


class FindingCategory(Enum):
    """Categories of findings across all agent domains."""
    # Security (security_analyzer)
    SECURITY = "security"
    VULNERABILITY = "vulnerability"
    
    # Performance (backend_analyzer, frontend_analyzer)
    PERFORMANCE = "performance"
    MEMORY = "memory"
    
    # Code Quality (all analyzers)
    BUG = "bug"
    CODE_SMELL = "code_smell"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    
    # Architecture (database_architect, infrastructure_analyzer)
    ARCHITECTURE = "architecture"
    DESIGN_PATTERN = "design_pattern"
    
    # Accessibility (frontend_analyzer)
    ACCESSIBILITY = "accessibility"
    
    # Testing (tester)
    TEST_COVERAGE = "test_coverage"
    TEST_QUALITY = "test_quality"
    
    # Documentation (documenter)
    DOCUMENTATION = "documentation"
    
    # AI/ML (rag_architect, eval_architect, etc.)
    AI_QUALITY = "ai_quality"
    DATA_QUALITY = "data_quality"
    
    # General
    BEST_PRACTICE = "best_practice"
    DEPRECATION = "deprecation"
    CONFIGURATION = "configuration"


@dataclass
class Location:
    """Precise location of a finding in the codebase."""
    file: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    function: Optional[str] = None
    class_name: Optional[str] = None
    
    def __str__(self) -> str:
        loc = self.file
        if self.line_start:
            loc += f":{self.line_start}"
            if self.line_end and self.line_end != self.line_start:
                loc += f"-{self.line_end}"
        return loc


@dataclass
class Finding:
    """
    A standardized finding from any Forge agent.
    
    This is the primary schema for communicating analysis results between agents.
    All analyzers should output findings in this format to enable:
    - Consistent reporting across agents
    - Automated prioritization and triage
    - Integration with debugger/improver agents
    - Workflow orchestration
    """
    # Required fields
    agent: str                          # Name of the agent that produced this finding
    category: FindingCategory           # Type of finding
    severity: FindingSeverity           # How urgent is this?
    title: str                          # Short, descriptive title
    description: str                    # Detailed explanation
    location: Location                  # Where in the codebase
    
    # Identification
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    
    # Evidence and context
    evidence: Optional[str] = None      # Code snippet or data showing the issue
    context: Optional[str] = None       # Additional context about the finding
    
    # Remediation
    recommendation: Optional[str] = None  # How to fix this
    suggested_fix: Optional[str] = None   # Actual code fix if available
    effort_to_fix: Optional[str] = None   # "low", "medium", "high"
    
    # Metadata
    confidence: float = 1.0             # 0.0 to 1.0, how confident is the agent
    references: list[str] = field(default_factory=list)  # URLs, docs, etc.
    tags: list[str] = field(default_factory=list)        # Searchable tags
    related_findings: list[str] = field(default_factory=list)  # IDs of related findings
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Status tracking (for workflow integration)
    status: str = "open"  # open, acknowledged, in_progress, resolved, wont_fix
    assigned_to: Optional[str] = None  # Agent or human assigned to fix
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "agent": self.agent,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": {
                "file": self.location.file,
                "line_start": self.location.line_start,
                "line_end": self.location.line_end,
                "column_start": self.location.column_start,
                "column_end": self.location.column_end,
                "function": self.location.function,
                "class_name": self.location.class_name,
            },
            "evidence": self.evidence,
            "context": self.context,
            "recommendation": self.recommendation,
            "suggested_fix": self.suggested_fix,
            "effort_to_fix": self.effort_to_fix,
            "confidence": self.confidence,
            "references": self.references,
            "tags": self.tags,
            "related_findings": self.related_findings,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "assigned_to": self.assigned_to,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Finding":
        """Create Finding from dictionary."""
        location_data = data.get("location", {})
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8].upper()),
            agent=data["agent"],
            category=FindingCategory(data["category"]),
            severity=FindingSeverity(data["severity"]),
            title=data["title"],
            description=data["description"],
            location=Location(
                file=location_data.get("file", "unknown"),
                line_start=location_data.get("line_start"),
                line_end=location_data.get("line_end"),
                column_start=location_data.get("column_start"),
                column_end=location_data.get("column_end"),
                function=location_data.get("function"),
                class_name=location_data.get("class_name"),
            ),
            evidence=data.get("evidence"),
            context=data.get("context"),
            recommendation=data.get("recommendation"),
            suggested_fix=data.get("suggested_fix"),
            effort_to_fix=data.get("effort_to_fix"),
            confidence=data.get("confidence", 1.0),
            references=data.get("references", []),
            tags=data.get("tags", []),
            related_findings=data.get("related_findings", []),
            status=data.get("status", "open"),
            assigned_to=data.get("assigned_to"),
        )
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.id}: {self.title} ({self.location})"
