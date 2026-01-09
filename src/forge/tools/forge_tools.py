"""Custom Forge Tools for the Claude Agent SDK - SECURITY HARDENED"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Security: Define allowed base directories
ALLOWED_BASE_DIRS = [
    Path.home(),
    Path("/tmp"),
]

# Security: Dangerous patterns to block
DANGEROUS_PATTERNS = [
    r"\.\./",  # Path traversal
    r"~",      # Home expansion
    r"\$",     # Variable expansion
    r"`",      # Command substitution
    r"\|",     # Pipe
    r";",      # Command chaining
    r"&&",     # Command chaining
    r"\|\|",   # Command chaining
]


def validate_path(path_str: str, base_dir: Path | None = None) -> Path:
    """Validate and sanitize a path to prevent directory traversal attacks."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, path_str):
            raise ValueError(f"Invalid path: contains dangerous pattern")
    
    if base_dir:
        path = (base_dir / path_str).resolve()
    else:
        path = Path(path_str).resolve()
    
    is_allowed = any(
        str(path).startswith(str(allowed.resolve()))
        for allowed in ALLOWED_BASE_DIRS
    )
    
    if not is_allowed:
        raise ValueError(f"Access denied: path outside allowed directories")
    
    return path


def sanitize_for_logging(data: Any, max_length: int = 200) -> str:
    """Sanitize data for safe logging."""
    text = str(data)
    text = re.sub(r'(api[_-]?key|password|secret|token)["\']?\s*[:=]\s*["\']?[\w-]+', 
                  r'\1=***MASKED***', text, flags=re.IGNORECASE)
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text


try:
    from claude_agent_sdk import tool
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    def tool(name: str, description: str, schema: dict):
        def decorator(func):
            func._tool_name = name
            func._tool_description = description
            func._tool_schema = schema
            return func
        return decorator


@tool("analyze_project", "Analyze a project directory", {"path": str})
async def analyze_project(args: dict[str, Any]) -> dict:
    """Analyze a project directory with security validation."""
    try:
        path = validate_path(args.get("path", "."))
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}]}
    
    if not path.exists() or not path.is_dir():
        return {"content": [{"type": "text", "text": "Error: Invalid directory"}]}
    
    structure = {"root": str(path), "files": [], "directories": [], "languages": {}}
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    language_extensions = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".go": "Go"}
    
    file_count = 0
    max_files = 500
    
    try:
        for item in path.rglob("*"):
            if file_count >= max_files:
                break
            if any(ignored in item.parts for ignored in ignore_dirs):
                continue
            try:
                rel_path = str(item.relative_to(path))
                if item.is_file():
                    structure["files"].append(rel_path)
                    file_count += 1
                    ext = item.suffix.lower()
                    if ext in language_extensions:
                        lang = language_extensions[ext]
                        structure["languages"][lang] = structure["languages"].get(lang, 0) + 1
                elif item.is_dir():
                    structure["directories"].append(rel_path)
            except ValueError:
                continue
    except PermissionError:
        pass
    
    structure["files"] = structure["files"][:100]
    structure["directories"] = structure["directories"][:50]
    return {"content": [{"type": "text", "text": json.dumps(structure, indent=2)}]}


@tool("search_code", "Search for a pattern in code files", {"query": str, "path": str})
async def search_code(args: dict[str, Any]) -> dict:
    """Search for a pattern in code files with security validation."""
    query = args.get("query", "")
    if not query or len(query) < 2 or len(query) > 200:
        return {"content": [{"type": "text", "text": "Error: Invalid query length"}]}
    
    try:
        path = validate_path(args.get("path", "."))
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}]}
    
    extensions = [".py", ".js", ".ts", ".tsx", ".jsx"]
    results = []
    ignore_dirs = {".git", "node_modules", "__pycache__", ".venv"}
    max_results = 50
    max_file_size = 1024 * 1024
    
    for ext in extensions:
        if len(results) >= max_results:
            break
        for file_path in path.rglob(f"*{ext}"):
            if len(results) >= max_results:
                break
            if any(ignored in file_path.parts for ignored in ignore_dirs):
                continue
            try:
                if file_path.stat().st_size > max_file_size:
                    continue
                content = file_path.read_text(errors='ignore')
                for i, line in enumerate(content.splitlines(), 1):
                    if query.lower() in line.lower():
                        results.append({"file": str(file_path.relative_to(path)), "line": i, "content": line.strip()[:200]})
                        if len(results) >= max_results:
                            break
            except (PermissionError, OSError):
                continue
    
    return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}


@tool("get_file_info", "Get file information", {"path": str})
async def get_file_info(args: dict[str, Any]) -> dict:
    """Get file information with security validation."""
    try:
        path = validate_path(args.get("path", ""))
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}]}
    
    if not path.exists():
        return {"content": [{"type": "text", "text": "Error: File does not exist"}]}
    
    try:
        stat = path.stat()
    except PermissionError:
        return {"content": [{"type": "text", "text": "Error: Permission denied"}]}
    
    info = {"path": str(path), "name": path.name, "extension": path.suffix, "size_bytes": stat.st_size, "is_file": path.is_file()}
    
    allowed_extensions = {".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml"}
    if path.is_file() and path.suffix in allowed_extensions and stat.st_size <= 100 * 1024:
        try:
            content = path.read_text(errors='ignore')
            info["preview"] = content[:1000]
            info["line_count"] = len(content.splitlines())
        except (PermissionError, OSError):
            info["preview_error"] = "Could not read file"
    
    return {"content": [{"type": "text", "text": json.dumps(info, indent=2)}]}


@tool("run_tests", "Run tests in a project", {"path": str, "framework": str})
async def run_tests(args: dict[str, Any]) -> dict:
    """Run tests with security validation."""
    import subprocess
    
    try:
        path = validate_path(args.get("path", "."))
    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}]}
    
    if not path.is_dir():
        return {"content": [{"type": "text", "text": "Error: Not a directory"}]}
    
    framework = args.get("framework", "auto")
    if framework not in {"auto", "pytest", "npm", "jest"}:
        framework = "auto"
    
    if framework == "auto":
        framework = "pytest" if (path / "pyproject.toml").exists() else "npm" if (path / "package.json").exists() else "pytest"
    
    commands = {"pytest": ["python", "-m", "pytest", "-v", "--tb=short", "-x"], "npm": ["npm", "test"], "jest": ["npx", "jest"]}
    cmd = commands.get(framework, commands["pytest"])
    
    try:
        result = subprocess.run(cmd, cwd=str(path), capture_output=True, text=True, timeout=120, env={**os.environ, "CI": "true"})
        output = {"success": result.returncode == 0, "framework": framework, "stdout": result.stdout[-5000:], "stderr": result.stderr[-2000:], "return_code": result.returncode}
    except subprocess.TimeoutExpired:
        output = {"success": False, "error": "Tests timed out"}
    except Exception as e:
        output = {"success": False, "error": sanitize_for_logging(str(e))}
    
    return {"content": [{"type": "text", "text": json.dumps(output, indent=2)}]}


TOOL_METADATA = [
    {"name": "analyze_project", "description": "Analyze a project directory"},
    {"name": "search_code", "description": "Search for a pattern in code files"},
    {"name": "get_file_info", "description": "Get file information"},
    {"name": "run_tests", "description": "Run tests in a project"},
]

FORGE_TOOLS = [analyze_project, search_code, get_file_info, run_tests]

def get_forge_tools() -> list:
    return FORGE_TOOLS

def list_forge_tools() -> list[dict]:
    return TOOL_METADATA
