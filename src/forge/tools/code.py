"""Code analysis tool"""
import logging
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ProjectStructure:
    root: Path
    files: list[Path] = field(default_factory=list)
    directories: list[Path] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)

class CodeTool:
    LANGUAGE_EXTENSIONS = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React", ".tsx": "React TypeScript", ".go": "Go",
        ".rs": "Rust", ".java": "Java", ".rb": "Ruby",
    }
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
    
    def analyze_structure(self) -> ProjectStructure:
        structure = ProjectStructure(root=self.project_dir)
        ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        
        for path in self.project_dir.rglob("*"):
            if any(ignored in path.parts for ignored in ignore_dirs):
                continue
            if path.is_file():
                structure.files.append(path)
                ext = path.suffix.lower()
                if ext in self.LANGUAGE_EXTENSIONS:
                    lang = self.LANGUAGE_EXTENSIONS[ext]
                    structure.languages[lang] = structure.languages.get(lang, 0) + 1
            elif path.is_dir():
                structure.directories.append(path)
        
        return structure
    
    def find_files(self, pattern: str) -> list[Path]:
        return list(self.project_dir.glob(pattern))
    
    def search_content(self, query: str, extensions: list[str] | None = None) -> list[tuple[Path, int, str]]:
        results = []
        extensions = extensions or [".py", ".js", ".ts", ".tsx", ".jsx"]
        for ext in extensions:
            for file in self.project_dir.rglob(f"*{ext}"):
                try:
                    for i, line in enumerate(file.read_text().splitlines(), 1):
                        if query.lower() in line.lower():
                            results.append((file, i, line.strip()))
                except Exception:
                    pass
        return results
