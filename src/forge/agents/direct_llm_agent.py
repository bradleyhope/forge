"""
Direct LLM Agent - Uses API calls directly instead of Claude Agent SDK.
This provides more control and avoids SDK-related hangs.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Optional

from forge.agents.base import AgentDefinition, AgentResult, BaseAgent, Task
from forge.config.settings import ForgeSettings

logger = logging.getLogger(__name__)


class DirectLLMAgent(BaseAgent):
    """
    Agent that uses direct API calls to LLMs.
    Supports Claude, GPT, Gemini, and Grok.
    """
    
    def __init__(
        self,
        definition: AgentDefinition,
        settings: ForgeSettings | None = None,
        working_dir: Path | None = None,
        llm_provider: str = "claude",  # claude, openai, gemini, grok
    ):
        super().__init__(definition)
        self.settings = settings or ForgeSettings()
        self.working_dir = working_dir or Path.cwd()
        self.llm_provider = llm_provider
        self._client = None
    
    def _get_client(self):
        """Get or create the appropriate LLM client."""
        if self._client:
            return self._client
        
        if self.llm_provider == "claude":
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )
        elif self.llm_provider == "openai":
            import openai
            self._client = openai.OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY"),
                base_url=os.environ.get("OPENAI_API_BASE")
            )
        elif self.llm_provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            self._client = genai
        elif self.llm_provider == "grok":
            # Grok uses OpenAI-compatible API
            import openai
            self._client = openai.OpenAI(
                api_key=os.environ.get("XAI_API_KEY"),
                base_url="https://api.x.ai/v1"
            )
        
        return self._client
    
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
    
    def _get_model_name(self) -> str:
        """Get the appropriate model name for the provider."""
        if self.llm_provider == "claude":
            return self.definition.model or "claude-sonnet-4-20250514"
        elif self.llm_provider == "openai":
            return "gpt-4o"
        elif self.llm_provider == "gemini":
            return "gemini-2.5-flash"
        elif self.llm_provider == "grok":
            return "grok-3"
        return self.definition.model
    
    async def execute(self, task: Task) -> AgentResult:
        """Execute a task using direct API calls."""
        prompt = self._build_prompt(task)
        client = self._get_client()
        
        try:
            if self.llm_provider == "claude":
                response = client.messages.create(
                    model=self._get_model_name(),
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
                output = response.content[0].text
                tokens = response.usage.input_tokens + response.usage.output_tokens
                cost = self._estimate_cost(tokens, "claude")
                
            elif self.llm_provider == "openai":
                response = client.chat.completions.create(
                    model=self._get_model_name(),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096
                )
                output = response.choices[0].message.content
                tokens = response.usage.total_tokens
                cost = self._estimate_cost(tokens, "openai")
                
            elif self.llm_provider == "gemini":
                model = client.GenerativeModel(self._get_model_name())
                response = model.generate_content(prompt)
                output = response.text
                tokens = 0  # Gemini doesn't always return token count
                cost = 0.01  # Estimate
                
            elif self.llm_provider == "grok":
                response = client.chat.completions.create(
                    model=self._get_model_name(),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096
                )
                output = response.choices[0].message.content
                tokens = response.usage.total_tokens if response.usage else 0
                cost = self._estimate_cost(tokens, "grok")
            
            return AgentResult(
                success=True,
                output=output,
                cost_usd=cost,
                tokens_used=tokens,
                turns_used=1,
            )
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return AgentResult(
                success=False,
                output="",
                error=str(e),
            )
    
    def _estimate_cost(self, tokens: int, provider: str) -> float:
        """Estimate cost based on tokens and provider."""
        rates = {
            "claude": 0.003,  # per 1K tokens (sonnet)
            "openai": 0.005,  # per 1K tokens (gpt-4o)
            "gemini": 0.001,  # per 1K tokens
            "grok": 0.005,    # per 1K tokens
        }
        return (tokens / 1000) * rates.get(provider, 0.003)


class MultiLLMOrchestrator:
    """
    Orchestrator that runs the same task across multiple LLMs
    and synthesizes the results.
    """
    
    def __init__(
        self,
        definition: AgentDefinition,
        settings: ForgeSettings | None = None,
        working_dir: Path | None = None,
        providers: list[str] = None,
    ):
        self.definition = definition
        self.settings = settings or ForgeSettings()
        self.working_dir = working_dir or Path.cwd()
        self.providers = providers or ["claude", "openai", "gemini", "grok"]
        self.agents = {}
        
        for provider in self.providers:
            self.agents[provider] = DirectLLMAgent(
                definition=definition,
                settings=settings,
                working_dir=working_dir,
                llm_provider=provider,
            )
    
    async def execute_all(self, task: Task, timeout: int = 120) -> dict[str, AgentResult]:
        """Execute task across all providers in parallel."""
        results = {}
        
        async def run_agent(provider: str):
            try:
                result = await asyncio.wait_for(
                    self.agents[provider].execute(task),
                    timeout=timeout
                )
                return provider, result
            except asyncio.TimeoutError:
                return provider, AgentResult(
                    success=False,
                    output="",
                    error=f"Timeout after {timeout}s"
                )
            except Exception as e:
                return provider, AgentResult(
                    success=False,
                    output="",
                    error=str(e)
                )
        
        tasks = [run_agent(p) for p in self.providers]
        completed = await asyncio.gather(*tasks)
        
        for provider, result in completed:
            results[provider] = result
        
        return results
    
    def synthesize_results(self, results: dict[str, AgentResult]) -> str:
        """Synthesize results from multiple LLMs into a unified report."""
        synthesis = ["# Multi-LLM Analysis Synthesis\n"]
        
        for provider, result in results.items():
            synthesis.append(f"\n## {provider.upper()} Analysis\n")
            if result.success:
                synthesis.append(result.output)
            else:
                synthesis.append(f"*Error: {result.error}*")
        
        return "\n".join(synthesis)
