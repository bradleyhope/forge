#!/usr/bin/env python3
"""Test script for Claude Agent SDK integration."""
import asyncio
import os
import sys

# Check for API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("⚠️  ANTHROPIC_API_KEY not set - SDK calls will fail")
    print("   Set it with: export ANTHROPIC_API_KEY=your_key")
    print()

async def test_basic_import():
    """Test basic imports work."""
    print("1. Testing imports...")
    try:
        from forge import Forge
        from forge.agents import ALL_AGENTS
        from forge.agents.claude_agent import ClaudeAgent, ClaudeAgentWithClient
        from forge.agents.base import AgentDefinition, Task, AgentResult
        print("   ✓ All imports successful")
        return True
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

async def test_forge_initialization():
    """Test Forge can be initialized."""
    print("\n2. Testing Forge initialization...")
    try:
        from forge import Forge
        forge = Forge()
        agents = forge.list_agents()
        print(f"   ✓ Forge initialized with {len(agents)} agents")
        return True
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return False

async def test_agent_creation():
    """Test agent creation."""
    print("\n3. Testing agent creation...")
    try:
        from forge import Forge
        forge = Forge()
        agent = forge.get_agent("backend_analyzer")
        if agent:
            print(f"   ✓ Agent created: {agent.definition.name}")
            print(f"     Model: {agent.definition.model}")
            print(f"     Tools: {agent.definition.tools}")
            return True
        else:
            print("   ✗ Agent not found")
            return False
    except Exception as e:
        print(f"   ✗ Agent creation failed: {e}")
        return False

async def test_sdk_availability():
    """Test Claude Agent SDK is available."""
    print("\n4. Testing Claude Agent SDK availability...")
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage
        print("   ✓ Claude Agent SDK imported successfully")
        return True
    except ImportError as e:
        print(f"   ✗ SDK not available: {e}")
        return False

async def test_custom_tools():
    """Test custom Forge tools."""
    print("\n5. Testing custom Forge tools...")
    try:
        from forge.tools.forge_tools import FORGE_TOOLS, get_forge_tools
        tools = get_forge_tools()
        print(f"   ✓ {len(tools)} custom tools available:")
        for tool in tools:
            name = getattr(tool, '_tool_name', tool.__name__)
            print(f"     - {name}")
        return True
    except Exception as e:
        print(f"   ✗ Custom tools failed: {e}")
        return False

async def test_cost_tracker():
    """Test cost tracking."""
    print("\n6. Testing cost tracker...")
    try:
        from forge.utils.cost_tracker import CostTracker
        tracker = CostTracker(budget_usd=10.0)
        tracker.record("claude-sonnet-4", input_tokens=1000, output_tokens=500)
        summary = tracker.get_summary()
        print(f"   ✓ Cost tracker working")
        print(f"     Total cost: ${summary['total_cost_usd']:.4f}")
        print(f"     Budget: ${summary['budget_usd']:.2f}")
        return True
    except Exception as e:
        print(f"   ✗ Cost tracker failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("=" * 50)
    print("Forge SDK Integration Tests")
    print("=" * 50)
    
    results = []
    results.append(await test_basic_import())
    results.append(await test_forge_initialization())
    results.append(await test_agent_creation())
    results.append(await test_sdk_availability())
    results.append(await test_custom_tools())
    results.append(await test_cost_tracker())
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
