"""Claude Agent SDK Integration - FIXED for proper message handling"""
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

When you are done analyzing, provide a clear summary of your findings.
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
                msg_type = type(message).__name__
                
                # Skip system/init messages
                if msg_type == 'SystemMessage':
                    continue
                
                turns_used += 1
                
                # Extract content from assistant messages
                if msg_type == 'AssistantMessage':
                    content = getattr(message, 'content', None)
                    if content:
                        if isinstance(content, list):
                            for item in content:
                                # Handle TextBlock
                                if hasattr(item, 'text'):
                                    text = getattr(item, 'text', '')
                                    if text:
                                        output_parts.append(text)
                                elif isinstance(item, dict) and item.get('type') == 'text':
                                    output_parts.append(item.get('text', ''))
                        elif isinstance(content, str):
                            output_parts.append(content)
                
                # Handle ResultMessage - extract cost info
                if msg_type == 'ResultMessage':
                    # Extract cost from result message
                    result_cost = getattr(message, 'total_cost_usd', 0.0)
                    if result_cost:
                        total_cost = result_cost
                    
                    # Extract usage info
                    usage = getattr(message, 'usage', None)
                    if usage:
                        if isinstance(usage, dict):
                            total_tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                        else:
                            total_tokens = getattr(usage, 'input_tokens', 0) + getattr(usage, 'output_tokens', 0)
                    
                    # Check if it was a max_turns termination (still consider it success if we have output)
                    subtype = getattr(message, 'subtype', '')
                    if subtype == 'error_max_turns' and output_parts:
                        self.logger.warning("Max turns reached, but returning partial results")
                
                # Safely extract usage/cost info from other messages
                usage = getattr(message, 'usage', None)
                if usage and not total_tokens:
                    if isinstance(usage, dict):
                        total_tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                    else:
                        input_tokens = getattr(usage, 'input_tokens', 0)
                        output_tokens = getattr(usage, 'output_tokens', 0)
                        total_tokens = input_tokens + output_tokens
                    
        except GeneratorExit:
            pass
        except Exception as e:
            error_msg = str(e)
            # Don't treat async cleanup errors as fatal if we have output
            if output_parts and ("cancel scope" in error_msg or "has no attribute" in error_msg):
                self.logger.warning(f"Non-fatal SDK cleanup: {error_msg}")
            else:
                self.logger.error(f"Agent execution failed: {e}")
                return AgentResult(
                    success=False,
                    output="\n".join(output_parts) if output_parts else "",
                    error=error_msg,
                )
        
        output = "\n".join(output_parts)
        
        # Estimate cost if not provided
        if not total_cost and total_tokens:
            model = self.definition.model
            if "opus" in model.lower():
                cost_per_1k = 0.015
            elif "sonnet" in model.lower():
                cost_per_1k = 0.003
            else:
                cost_per_1k = 0.003
            total_cost = (total_tokens / 1000) * cost_per_1k
        
        return AgentResult(
            success=bool(output),
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
        return await super().execute(task)
