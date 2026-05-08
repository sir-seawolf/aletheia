"""
Emotional tagger — assigns valence and arousal to any text.

Uses a bilingual keyword dictionary (Spanish + English).
No ML dependencies — fast, offline, deterministic.

Output: EmotionTag(valence[-1,1], arousal[0,1], label)
"""

import re
from typing import NamedTuple


class EmotionTag(NamedTuple):
    valence: float   # -1 very negative → +1 very positive
    arousal: float   # 0 calm → 1 excited / urgent
    label: str       # human-readable composite label


_POSITIVE = {
    "bien", "exito", "excelente", "perfecto", "logro", "aprobado", "correcto",
    "funciona", "resuelto", "completado", "avance", "progreso", "conseguido",
    "bueno", "genial", "fantastico", "satisfecho", "feliz", "contento",
    "mejora", "mejorando", "positivo", "favorable", "ganamos", "logramos",
    "good", "success", "excellent", "perfect", "achievement", "correct",
    "works", "solved", "completed", "progress", "happy", "great", "done",
}

_NEGATIVE = {
    "error", "fallo", "problema", "mal", "roto", "critico", "bloqueo",
    "rechazado", "imposible", "fallido", "incorrecto", "negativo",
    "preocupa", "preocupacion", "frustrado", "frustracion", "perdemos",
    "peor", "empeorando", "adverso", "grave", "serio", "difícil",
    "fail", "failure", "problem", "broken", "blocked", "rejected",
    "incorrect", "wrong", "bad", "worried", "frustrated", "issue",
}

_HIGH_AROUSAL = {
    "urgente", "critico", "inmediato", "emergencia", "alerta", "ahora",
    "rapido", "importante", "necesito", "debo", "emocionante", "increible",
    "alucinante", "impresionante", "wow", "asombroso",
    "urgent", "critical", "immediate", "emergency", "alert", "fast",
    "important", "must", "need", "exciting", "amazing", "asap",
}

_LOW_AROUSAL = {
    "tranquilo", "lento", "estable", "calma", "gradual", "pausado",
    "reflexion", "contemplando", "pensando", "analizando", "considerando",
    "calm", "slow", "stable", "gradual", "relaxed", "steady", "reflecting",
}


def _hits(words: set[str], keyword_set: set[str]) -> int:
    return len(words & keyword_set)


def tag(text: str) -> EmotionTag:
    """Tag text with valence and arousal scores."""
    words = set(re.findall(r"\b\w+\b", text.lower()))

    pos = _hits(words, _POSITIVE)
    neg = _hits(words, _NEGATIVE)
    hi  = _hits(words, _HIGH_AROUSAL)
    lo  = _hits(words, _LOW_AROUSAL)

    valence = round((pos - neg) / max(pos + neg, 1), 2)
    arousal = round(hi / max(hi + lo, 1), 2)

    if valence > 0.3 and arousal > 0.5:
        label = "positivo_activo"
    elif valence > 0.3:
        label = "positivo_tranquilo"
    elif valence < -0.3 and arousal > 0.5:
        label = "negativo_tenso"
    elif valence < -0.3:
        label = "negativo_tranquilo"
    elif arousal > 0.5:
        label = "neutro_activo"
    else:
        label = "neutro"

    return EmotionTag(valence=valence, arousal=arousal, label=label)
