"""Claude Agent SDK Integration - FIXED"""
import asyncio
import logging
from pathlib import Path
from typing import Any

from forge.agents.base import AgentDefinition, AgentResult, BaseAgent, Task
from forge.config.settings import ForgeSettings

logger = logging.getLogger(__name__)

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("Claude Agent SDK not available")


class ClaudeAgent(BaseAgent):
    """Agent that uses the Claude Agent SDK for execution."""
    
    def __init__(
        self,
        definition: AgentDefinition,
        settings: ForgeSettings | None = None,
        working_dir: Path | None = None,
    ):
        super().__init__(definition)
        self.settings = settings or ForgeSettings()
        self.working_dir = working_dir or Path.cwd()
    
    def _build_prompt(self, task: Task) -> str:
        """Build the full prompt for the agent."""
        context = task.context.copy()
        context["task"] = task.description
        context["working_dir"] = str(self.working_dir)
        
        base_prompt = self.definition.render_prompt(context)
        
        return f"""{base_prompt}

## Current Task
{task.description}

## Working Directory
{self.working_dir}

## Instructions
1. Analyze the codebase thoroughly
2. Identify issues based on your focus areas
3. Provide detailed findings with file locations and line numbers
4. Suggest specific fixes for each issue
5. Prioritize issues by severity (critical, high, medium, low)
"""
    
    async def execute(self, task: Task) -> AgentResult:
        """Execute a task using the Claude Agent SDK."""
        if not SDK_AVAILABLE:
            return AgentResult(
                success=False,
                output="",
                error="Claude Agent SDK not available",
            )
        
        prompt = self._build_prompt(task)
        
        options = ClaudeAgentOptions(
            system_prompt=self.definition.prompt_template or "",
            allowed_tools=self.definition.tools or ["Read", "Glob", "Grep"],
            max_turns=self.definition.max_turns,
            cwd=str(self.working_dir),
            permission_mode="acceptEdits",
            model=self.definition.model,
        )
        
        output_parts = []
        total_cost = 0.0
        total_tokens = 0
        turns_used = 0
        
        try:
            async for message in query(prompt=prompt, options=options):
                turns_used += 1
                
                # Safely extract content using getattr with defaults
                content = getattr(message, 'content', None)
                if content:
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                output_parts.append(item.get('text', ''))
                            elif hasattr(item, 'type') and item.type == 'text':
                                output_parts.append(getattr(item, 'text', ''))
                    elif isinstance(content, str):
                        output_parts.append(content)
                
                # Safely extract usage/cost info
                usage = getattr(message, 'usage', None)
                if usage:
                    input_tokens = getattr(usage, 'input_tokens', 0)
                    output_tokens = getattr(usage, 'output_tokens', 0)
                    total_tokens += input_tokens + output_tokens
                
                # Check for result message
                if hasattr(message, 'is_result') and message.is_result:
                    break
                    
        except Exception as e:
            error_msg = str(e)
            # Don't treat "no attribute" errors as fatal if we have output
            if output_parts and "has no attribute" in error_msg:
                self.logger.warning(f"Non-fatal SDK error: {error_msg}")
            else:
                self.logger.error(f"Agent execution failed: {e}")
                return AgentResult(
                    success=False,
                    output="\n".join(output_parts) if output_parts else "",
                    error=error_msg,
                )
        
        output = "\n".join(output_parts)
        
        # Estimate cost based on model
        model = self.definition.model
        if "opus" in model.lower():
            cost_per_1k = 0.015
        elif "sonnet" in model.lower():
            cost_per_1k = 0.003
        else:
            cost_per_1k = 0.003
        
        total_cost = (total_tokens / 1000) * cost_per_1k
        
        return AgentResult(
            success=True,
            output=output,
            cost_usd=total_cost,
            tokens_used=total_tokens,
            turns_used=turns_used,
        )


class ClaudeAgentWithClient(ClaudeAgent):
    """Extended Claude Agent with custom tools and hooks."""
    
    def __init__(
        self,
        definition: AgentDefinition,
        settings: ForgeSettings | None = None,
        working_dir: Path | None = None,
        custom_tools: list | None = None,
        hooks: dict | None = None,
    ):
        super().__init__(definition, settings, working_dir)
        self.custom_tools = custom_tools or []
        self.hooks = hooks or {}
    
    async def execute(self, task: Task) -> AgentResult:
        """Execute with custom tools and hooks."""
        # For now, use the base implementation
        # Custom tools would be added via MCP in a full implementation
        return await super().execute(task)
