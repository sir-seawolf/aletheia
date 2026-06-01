"""
Proactive intelligence engine — Sprint 5.

Two capabilities:
  briefing()       — startup summary of recent memory themes
  pattern_check()  — detects repeated focus during a session

Fully offline. Sources: PALACE, working_memory, semantic_graph.
"""

from collections import Counter

from core.palace.reader import read_palace
from core.palace.classifier import AREAS_KEYWORDS
from core.memory.working_memory import WorkingMemory
from core.cognition.emotional_state import get as get_state, summary as state_summary
from core.ecosystem.coordinator import civilization_summary

_AREAS = list(AREAS_KEYWORDS.keys())
_PATTERN_THRESHOLD = 3       # appearances of same word to trigger suggestion
_PATTERN_MIN_TURNS = 3       # min session turns before pattern check fires
_STOP_WORDS = {
    "que", "como", "cual", "cuales", "para", "sobre", "desde", "hasta",
    "tiene", "tienes", "puedes", "puedo", "quiero", "quieres", "sabes",
    "what", "which", "about", "from", "with", "have", "does", "this",
    "that", "there", "where", "when", "would", "could", "should",
    "explicame", "explica", "dime", "cuéntame", "cuentame",
}


# ── PALACE helpers ─────────────────────────────────────────────────────────

def _read_recent_themes(max_per_area: int = 3) -> list[str]:
    """Collect tag strings from the most recent PALACE entries."""
    themes: list[str] = []
    for area in _AREAS:
        entries = read_palace(area)[-max_per_area:]
        for entry in entries:
            tags = entry.get("tags", "")
            if isinstance(tags, str):
                themes.extend(t.strip().lower() for t in tags.split(",") if t.strip())
            elif isinstance(tags, list):
                themes.extend(str(t).lower() for t in tags)
    return [t for t in themes if t and t not in ("unknown", "voz", "voice", "")]


def _palace_total() -> int:
    total = 0
    for area in _AREAS:
        total += len(read_palace(area))
    return total


# ── public API ─────────────────────────────────────────────────────────────

def briefing() -> str:
    """
    Generate a natural-language startup briefing.
    Returns empty string if the PALACE is empty (fresh install).
    """
    themes = _read_recent_themes()
    if not themes:
        return ""

    counter = Counter(themes)
    top = [t for t, _ in counter.most_common(4)]
    total = _palace_total()

    # Build topic string
    if len(top) == 0:
        return ""
    elif len(top) == 1:
        topic_str = top[0]
    elif len(top) == 2:
        topic_str = f"{top[0]} y {top[1]}"
    else:
        topic_str = f"{top[0]}, {top[1]} y {top[2]}"

    parts: list[str] = []

    # Sprint 6 — open with emotional state if non-neutral
    mood = state_summary()
    if mood:
        parts.append(mood)

    if total > 0:
        parts.append(f"Tengo {total} registros en memoria.")
    parts.append(f"Los temas mas frecuentes son {topic_str}.")

    # Sprint 8 — civilization summary if debates exist
    civ = civilization_summary()
    if civ:
        parts.append(civ)

    parts.append("Por donde empezamos?")

    return " ".join(parts)


def pattern_check(wm: WorkingMemory, already_noted: set[str]) -> str | None:
    """
    Scan working memory for a repeated topic focus.
    Returns a proactive suggestion string, or None if no strong pattern.
    `already_noted` tracks topics already surfaced this session to avoid repeating.
    """
    if len(wm) < _PATTERN_MIN_TURNS:
        return None

    # Gather meaningful words from all questions
    words: list[str] = []
    for turn in wm._turns:
        for w in turn.question.lower().split():
            cleaned = w.strip(".,!?¿¡;:()")
            if len(cleaned) > 4 and cleaned not in _STOP_WORDS:
                words.append(cleaned)

    if not words:
        return None

    counter = Counter(words)
    for word, count in counter.most_common(5):
        if count >= _PATTERN_THRESHOLD and word not in already_noted:
            already_noted.add(word)
            return (
                f"Noto que el tema de {word} aparece con frecuencia en esta sesion. "
                f"Quieres que profundice mas en ello?"
            )

    return None
