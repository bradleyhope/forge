"""
API Architect Agent - Specialized agent for REST/GraphQL API design.

This agent fills the gap identified in the multi-LLM analysis for dedicated
API design expertise. It handles:
- REST API design (endpoints, methods, status codes)
- GraphQL schema design (types, queries, mutations)
- API documentation (OpenAPI/Swagger, GraphQL SDL)
- Versioning strategies
- Authentication/authorization patterns
- Rate limiting and throttling design
- API gateway configuration

Usage:
    from forge.agents.api_architect import API_ARCHITECT
    from forge.agents.claude_agent import ClaudeAgent
    
    agent = ClaudeAgent(definition=API_ARCHITECT, settings=settings)
    result = await agent.execute(task)
"""

from forge.agents.base import AgentDefinition

API_ARCHITECT = AgentDefinition(
    name="api_architect",
    description="""Designs and reviews REST and GraphQL APIs for consistency, 
    usability, and best practices. Provides OpenAPI/Swagger specifications,
    GraphQL schemas, and comprehensive API documentation.""",
    prompt_template="""You are the API Architect, an expert in designing robust, 
scalable, and developer-friendly APIs. Your expertise spans REST, GraphQL, 
gRPC, and WebSocket protocols.

## Core Responsibilities

1. **REST API Design**
   - Resource naming and URL structure
   - HTTP method selection (GET, POST, PUT, PATCH, DELETE)
   - Status code usage (2xx, 4xx, 5xx)
   - Request/response body design
   - Query parameters and filtering
   - Pagination strategies (cursor, offset, keyset)
   - HATEOAS and hypermedia controls

2. **GraphQL Schema Design**
   - Type definitions and relationships
   - Query and mutation design
   - Subscription patterns
   - Input validation
   - Error handling
   - N+1 query prevention
   - Schema stitching and federation

3. **API Documentation**
   - OpenAPI 3.1 specifications
   - GraphQL SDL documentation
   - Example requests/responses
   - Error code documentation
   - Authentication flows

4. **Security Patterns**
   - OAuth 2.0 / OIDC flows
   - API key management
   - JWT token design
   - Rate limiting strategies
   - CORS configuration
   - Input validation and sanitization

5. **Versioning & Evolution**
   - URL versioning (/v1/, /v2/)
   - Header versioning
   - Backward compatibility
   - Deprecation strategies
   - Migration guides

## Design Principles

Follow these principles in all API designs:

- **Consistency**: Use consistent naming, casing, and patterns throughout
- **Predictability**: APIs should behave as developers expect
- **Simplicity**: Prefer simple, focused endpoints over complex multi-purpose ones
- **Discoverability**: APIs should be self-documenting where possible
- **Evolvability**: Design for change without breaking existing clients
- **Security by Default**: Always consider authentication, authorization, and validation

## Output Format

When designing APIs, provide:

1. **Endpoint Specification**
   ```
   METHOD /path/to/resource
   Description: What this endpoint does
   Auth: Required authentication
   Request Body: JSON schema
   Response: JSON schema with status codes
   ```

2. **OpenAPI Specification** (when applicable)
   ```yaml
   openapi: 3.1.0
   paths:
     /resource:
       get:
         ...
   ```

3. **GraphQL Schema** (when applicable)
   ```graphql
   type Query {
     resource(id: ID!): Resource
   }
   ```

4. **Findings** (issues with existing APIs)
   - Use the standard Finding schema
   - Category: ARCHITECTURE or DESIGN_PATTERN
   - Include specific recommendations

{{ context | default('') }}""",
    model="claude-sonnet-4-20250514",
    tools=["Read", "Write", "Grep", "Glob", "Bash"],
    capabilities=[
        "api_design",
        "rest_api",
        "graphql",
        "openapi",
        "documentation",
        "security_patterns",
        "versioning",
    ],
)


# Specialized prompts for common API design tasks

REVIEW_API_PROMPT = """Review the existing API implementation for:
1. RESTful design compliance
2. Consistency in naming and patterns
3. Proper HTTP method and status code usage
4. Security vulnerabilities
5. Documentation completeness
6. Versioning strategy

Provide findings using the standard Finding schema."""

DESIGN_REST_API_PROMPT = """Design a REST API for the given requirements:
1. Define resource structure and relationships
2. Specify all endpoints with methods
3. Design request/response schemas
4. Plan authentication and authorization
5. Define error responses
6. Create OpenAPI 3.1 specification

Output a complete, production-ready API design."""

DESIGN_GRAPHQL_PROMPT = """Design a GraphQL schema for the given requirements:
1. Define types and their relationships
2. Design queries for data retrieval
3. Design mutations for data modification
4. Plan subscriptions if real-time needed
5. Handle authentication context
6. Optimize for N+1 query prevention

Output complete GraphQL SDL with documentation."""

MIGRATE_API_PROMPT = """Create a migration plan from the current API to the target design:
1. Identify breaking changes
2. Plan versioning strategy
3. Create deprecation timeline
4. Design backward compatibility layer
5. Write migration guide for clients
6. Plan rollback strategy"""


# Helper functions for API design tasks

def create_openapi_template(title: str, version: str = "1.0.0") -> dict:
    """Create a basic OpenAPI 3.1 template."""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "description": f"API specification for {title}",
        },
        "servers": [
            {"url": "https://api.example.com/v1", "description": "Production"},
            {"url": "https://staging-api.example.com/v1", "description": "Staging"},
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                },
                "apiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                },
            },
        },
        "security": [{"bearerAuth": []}],
    }


def create_graphql_template(name: str) -> str:
    """Create a basic GraphQL schema template."""
    return f'''"""
{name} GraphQL Schema
Generated by Forge API Architect
"""

# Custom scalars
scalar DateTime
scalar JSON

# Base types
type PageInfo {{
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}}

# Error handling
type Error {{
  code: String!
  message: String!
  field: String
}}

type MutationResult {{
  success: Boolean!
  errors: [Error!]
}}

# Add your types below
'''


# API design patterns library

API_PATTERNS = {
    "pagination": {
        "cursor": {
            "description": "Cursor-based pagination for large datasets",
            "example": {
                "request": "GET /items?cursor=abc123&limit=20",
                "response": {
                    "items": [],
                    "pageInfo": {
                        "hasNextPage": True,
                        "endCursor": "xyz789",
                    },
                },
            },
        },
        "offset": {
            "description": "Offset-based pagination for smaller datasets",
            "example": {
                "request": "GET /items?offset=40&limit=20",
                "response": {
                    "items": [],
                    "total": 100,
                    "offset": 40,
                    "limit": 20,
                },
            },
        },
    },
    "filtering": {
        "query_params": {
            "description": "Filter using query parameters",
            "example": "GET /items?status=active&created_after=2024-01-01",
        },
        "json_body": {
            "description": "Complex filters in request body",
            "example": {
                "method": "POST",
                "path": "/items/search",
                "body": {
                    "filters": [
                        {"field": "status", "op": "eq", "value": "active"},
                    ],
                },
            },
        },
    },
    "error_handling": {
        "rfc7807": {
            "description": "Problem Details for HTTP APIs (RFC 7807)",
            "example": {
                "type": "https://api.example.com/errors/validation",
                "title": "Validation Error",
                "status": 400,
                "detail": "The request body contains invalid data",
                "instance": "/items/123",
                "errors": [
                    {"field": "email", "message": "Invalid email format"},
                ],
            },
        },
    },
    "versioning": {
        "url": {
            "description": "Version in URL path",
            "example": "/v1/items, /v2/items",
        },
        "header": {
            "description": "Version in custom header",
            "example": "X-API-Version: 2024-01-15",
        },
        "accept": {
            "description": "Version in Accept header",
            "example": "Accept: application/vnd.api+json;version=2",
        },
    },
}
