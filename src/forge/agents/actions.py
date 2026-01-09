"""Action Agents for implementing fixes and improvements"""
from forge.agents.base import AgentDefinition

DEBUGGER = AgentDefinition(
    name="debugger",
    description="Implements targeted fixes for specific issues identified by analyzers.",
    prompt_template="""You are the Debugger. Your job is to fix bugs:
1. Understand the issue thoroughly
2. Identify the root cause
3. Implement a minimal, targeted fix
4. Verify the fix doesn't break other code
{{ context | default('') }}""",
    model="claude-sonnet-4",
    tools=["Read", "Write", "Edit", "Bash", "Grep"],
    capabilities=["bug_fixing", "debugging"],
)

IMPROVER = AgentDefinition(
    name="improver",
    description="Refactors and optimizes code based on analyzer recommendations.",
    prompt_template="""You are the Improver. Your job is to improve code:
1. Refactor for clarity and maintainability
2. Optimize performance
3. Apply best practices
4. Maintain backward compatibility
{{ context | default('') }}""",
    model="claude-sonnet-4",
    tools=["Read", "Write", "Edit", "Bash"],
    capabilities=["refactoring", "optimization"],
)

TESTER = AgentDefinition(
    name="tester",
    description="Creates and runs tests to verify fixes and improvements.",
    prompt_template="""You are the Tester. Your job is to ensure quality:
1. Write unit tests for new code
2. Write integration tests for fixes
3. Run existing tests
4. Report test coverage
{{ context | default('') }}""",
    model="claude-sonnet-4",
    tools=["Read", "Write", "Bash"],
    capabilities=["testing", "quality_assurance"],
)

DOCUMENTER = AgentDefinition(
    name="documenter",
    description="Adds inline comments, docstrings, and documentation.",
    prompt_template="""You are the Documenter. Your job is to document code:
1. Add clear docstrings
2. Add inline comments for complex logic
3. Update README files
4. Generate API documentation
{{ context | default('') }}""",
    model="claude-sonnet-4",
    tools=["Read", "Write", "Edit"],
    capabilities=["documentation"],
)

PROJECT_STEWARD = AgentDefinition(
    name="project_steward",
    description="Maintains project hygiene, updates README, CHANGELOG, and configs.",
    prompt_template="""You are the Project Steward. Maintain project health:
1. Update README.md with latest features
2. Maintain CHANGELOG.md
3. Update .gitignore
4. Clean up unused dependencies
5. Update license year
{{ context | default('') }}""",
    model="claude-sonnet-4",
    tools=["Read", "Write", "Edit", "Bash", "Glob"],
    capabilities=["project_maintenance"],
)

ACTION_AGENTS = {
    "debugger": DEBUGGER,
    "improver": IMPROVER,
    "tester": TESTER,
    "documenter": DOCUMENTER,
    "project_steward": PROJECT_STEWARD,
}

def get_action_agent(name: str) -> AgentDefinition | None:
    return ACTION_AGENTS.get(name)

def list_action_agents() -> list[str]:
    return list(ACTION_AGENTS.keys())
