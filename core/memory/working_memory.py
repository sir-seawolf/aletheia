"""
Working memory — short-term intra-session context.

Accumulates the last N conversation turns (question + response + emotion).
Injected into LLM prompts so Aletheia has continuity within a session.
Cleared when the session ends.

Usage:
    from core.memory.working_memory import session as wm
    wm.add(question, response, emotion_label)
    wm.to_context_str()   # for prompt injection
    wm.clear()            # at session end
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Turn:
    question: str
    response: str
    emotion_label: str = "neutro"
    ts: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class WorkingMemory:
    def __init__(self, max_turns: int = 8):
        self._turns: list[Turn] = []
        self.max_turns = max_turns

    def add(self, question: str, response: str, emotion_label: str = "neutro") -> None:
        self._turns.append(Turn(
            question=question[:300],
            response=response[:300],
            emotion_label=emotion_label,
        ))
        if len(self._turns) > self.max_turns:
            self._turns.pop(0)

    def to_context_str(self, last_n: int = 4) -> str:
        """Compact string for LLM prompt injection."""
        recent = self._turns[-last_n:]
        if not recent:
            return ""
        lines = ["[Contexto de esta sesion]"]
        for t in recent:
            emotion = f" ({t.emotion_label})" if t.emotion_label != "neutro" else ""
            lines.append(f"  U: {t.question}{emotion}")
            lines.append(f"  A: {t.response[:150]}")
        return "\n".join(lines)

    def last_emotion(self) -> Optional[str]:
        return self._turns[-1].emotion_label if self._turns else None

    def last_question(self) -> Optional[str]:
        return self._turns[-1].question if self._turns else None

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)


# Global instance — one per Python process / voice session
session = WorkingMemory()
