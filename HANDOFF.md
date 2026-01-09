# Forge v0.2.0 - Handoff Document

## Overview

**Forge** is a multi-agent AI engineering platform built on the Claude Agent SDK. It provides autonomous code analysis, debugging, improvement, and AI/data infrastructure design capabilities.

## What's New in v0.2.0

- **Real Claude Agent SDK Integration** - Uses the actual `claude-agent-sdk` package
- **Custom Forge Tools** - 4 custom MCP tools for project analysis
- **Cost Tracking** - Budget management with alerts
- **19 Specialized Agents** - Full roster of specialists

## Quick Start

```bash
# Install
cd /home/ubuntu/forge
pip install -e .

# Set API key
export ANTHROPIC_API_KEY=your_key

# List agents
forge agents

# Analyze a project
forge analyze /path/to/project

# Fix an issue
forge fix "Fix the authentication bug"

# Run a workflow
forge run "Review and improve the API"
```

## Project Structure

```
/home/ubuntu/forge/
├── src/forge/
│   ├── __init__.py          # Main package
│   ├── orchestrator.py      # Central orchestrator
│   ├── router.py            # AI model router
│   ├── cli.py               # CLI interface
│   ├── agents/
│   │   ├── base.py          # Base agent classes
│   │   ├── claude_agent.py  # Real Claude SDK integration
│   │   ├── specialists.py   # Specialist agents (7)
│   │   ├── actions.py       # Action agents (5)
│   │   ├── infrastructure.py # Infrastructure agents (7)
│   │   └── subagent.py      # Subagent orchestration
│   ├── memory/
│   │   ├── manager.py       # Memory management
│   │   ├── condenser.py     # Context condensation
│   │   └── vector_store.py  # ChromaDB integration
│   ├── tools/
│   │   ├── git.py           # Git integration
│   │   ├── code.py          # Code analysis
│   │   ├── mcp.py           # MCP tool integration
│   │   └── forge_tools.py   # Custom Forge tools
│   └── utils/
│       ├── logging.py       # Logging utilities
│       └── cost_tracker.py  # Cost tracking
├── examples/
│   └── test_sdk_integration.py  # Integration tests
├── pyproject.toml           # Package config
├── README.md                # User documentation
└── HANDOFF.md               # This file
```

## Agents (19 Total)

### Specialists (7)
| Agent | Purpose |
|-------|---------|
| backend_analyzer | Backend code analysis |
| frontend_analyzer | Frontend/UI analysis |
| security_analyzer | Security scanning |
| database_architect | Database design |
| vector_search_architect | Vector search design |
| langchain_architect | LangChain pipelines |
| prompt_engineer | Prompt optimization |

### Actions (5)
| Agent | Purpose |
|-------|---------|
| debugger | Bug fixing |
| improver | Code refactoring |
| tester | Test creation |
| documenter | Documentation |
| project_steward | Project hygiene |

### Infrastructure (7)
| Agent | Purpose |
|-------|---------|
| graph_architect | Neo4j knowledge graphs |
| chunking_strategist | RAG chunking |
| embedding_architect | Embedding models |
| rag_architect | RAG pipelines |
| agent_architect | LLM agent design |
| eval_architect | LLM evaluation |
| infrastructure_analyzer | Cloud/DevOps |

## Custom Forge Tools

| Tool | Description |
|------|-------------|
| analyze_project | Analyze project structure |
| search_code | Search for patterns in code |
| get_file_info | Get file details and preview |
| run_tests | Run project tests |

## Claude Agent SDK Integration

The `ClaudeAgent` class in `claude_agent.py` uses the real SDK:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt="...",
    allowed_tools=["Read", "Write", "Bash"],
    max_turns=50,
    cwd="/path/to/project",
    permission_mode="acceptEdits",
)

async for message in query(prompt="...", options=options):
    # Process messages
```

## Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY=your_anthropic_key

# Optional (for multi-LLM routing)
export OPENAI_API_KEY=your_openai_key
export GEMINI_API_KEY=your_gemini_key
```

## Testing

```bash
# Run integration tests
python examples/test_sdk_integration.py

# Test CLI
forge agents
forge --help
```

## Next Steps

1. Add more custom tools
2. Implement multi-LLM routing
3. Add Neo4j integration
4. GitHub Actions integration
5. Integrate with Rook/Athena

## Related Resources

- Claude Agent SDK: https://docs.anthropic.com/en/docs/agents-and-tools/claude-agent-sdk
- SDK Python Package: https://pypi.org/project/claude-agent-sdk/
