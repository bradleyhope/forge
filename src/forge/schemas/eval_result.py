"""
EvalResult Schema - Standardized format for evaluation and testing outcomes.

An EvalResult represents the outcome of any evaluation, test, or quality check.
This schema is used by:
- tester (test execution results)
- eval_architect (LLM evaluation results)
- security_analyzer (security scan results)
- frontend_analyzer (accessibility/performance audits)

Usage:
    result = EvalResult(
        id="EVAL-001",
        agent="tester",
        name="Authentication Test Suite",
        status=EvalStatus.PASSED,
        metrics=[
            EvalMetric(name="tests_passed", value=45, unit="count"),
            EvalMetric(name="tests_failed", value=2, unit="count"),
            EvalMetric(name="coverage", value=87.5, unit="percent"),
            EvalMetric(name="duration", value=12.3, unit="seconds"),
        ],
        passed_checks=["login", "logout", "token_refresh"],
        failed_checks=["password_reset", "mfa_enrollment"],
        dataset="test/fixtures/auth_users.json",
    )
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import uuid


class EvalStatus(Enum):
    """Overall status of an evaluation."""
    PASSED = "passed"          # All checks passed
    FAILED = "failed"          # One or more checks failed
    PARTIAL = "partial"        # Some checks passed, some failed
    ERROR = "error"            # Evaluation could not complete
    SKIPPED = "skipped"        # Evaluation was skipped
    PENDING = "pending"        # Evaluation not yet run


class MetricType(Enum):
    """Types of metrics that can be reported."""
    COUNT = "count"            # Integer count
    PERCENT = "percent"        # Percentage (0-100)
    RATIO = "ratio"            # Ratio (0-1)
    DURATION = "duration"      # Time in seconds
    SIZE = "size"              # Size in bytes
    SCORE = "score"            # Arbitrary score
    CURRENCY = "currency"      # Cost in USD


@dataclass
class EvalMetric:
    """
    A single metric from an evaluation.
    
    Metrics provide quantitative data about evaluation outcomes.
    """
    name: str                           # Metric name (e.g., "coverage", "latency")
    value: float                        # Numeric value
    unit: str = "count"                 # Unit of measurement
    
    # Thresholds for pass/fail determination
    threshold_min: Optional[float] = None   # Minimum acceptable value
    threshold_max: Optional[float] = None   # Maximum acceptable value
    
    # Comparison to baseline
    baseline: Optional[float] = None        # Previous/expected value
    delta: Optional[float] = None           # Change from baseline
    delta_percent: Optional[float] = None   # Percentage change
    
    # Status
    passed: bool = True                     # Did this metric pass its threshold?
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "threshold_min": self.threshold_min,
            "threshold_max": self.threshold_max,
            "baseline": self.baseline,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
            "passed": self.passed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EvalMetric":
        return cls(
            name=data["name"],
            value=data["value"],
            unit=data.get("unit", "count"),
            threshold_min=data.get("threshold_min"),
            threshold_max=data.get("threshold_max"),
            baseline=data.get("baseline"),
            delta=data.get("delta"),
            delta_percent=data.get("delta_percent"),
            passed=data.get("passed", True),
        )
    
    def __str__(self) -> str:
        status = "✓" if self.passed else "✗"
        return f"{status} {self.name}: {self.value} {self.unit}"


@dataclass
class CheckResult:
    """Result of a single check within an evaluation."""
    name: str
    passed: bool
    message: Optional[str] = None
    duration_ms: Optional[float] = None
    details: Optional[dict] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }


@dataclass
class EvalResult:
    """
    A standardized evaluation result from any Forge agent.
    
    EvalResults capture the outcome of:
    - Unit/integration/E2E tests
    - LLM evaluations (accuracy, hallucination rate, etc.)
    - Security scans
    - Performance benchmarks
    - Accessibility audits
    - Code quality checks
    """
    # Required fields
    agent: str                          # Agent that ran the evaluation
    name: str                           # Name of the evaluation
    status: EvalStatus                  # Overall pass/fail status
    
    # Identification
    id: str = field(default_factory=lambda: f"EVAL-{str(uuid.uuid4())[:8].upper()}")
    
    # Metrics
    metrics: list[EvalMetric] = field(default_factory=list)
    
    # Individual checks
    checks: list[CheckResult] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    skipped_checks: list[str] = field(default_factory=list)
    
    # Summary statistics
    total_checks: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    
    # Dataset/input information
    dataset: Optional[str] = None           # Dataset used for evaluation
    dataset_size: Optional[int] = None      # Number of samples
    sample_ids: list[str] = field(default_factory=list)  # Specific samples evaluated
    
    # Timing
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Context
    description: Optional[str] = None
    configuration: Optional[dict] = None    # Eval configuration used
    environment: Optional[dict] = None      # Runtime environment info
    
    # Related entities
    finding_ids: list[str] = field(default_factory=list)    # Findings generated
    change_plan_id: Optional[str] = None                    # Related ChangePlan
    
    # Artifacts
    artifacts: list[str] = field(default_factory=list)      # Paths to output files
    logs: list[str] = field(default_factory=list)           # Execution logs
    
    # Error information (if status is ERROR)
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.passed_count / self.total_checks) * 100
    
    @property
    def is_passing(self) -> bool:
        """Check if evaluation is considered passing."""
        return self.status in (EvalStatus.PASSED, EvalStatus.PARTIAL)
    
    def add_metric(self, metric: EvalMetric) -> None:
        """Add a metric to the result."""
        self.metrics.append(metric)
    
    def add_check(self, check: CheckResult) -> None:
        """Add a check result and update counts."""
        self.checks.append(check)
        self.total_checks += 1
        if check.passed:
            self.passed_count += 1
            self.passed_checks.append(check.name)
        else:
            self.failed_count += 1
            self.failed_checks.append(check.name)
    
    def get_metric(self, name: str) -> Optional[EvalMetric]:
        """Get a metric by name."""
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent": self.agent,
            "name": self.name,
            "status": self.status.value,
            "metrics": [m.to_dict() for m in self.metrics],
            "checks": [c.to_dict() for c in self.checks],
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "skipped_checks": self.skipped_checks,
            "total_checks": self.total_checks,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "pass_rate": self.pass_rate,
            "dataset": self.dataset,
            "dataset_size": self.dataset_size,
            "sample_ids": self.sample_ids,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "description": self.description,
            "configuration": self.configuration,
            "environment": self.environment,
            "finding_ids": self.finding_ids,
            "change_plan_id": self.change_plan_id,
            "artifacts": self.artifacts,
            "logs": self.logs,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EvalResult":
        result = cls(
            id=data.get("id", f"EVAL-{str(uuid.uuid4())[:8].upper()}"),
            agent=data["agent"],
            name=data["name"],
            status=EvalStatus(data["status"]),
            metrics=[EvalMetric.from_dict(m) for m in data.get("metrics", [])],
            passed_checks=data.get("passed_checks", []),
            failed_checks=data.get("failed_checks", []),
            skipped_checks=data.get("skipped_checks", []),
            total_checks=data.get("total_checks", 0),
            passed_count=data.get("passed_count", 0),
            failed_count=data.get("failed_count", 0),
            skipped_count=data.get("skipped_count", 0),
            dataset=data.get("dataset"),
            dataset_size=data.get("dataset_size"),
            sample_ids=data.get("sample_ids", []),
            duration_seconds=data.get("duration_seconds"),
            description=data.get("description"),
            configuration=data.get("configuration"),
            environment=data.get("environment"),
            finding_ids=data.get("finding_ids", []),
            change_plan_id=data.get("change_plan_id"),
            artifacts=data.get("artifacts", []),
            logs=data.get("logs", []),
            error_message=data.get("error_message"),
            error_traceback=data.get("error_traceback"),
        )
        return result
    
    def __str__(self) -> str:
        return f"[{self.status.value.upper()}] {self.id}: {self.name} ({self.pass_rate:.1f}% pass rate)"
