"""
Persistent emotional state — Sprint 6.

Aletheia carries a continuous valence/arousal state that:
  - Persists between sessions (JSON in PALACE/emotional_state.json)
  - Updates gradually via exponential moving average (no abrupt jumps)
  - Is influenced by pipeline quality, guardian decisions, and session length
  - Shapes briefing tone and response style

State file is excluded from git via PALACE/ gitignore entry.
"""

import json
from datetime import datetime
from pathlib import Path

from core.memory.emotional_tagger import EmotionTag

_STATE_PATH = Path("PALACE/emotional_state.json")
_ALPHA = 0.12        # learning rate — how fast new events shift the state
_DECAY = 0.005       # per-session drift toward neutral (prevents extremes)

_DEFAULT = {"valence": 0.0, "arousal": 0.3, "event_count": 0, "updated_at": ""}


# ── persistence ────────────────────────────────────────────────────────────

def _load() -> dict:
    if _STATE_PATH.exists():
        try:
            return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(_DEFAULT)


def _save(state: dict) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")
    _STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


# ── label helper ───────────────────────────────────────────────────────────

def _label(valence: float, arousal: float) -> str:
    if valence > 0.25 and arousal > 0.5:
        return "positivo_activo"
    if valence > 0.25:
        return "positivo_tranquilo"
    if valence < -0.25 and arousal > 0.5:
        return "negativo_tenso"
    if valence < -0.25:
        return "negativo_tranquilo"
    if arousal > 0.5:
        return "neutro_activo"
    return "neutro"


# ── public API ─────────────────────────────────────────────────────────────

def get() -> EmotionTag:
    """Return current emotional state as an EmotionTag."""
    s = _load()
    v = float(s.get("valence", 0.0))
    a = float(s.get("arousal", 0.3))
    return EmotionTag(valence=round(v, 3), arousal=round(a, 3), label=_label(v, a))


def update_from_result(result: dict) -> EmotionTag:
    """
    Update state based on a pipeline result dict.
    Called after every process_request() in the voice session.
    """
    s = _load()
    v = float(s.get("valence", 0.0))
    a = float(s.get("arousal", 0.3))

    dqs        = float(result.get("dqs", 0.5))
    confidence = float(result.get("confidence", 0.5))
    blocked    = bool(result.get("guardian_block", False))

    # Compute event signals
    if blocked:
        ev, ea = -0.4, 0.7     # guardian blocked → tension
    elif dqs > 0.7:
        ev, ea = +0.3, 0.4     # high quality decision → positive energy
    elif dqs < 0.35:
        ev, ea = -0.2, 0.2     # poor decision → mild negative
    else:
        ev = (confidence - 0.5) * 0.4   # neutral territory, confidence-driven
        ea = 0.3

    # Exponential moving average
    v = (1 - _ALPHA) * v + _ALPHA * ev
    a = (1 - _ALPHA) * a + _ALPHA * ea

    # Clamp
    v = max(-1.0, min(1.0, v))
    a = max(0.0,  min(1.0, a))

    s["valence"]     = round(v, 4)
    s["arousal"]     = round(a, 4)
    s["event_count"] = int(s.get("event_count", 0)) + 1
    _save(s)

    return EmotionTag(valence=round(v, 3), arousal=round(a, 3), label=_label(v, a))


def update_from_session(turn_count: int) -> None:
    """
    Called at session end. Long sessions nudge valence slightly positive
    (engagement is inherently rewarding). Applies mild decay toward neutral.
    """
    s = _load()
    v = float(s.get("valence", 0.0))
    a = float(s.get("arousal", 0.3))

    if turn_count >= 5:
        v = (1 - _ALPHA) * v + _ALPHA * 0.2   # engagement reward

    # Decay toward neutral arousal over time
    a = a * (1 - _DECAY * turn_count)
    a = max(0.1, a)

    s["valence"] = round(max(-1.0, min(1.0, v)), 4)
    s["arousal"] = round(a, 4)
    _save(s)


def note_pattern_detected() -> None:
    """Pattern detection (Sprint 5) is a mild positive signal."""
    s = _load()
    v = float(s.get("valence", 0.0))
    v = (1 - _ALPHA * 0.5) * v + (_ALPHA * 0.5) * 0.15
    s["valence"] = round(max(-1.0, min(1.0, v)), 4)
    _save(s)


def summary() -> str:
    """One-line human-readable state summary for briefings."""
    state = get()
    phrases = {
        "positivo_activo":    "Me siento con energia y optimista.",
        "positivo_tranquilo": "Estoy en un estado reflexivo y positivo.",
        "negativo_tenso":     "Noto cierta tension en mi estado actual.",
        "negativo_tranquilo": "Estoy algo cauto hoy.",
        "neutro_activo":      "Estoy alerta y preparado.",
        "neutro":             "",
    }
    return phrases.get(state.label, "")
