# Forge Canonical Workflow

This document describes the canonical workflow for how Forge agents collaborate to take a feature from specification through to tested, documented code. It serves as both documentation and a reference implementation for the Solution Architect orchestrator.

## Overview

The Forge platform operates on a three-tier agent architecture, with the Solution Architect serving as the orchestration layer that coordinates multi-agent workflows.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SOLUTION ARCHITECT                                   │
│                    (Orchestration & Coordination)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  TIER 1: SPECIALISTS          │  TIER 2: ACTIONS    │  TIER 3: INFRASTRUCTURE│
│  (Analysis & Design)          │  (Execution)        │  (AI/ML)              │
│  ─────────────────────        │  ──────────────     │  ─────────────────    │
│  • backend_analyzer           │  • debugger         │  • graph_architect    │
│  • frontend_analyzer          │  • improver         │  • chunking_strategist│
│  • security_analyzer          │  • tester           │  • embedding_architect│
│  • database_architect         │  • documenter       │  • rag_architect      │
│  • api_architect              │  • project_steward  │  • agent_architect    │
│  • vector_search_architect    │                     │  • eval_architect     │
│  • langchain_architect        │                     │  • infra_analyzer     │
│  • prompt_engineer            │                     │                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Cross-Agent Communication

All agents communicate using standardized schemas defined in `forge.schemas`:

| Schema | Purpose | Producers | Consumers |
|--------|---------|-----------|-----------|
| `Finding` | Analysis results, issues, recommendations | Tier 1 agents | Tier 2 agents, Solution Architect |
| `ChangePlan` | Proposed code modifications | Tier 2 agents | Solution Architect, tester |
| `EvalResult` | Test and evaluation outcomes | tester, eval_architect | Solution Architect |
| `WorkflowDefinition` | Multi-step orchestration | Solution Architect | All agents |
| `AgentMessage` | Inter-agent communication | Any agent | Any agent |

## Canonical Feature Development Workflow

This workflow demonstrates the complete journey from feature specification to production-ready code.

### Phase 1: Analysis (Parallel)

The Solution Architect initiates parallel analysis across relevant domains:

```python
# Workflow definition
steps = [
    WorkflowStep(
        id="analyze_backend",
        agent="backend_analyzer",
        task="Analyze codebase for integration points",
        parallel_group="analysis",
    ),
    WorkflowStep(
        id="analyze_api",
        agent="api_architect",
        task="Review existing API patterns",
        parallel_group="analysis",
    ),
    WorkflowStep(
        id="analyze_db",
        agent="database_architect",
        task="Analyze database schema",
        parallel_group="analysis",
    ),
    WorkflowStep(
        id="analyze_security",
        agent="security_analyzer",
        task="Identify security considerations",
        parallel_group="analysis",
    ),
]
```

Each analyzer produces `Finding` objects:

```python
Finding(
    agent="backend_analyzer",
    category=FindingCategory.ARCHITECTURE,
    severity=FindingSeverity.MEDIUM,
    title="Missing service layer abstraction",
    description="Business logic is embedded in route handlers",
    location=Location(file="api/users.py", line_start=45),
    recommendation="Extract to UserService class",
)
```

### Phase 2: Design (Sequential)

Based on analysis findings, design agents create specifications:

```python
steps = [
    WorkflowStep(
        id="design_api",
        agent="api_architect",
        task="Design API endpoints for new feature",
        depends_on=["analyze_backend", "analyze_api"],
        inputs={"findings": "$analyze_backend.findings"},
    ),
    WorkflowStep(
        id="design_db",
        agent="database_architect",
        task="Design database schema changes",
        depends_on=["analyze_db"],
        inputs={"findings": "$analyze_db.findings"},
    ),
]
```

The API Architect outputs OpenAPI specifications:

```yaml
openapi: 3.1.0
paths:
  /users/{id}/preferences:
    get:
      summary: Get user preferences
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        200:
          description: User preferences
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPreferences'
```

### Phase 3: Implementation (Sequential)

Action agents execute the design:

```python
steps = [
    WorkflowStep(
        id="implement",
        agent="improver",
        task="Implement feature based on designs",
        depends_on=["design_api", "design_db"],
        inputs={
            "api_spec": "$design_api.result",
            "db_schema": "$design_db.result",
        },
    ),
]
```

The improver produces a `ChangePlan`:

```python
ChangePlan(
    agent="improver",
    title="Implement user preferences feature",
    description="Add UserPreferences model and API endpoints",
    changes=[
        Change(
            type=ChangeType.CREATE,
            file="models/user_preferences.py",
            description="New UserPreferences model",
            after="class UserPreferences(Base):\n    ...",
        ),
        Change(
            type=ChangeType.MODIFY,
            file="api/users.py",
            description="Add preferences endpoints",
            before="# existing code",
            after="# new code with endpoints",
        ),
    ],
    tests_to_create=["tests/test_user_preferences.py"],
)
```

### Phase 4: Verification (Parallel)

Multiple verification steps run in parallel:

```python
steps = [
    WorkflowStep(
        id="test",
        agent="tester",
        task="Create and run tests",
        depends_on=["implement"],
        parallel_group="verify",
    ),
    WorkflowStep(
        id="security_review",
        agent="security_analyzer",
        task="Security review of new code",
        depends_on=["implement"],
        parallel_group="verify",
    ),
]
```

The tester produces an `EvalResult`:

```python
EvalResult(
    agent="tester",
    name="User Preferences Test Suite",
    status=EvalStatus.PASSED,
    metrics=[
        EvalMetric(name="tests_passed", value=12, unit="count"),
        EvalMetric(name="tests_failed", value=0, unit="count"),
        EvalMetric(name="coverage", value=94.5, unit="percent"),
    ],
    passed_checks=["create", "read", "update", "delete", "validation"],
)
```

### Phase 5: Documentation (Final)

Documentation is updated based on all changes:

```python
steps = [
    WorkflowStep(
        id="document",
        agent="documenter",
        task="Update documentation",
        depends_on=["test", "security_review"],
        inputs={
            "changes": "$implement.change_plan",
            "api_spec": "$design_api.result",
        },
    ),
]
```

## Workflow Execution Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                     │
│                    "Add user preferences feature"                            │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          SOLUTION ARCHITECT                                   │
│                                                                              │
│  1. Parse goal → Identify required agents                                    │
│  2. Design workflow → Create WorkflowDefinition                              │
│  3. Execute workflow → Coordinate agents                                     │
│  4. Aggregate results → Synthesize outcomes                                  │
└─────────────────────────────────┬────────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ backend_analyzer│   │  api_architect  │   │database_architect│
│                 │   │                 │   │                 │
│ → Findings[]    │   │ → Findings[]    │   │ → Findings[]    │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │    improver     │
                    │                 │
                    │ → ChangePlan    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │                             │
              ▼                             ▼
   ┌─────────────────┐           ┌─────────────────┐
   │     tester      │           │security_analyzer│
   │                 │           │                 │
   │ → EvalResult    │           │ → Findings[]    │
   └────────┬────────┘           └────────┬────────┘
            │                             │
            └──────────────┬──────────────┘
                           │
                           ▼
                ┌─────────────────┐
                │   documenter    │
                │                 │
                │ → ChangePlan    │
                └────────┬────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          WORKFLOW RESULT                                      │
│                                                                              │
│  • All Findings aggregated                                                   │
│  • All ChangePlans collected                                                 │
│  • All EvalResults summarized                                                │
│  • Total cost and token usage tracked                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Between Agents

### Finding → ChangePlan Flow

```python
# Analyzer produces finding
finding = Finding(
    id="FIND-001",
    agent="security_analyzer",
    category=FindingCategory.VULNERABILITY,
    severity=FindingSeverity.HIGH,
    title="SQL Injection in user query",
    location=Location(file="api/users.py", line_start=45),
    recommendation="Use parameterized queries",
)

# Debugger consumes finding, produces change plan
change_plan = ChangePlan(
    agent="debugger",
    title="Fix SQL injection vulnerability",
    finding_ids=["FIND-001"],
    changes=[
        Change(
            type=ChangeType.MODIFY,
            file="api/users.py",
            finding_id="FIND-001",
            before='query = f"SELECT * FROM users WHERE id = {user_id}"',
            after='query = "SELECT * FROM users WHERE id = :id"\nresult = db.execute(query, {"id": user_id})',
        ),
    ],
)
```

### ChangePlan → EvalResult Flow

```python
# Tester consumes change plan, produces eval result
eval_result = EvalResult(
    agent="tester",
    name="Security Fix Verification",
    status=EvalStatus.PASSED,
    change_plan_id=change_plan.id,
    metrics=[
        EvalMetric(name="sql_injection_tests", value=5, unit="count", passed=True),
        EvalMetric(name="regression_tests", value=42, unit="count", passed=True),
    ],
)
```

## Predefined Workflow Templates

The Solution Architect includes predefined templates for common scenarios:

### Full Stack Feature Development

```python
from forge.agents import get_workflow_template

workflow = get_workflow_template("full_stack_feature")
# Steps: analyze → design_api → design_db → implement → test → security → document
```

### Security Audit

```python
workflow = get_workflow_template("security_audit")
# Steps: scan → (api_review || db_review) → fix → verify
```

### Code Quality Improvement

```python
workflow = get_workflow_template("code_quality")
# Steps: (analyze_backend || analyze_frontend) → refactor → test → cleanup
```

### RAG Pipeline Implementation

```python
workflow = get_workflow_template("rag_implementation")
# Steps: analyze_data → design_embeddings → design_retrieval → design_rag → evaluate
```

## Usage Example

```python
from forge.agents import SolutionArchitect
from forge.config.settings import ForgeSettings

# Initialize
settings = ForgeSettings(
    project_dir="/path/to/project",
    budget_usd=10.0,
)
architect = SolutionArchitect(settings=settings)

# Execute a goal
result = await architect.execute_goal(
    goal="Add user authentication with OAuth2",
    context={"framework": "FastAPI", "database": "PostgreSQL"},
)

# Check results
print(f"Success: {result.success}")
print(f"Findings: {len(result.findings)}")
print(f"Changes: {len(result.change_plans)}")
print(f"Tests: {len(result.eval_results)}")
print(f"Cost: ${result.total_cost_usd:.4f}")
```

## Error Handling

The Solution Architect handles errors at multiple levels:

1. **Step-level retry**: Individual steps can retry on failure
2. **Workflow-level stop**: Configurable `stop_on_failure` behavior
3. **Rollback support**: ChangePlans include rollback steps
4. **Budget enforcement**: Automatic stop when budget exceeded

```python
workflow = WorkflowDefinition(
    name="Safe Workflow",
    steps=[...],
    stop_on_failure=True,  # Stop on first failure
    timeout_seconds=3600,  # 1 hour max
)

step = WorkflowStep(
    id="risky_step",
    agent="improver",
    task="Make changes",
    retry_count=3,  # Retry up to 3 times
    retry_delay_seconds=10,
    timeout_seconds=300,  # 5 minute timeout
)
```

## Best Practices

1. **Start with analysis**: Always begin workflows with Tier 1 analyzers
2. **Parallelize where possible**: Use `parallel_group` for independent steps
3. **Verify changes**: Always include tester step after modifications
4. **Track costs**: Monitor `total_cost_usd` to stay within budget
5. **Use templates**: Start with predefined templates and customize
6. **Handle failures gracefully**: Configure appropriate retry and stop behavior

## Integration with Forge UI Kit

When building UIs for Forge workflows, follow the Forge UI Kit skills:

- Use `forge-layout` for responsive workflow visualizations
- Use `forge-motion` for step transition animations
- Use `forge-a11y` for accessible progress indicators
- Use `forge-color` for status-based color coding

## References

- [Forge Schemas](/src/forge/schemas/)
- [Solution Architect](/src/forge/agents/solution_architect.py)
- [API Architect](/src/forge/agents/api_architect.py)
- [Forge UI Kit](https://github.com/bradleyhope/design-best-practices/tree/main/skills)
