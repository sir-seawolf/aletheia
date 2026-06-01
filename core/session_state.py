"""
SessionStateRegistry — per-session CognitiveState manager.

Each session_id gets its own CognitiveState. The registry is in-process memory.
Use get_state(session_id) throughout the pipeline to read/write cognitive state.
"""

from __future__ import annotations

import threading
from typing import Dict

from core.cognitive_state import CognitiveState

_lock = threading.Lock()
_registry: Dict[str, CognitiveState] = {}

# Global fallback state for code paths with no explicit session_id
_global_state = CognitiveState()


def get_state(session_id: str = "local") -> CognitiveState:
    if session_id in ("local", "", None):
        return _global_state
    with _lock:
        if session_id not in _registry:
            _registry[session_id] = CognitiveState()
        return _registry[session_id]


def reset_state(session_id: str = "local") -> CognitiveState:
    with _lock:
        state = CognitiveState()
        if session_id in ("local", "", None):
            global _global_state
            _global_state = state
        else:
            _registry[session_id] = state
        return state


def set_voice_mode(session_id: str) -> None:
    """Apply voice-session defaults: tight latency, smaller budget."""
    state = get_state(session_id)
    state.latency_tolerance = 0.2
    state.token_budget = 3_000


def active_sessions() -> Dict[str, dict]:
    with _lock:
        out = {sid: s.snapshot() for sid, s in _registry.items()}
    out["local"] = _global_state.snapshot()
    return out
