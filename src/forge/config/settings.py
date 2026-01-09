"""Forge Configuration Settings - SECURITY HARDENED"""
import os
import re
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """Mask a secret value for safe logging/display."""
    if not value or len(value) <= visible_chars:
        return "***"
    return value[:visible_chars] + "*" * (len(value) - visible_chars)


class ModelConfig(BaseModel):
    name: str
    provider: str = "anthropic"
    cost_per_1k_input: float = 0.003
    cost_per_1k_output: float = 0.015
    max_tokens: int = 8192
    strengths: list[str] = Field(default_factory=list)


class AgentConfig(BaseModel):
    name: str
    description: str = ""
    model: str = "claude-sonnet-4"
    tools: list[str] = Field(default_factory=list)
    prompt_template: str | None = None
    system_prompt: str | None = None
    max_turns: int = 50
    capabilities: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)


class MemoryConfig(BaseModel):
    max_context_tokens: int = 100_000
    persist_dir: Path = Field(default_factory=lambda: Path.home() / ".forge" / "memory")
    vector_db: str = "chroma"
    embedding_model: str = "text-embedding-3-small"


class GitConfig(BaseModel):
    auto_commit: bool = True
    branch_prefix: str = "forge/"
    commit_prefix: str = "[Forge]"


class ForgeSettings(BaseSettings):
    project_dir: Path = Field(default_factory=Path.cwd)
    config_dir: Path | None = None
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    default_model: str = "claude-sonnet-4"
    max_budget_usd: float = 10.0
    log_level: str = "INFO"
    log_file: Path | None = None
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    models: dict[str, ModelConfig] = Field(default_factory=lambda: {
        "claude-opus-4": ModelConfig(name="claude-opus-4", provider="anthropic", cost_per_1k_input=0.015, cost_per_1k_output=0.075, strengths=["complex_reasoning", "coding"]),
        "claude-sonnet-4": ModelConfig(name="claude-sonnet-4", provider="anthropic", cost_per_1k_input=0.003, cost_per_1k_output=0.015, strengths=["coding", "analysis"]),
    })
    
    @property
    def budget_usd(self) -> float:
        """Alias for max_budget_usd for compatibility."""
        return self.max_budget_usd
    
    @property
    def anthropic_api_key_masked(self) -> str:
        """Get masked API key for safe logging."""
        return mask_secret(self.anthropic_api_key)
    
    @property
    def openai_api_key_masked(self) -> str:
        """Get masked API key for safe logging."""
        return mask_secret(self.openai_api_key)
    
    def validate_api_keys(self) -> dict[str, bool]:
        """Validate that required API keys are set."""
        return {
            "anthropic": bool(self.anthropic_api_key and len(self.anthropic_api_key) > 10),
            "openai": bool(self.openai_api_key and len(self.openai_api_key) > 10),
        }
    
    def __repr__(self) -> str:
        """Safe repr that masks secrets."""
        return (
            f"ForgeSettings(project_dir={self.project_dir}, "
            f"anthropic_api_key={self.anthropic_api_key_masked}, "
            f"openai_api_key={self.openai_api_key_masked}, "
            f"default_model={self.default_model})"
        )
    
    def __str__(self) -> str:
        return self.__repr__()
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.config_dir is None:
            self.config_dir = self.project_dir / "config"
