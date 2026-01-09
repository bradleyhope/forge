# Forge

**AI-Powered Software Engineering Platform**

Forge is a multi-agent system built on the Claude Agent SDK that provides autonomous code analysis, debugging, and improvement capabilities.

## Features

- **19 Specialized Agents** for different tasks
- **Intelligent Routing** - automatically selects the best model for each task
- **Memory System** - short-term and long-term memory for context
- **Git Integration** - auto-branching and commits
- **Cost Tracking** - budget management and cost reporting

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# List available agents
forge agents

# Analyze a project
forge analyze /path/to/project

# Fix a specific issue
forge fix "Fix the authentication bug in auth.py"

# Run a complete workflow
forge run "Review and improve the API endpoints"
```

## Agents

### Specialists
- `backend_analyzer` - Backend code analysis
- `frontend_analyzer` - Frontend/UI analysis
- `security_analyzer` - Security vulnerability scanning
- `database_architect` - Database design and optimization
- `vector_search_architect` - Vector search pipeline design
- `langchain_architect` - LangChain pipeline design
- `prompt_engineer` - Prompt optimization

### Infrastructure
- `graph_architect` - Neo4j knowledge graph design
- `chunking_strategist` - Document chunking for RAG
- `embedding_architect` - Embedding model selection
- `rag_architect` - RAG pipeline design
- `agent_architect` - LLM agent architecture design
- `eval_architect` - LLM evaluation frameworks
- `infrastructure_analyzer` - Cloud/DevOps analysis

### Actions
- `debugger` - Bug fixing
- `improver` - Code refactoring
- `tester` - Test creation
- `documenter` - Documentation
- `project_steward` - Project hygiene

## Environment Variables

```bash
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key  # Optional
```

## License

MIT
