"""
Chat session manager — multi-turn conversation with context window.

Each browser session keeps a rolling message history that is injected
into the LLM prompt so the model can reference previous turns.
History is kept in memory (per-process); it clears on server restart.
"""

from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal

_MAX_TURNS = 20        # turns kept in context window
_MAX_CHARS = 6_000     # max chars of history injected into prompt

# role: "user" | "assistant"
@dataclass
class Turn:
    role: Literal["user", "assistant"]
    content: str
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str | None = None   # e.g. "gmail_scan", "drive_search"


class ChatSession:
    def __init__(self, session_id: str, domain: str = "general"):
        self.session_id = session_id
        self.domain     = domain
        self.history: deque[Turn] = deque(maxlen=_MAX_TURNS)

    def add(self, role: str, content: str, action: str | None = None) -> None:
        self.history.append(Turn(role=role, content=content, action=action))

    def context_prompt(self) -> str:
        """Format recent history as a prompt prefix."""
        lines: list[str] = []
        chars = 0
        for turn in reversed(self.history):
            snippet = f"{turn.role.upper()}: {turn.content}"
            if chars + len(snippet) > _MAX_CHARS:
                break
            lines.insert(0, snippet)
            chars += len(snippet)
        return "\n".join(lines)

    def to_list(self) -> list[dict]:
        return [asdict(t) for t in self.history]

    def clear(self) -> None:
        self.history.clear()


# ── Process-level session store ────────────────────────────────────────────

_sessions: dict[str, ChatSession] = {}


def get_or_create(session_id: str, domain: str = "general") -> ChatSession:
    if session_id not in _sessions:
        _sessions[session_id] = ChatSession(session_id, domain)
    return _sessions[session_id]


def get(session_id: str) -> ChatSession | None:
    return _sessions.get(session_id)


def clear(session_id: str) -> None:
    if session_id in _sessions:
        _sessions[session_id].clear()
