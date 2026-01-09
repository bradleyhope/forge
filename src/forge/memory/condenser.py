"""Condenser for context window management"""
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CondenserState:
    messages: list[Message] = field(default_factory=list)
    total_tokens: int = 0

class Condenser:
    """Manages context window by condensing old messages."""
    
    def __init__(self, max_tokens: int = 100_000):
        self.max_tokens = max_tokens
        self._state = CondenserState()
    
    def add_message(self, role: str, content: str, metadata: dict | None = None):
        msg = Message(role=role, content=content, metadata=metadata or {})
        self._state.messages.append(msg)
        self._state.total_tokens += len(content) // 4  # Rough estimate
        self._maybe_condense()
    
    def _maybe_condense(self):
        if self._state.total_tokens > self.max_tokens * 0.9:
            # Keep last 50% of messages
            keep = len(self._state.messages) // 2
            self._state.messages = self._state.messages[-keep:]
            self._state.total_tokens = sum(len(m.content) // 4 for m in self._state.messages)
            logger.info(f"Condensed context to {len(self._state.messages)} messages")
    
    def get_messages(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self._state.messages]
