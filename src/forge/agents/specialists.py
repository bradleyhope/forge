"""Specialist Agents for code analysis"""
from forge.agents.base import AgentDefinition

BACKEND_ANALYZER = AgentDefinition(
    name="backend_analyzer",
    description="Analyzes backend code for bugs, performance issues, and architectural problems.",
    prompt_template="""You are the Backend Analyzer. Analyze code for:
1. Bugs and logic errors
2. Performance issues (N+1 queries, memory leaks)
3. Security vulnerabilities
4. Code quality and best practices
{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Grep", "Glob", "Bash"],
    capabilities=["bug_detection", "performance_analysis", "code_review"],
)

FRONTEND_ANALYZER = AgentDefinition(
    name="frontend_analyzer",
    description="Analyzes frontend code for visual bugs, accessibility, and performance.",
    prompt_template="""You are the Frontend Analyzer. Analyze frontend code for:
1. Visual bugs and layout issues
2. Accessibility (WCAG compliance)
3. Performance (bundle size, rendering)
4. Best practices (React, Vue, etc.)
{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Grep", "Glob", "Bash"],
    capabilities=["ui_analysis", "accessibility", "performance"],
)

SECURITY_ANALYZER = AgentDefinition(
    name="security_analyzer",
    description="Analyzes code for security vulnerabilities.",
    prompt_template="""You are the Security Analyzer. Check for:
1. OWASP Top 10 vulnerabilities
2. Injection attacks (SQL, XSS, etc.)
3. Authentication/authorization issues
4. Secrets in code
5. Dependency vulnerabilities
{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Grep", "Glob", "Bash"],
    capabilities=["security_audit", "vulnerability_detection"],
)

DATABASE_ARCHITECT = AgentDefinition(
    name="database_architect",
    description="Designs and optimizes database schemas and queries.",
    prompt_template="""You are the Database Architect. Help with:
1. Schema design and normalization
2. Query optimization (EXPLAIN analysis)
3. Indexing strategies
4. Migration planning
{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Write", "Bash"],
    capabilities=["schema_design", "query_optimization"],
)

VECTOR_SEARCH_ARCHITECT = AgentDefinition(
    name="vector_search_architect",
    description="Designs vector search pipelines and embedding strategies.",
    prompt_template="""You are the Vector Search Architect. Help with:
1. Embedding model selection
2. Chunking strategies
3. Hybrid search (dense + sparse)
4. Vector database selection
{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Write", "Bash"],
    capabilities=["embeddings", "semantic_search"],
)

LANGCHAIN_ARCHITECT = AgentDefinition(
    name="langchain_architect",
    description="Designs LangChain pipelines and agent architectures.",
    prompt_template="""You are the LangChain Architect. Help with:
1. Chain design and composition
2. Agent architectures (ReAct, etc.)
3. Tool integration
4. Memory strategies
{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Write", "Bash"],
    capabilities=["langchain", "agent_design"],
)

PROMPT_ENGINEER = AgentDefinition(
    name="prompt_engineer",
    description="Designs and optimizes prompts for LLM applications.",
    prompt_template="""You are the Prompt Engineer. Help with:
1. Prompt design and optimization
2. Few-shot examples
3. Output parsing
4. Model-specific tuning
{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Write"],
    capabilities=["prompt_design", "optimization"],
)

SPECIALIST_AGENTS = {
    "backend_analyzer": BACKEND_ANALYZER,
    "frontend_analyzer": FRONTEND_ANALYZER,
    "security_analyzer": SECURITY_ANALYZER,
    "database_architect": DATABASE_ARCHITECT,
    "vector_search_architect": VECTOR_SEARCH_ARCHITECT,
    "langchain_architect": LANGCHAIN_ARCHITECT,
    "prompt_engineer": PROMPT_ENGINEER,
}

def get_specialist(name: str) -> AgentDefinition | None:
    return SPECIALIST_AGENTS.get(name)

def list_specialists() -> list[str]:
    return list(SPECIALIST_AGENTS.keys())
