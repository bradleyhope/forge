"""Cost Tracking and Budget Management"""
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class CostEntry:
    """A single cost entry."""
    timestamp: float
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    task_id: str | None = None
    agent_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class BudgetAlert:
    """A budget alert."""
    threshold_percent: float
    message: str
    triggered_at: float

class CostTracker:
    """Tracks costs and manages budgets."""
    
    # Pricing per 1K tokens (as of 2025)
    PRICING = {
        "claude-opus-4": {"input": 0.015, "output": 0.075},
        "claude-sonnet-4": {"input": 0.003, "output": 0.015},
        "claude-haiku-3.5": {"input": 0.0008, "output": 0.004},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
        "gemini-2.0-pro": {"input": 0.00125, "output": 0.005},
    }
    
    def __init__(self, budget_usd: float = 10.0, persist_path: Path | None = None):
        self.budget_usd = budget_usd
        self.persist_path = persist_path
        self.entries: list[CostEntry] = []
        self.alerts: list[BudgetAlert] = []
        self._alert_thresholds = [0.5, 0.75, 0.9, 1.0]
        self._triggered_thresholds: set[float] = set()
        
        if persist_path:
            self._load()
    
    def _load(self):
        """Load persisted cost data."""
        if self.persist_path and self.persist_path.exists():
            try:
                data = json.loads(self.persist_path.read_text())
                self.entries = [CostEntry(**e) for e in data.get("entries", [])]
                self._triggered_thresholds = set(data.get("triggered_thresholds", []))
            except Exception as e:
                logger.warning(f"Failed to load cost data: {e}")
    
    def _save(self):
        """Save cost data to disk."""
        if self.persist_path:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "entries": [
                    {
                        "timestamp": e.timestamp,
                        "model": e.model,
                        "provider": e.provider,
                        "input_tokens": e.input_tokens,
                        "output_tokens": e.output_tokens,
                        "cost_usd": e.cost_usd,
                        "task_id": e.task_id,
                        "agent_name": e.agent_name,
                        "metadata": e.metadata,
                    }
                    for e in self.entries
                ],
                "triggered_thresholds": list(self._triggered_thresholds),
            }
            self.persist_path.write_text(json.dumps(data, indent=2))
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a given model and token counts."""
        pricing = self.PRICING.get(model, {"input": 0.003, "output": 0.015})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        provider: str = "anthropic",
        task_id: str | None = None,
        agent_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CostEntry:
        """Record a cost entry."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        entry = CostEntry(
            timestamp=time.time(),
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            task_id=task_id,
            agent_name=agent_name,
            metadata=metadata or {},
        )
        
        self.entries.append(entry)
        self._check_budget_alerts()
        self._save()
        
        logger.info(f"Recorded cost: ${cost:.4f} ({model}, {input_tokens}+{output_tokens} tokens)")
        return entry
    
    def _check_budget_alerts(self):
        """Check if any budget thresholds have been crossed."""
        total = self.get_total_cost()
        percent_used = total / self.budget_usd if self.budget_usd > 0 else 0
        
        for threshold in self._alert_thresholds:
            if threshold not in self._triggered_thresholds and percent_used >= threshold:
                self._triggered_thresholds.add(threshold)
                alert = BudgetAlert(
                    threshold_percent=threshold,
                    message=f"Budget alert: {threshold*100:.0f}% of ${self.budget_usd:.2f} used (${total:.2f})",
                    triggered_at=time.time(),
                )
                self.alerts.append(alert)
                logger.warning(alert.message)
    
    def get_total_cost(self) -> float:
        """Get total cost across all entries."""
        return sum(e.cost_usd for e in self.entries)
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget."""
        return max(0, self.budget_usd - self.get_total_cost())
    
    def is_over_budget(self) -> bool:
        """Check if over budget."""
        return self.get_total_cost() >= self.budget_usd
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of costs."""
        total = self.get_total_cost()
        by_model: dict[str, float] = {}
        by_agent: dict[str, float] = {}
        
        for entry in self.entries:
            by_model[entry.model] = by_model.get(entry.model, 0) + entry.cost_usd
            if entry.agent_name:
                by_agent[entry.agent_name] = by_agent.get(entry.agent_name, 0) + entry.cost_usd
        
        return {
            "total_cost_usd": total,
            "budget_usd": self.budget_usd,
            "remaining_usd": self.get_remaining_budget(),
            "percent_used": (total / self.budget_usd * 100) if self.budget_usd > 0 else 0,
            "entry_count": len(self.entries),
            "by_model": by_model,
            "by_agent": by_agent,
            "alerts": [{"threshold": a.threshold_percent, "message": a.message} for a in self.alerts],
        }
    
    def get_cost_by_timeframe(self, hours: float = 24) -> float:
        """Get cost within a timeframe."""
        cutoff = time.time() - (hours * 3600)
        return sum(e.cost_usd for e in self.entries if e.timestamp >= cutoff)
    
    def reset(self):
        """Reset all cost tracking."""
        self.entries = []
        self.alerts = []
        self._triggered_thresholds = set()
        self._save()


def estimate_cost(model: str, prompt_tokens: int, expected_output_tokens: int = 1000) -> float:
    """Estimate cost before making an API call."""
    tracker = CostTracker()
    return tracker.calculate_cost(model, prompt_tokens, expected_output_tokens)
