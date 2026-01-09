"""Memory Manager for long-term memory"""
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from forge.config.settings import MemoryConfig

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    id: str
    content: str
    importance: float = 0.5
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    persist: bool = False

class MemoryManager:
    """Manages short-term and long-term memory."""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.short_term: list[MemoryEntry] = []
        self.long_term: list[MemoryEntry] = []
        self._load_persisted()
    
    def _load_persisted(self):
        persist_file = self.config.persist_dir / "memory.json"
        if persist_file.exists():
            try:
                data = json.loads(persist_file.read_text())
                self.long_term = [MemoryEntry(**e) for e in data]
            except Exception as e:
                logger.warning(f"Failed to load memory: {e}")
    
    def _save_persisted(self):
        self.config.persist_dir.mkdir(parents=True, exist_ok=True)
        persist_file = self.config.persist_dir / "memory.json"
        data = [{"id": e.id, "content": e.content, "importance": e.importance, "timestamp": e.timestamp, "metadata": e.metadata, "persist": e.persist} for e in self.long_term]
        persist_file.write_text(json.dumps(data, indent=2))
    
    def add(self, content: str, importance: float = 0.5, persist: bool = False, metadata: dict | None = None) -> MemoryEntry:
        entry = MemoryEntry(id=f"mem_{time.time()}", content=content, importance=importance, persist=persist, metadata=metadata or {})
        if persist:
            self.long_term.append(entry)
            self._save_persisted()
        else:
            self.short_term.append(entry)
        return entry
    
    def recall(self, query: str, limit: int = 10) -> list[MemoryEntry]:
        all_entries = self.short_term + self.long_term
        # Simple keyword matching for now
        matches = [e for e in all_entries if query.lower() in e.content.lower()]
        return sorted(matches, key=lambda x: x.importance, reverse=True)[:limit]
