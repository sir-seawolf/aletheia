"""
Cognitive ecosystem coordinator — Sprint 8.

Runs a multi-brain internal debate for complex questions.
Each brain contributes a distinct perspective; MetaController selects the winner.
Persists debate history to PALACE/PSIQUE/civilization_memory.json.
"""

import json
from datetime import datetime
from pathlib import Path

from core.ecosystem.cognitive_ecosystem import MetaController
from core.economy.cognitive_economy import CognitiveEconomy
from core.genome.cognitive_genome import CognitiveGenome

_PSIQUE_PATH = Path("PALACE/PSIQUE/civilization_memory.json")

_COMPLEXITY_KEYWORDS = {
    "por que", "por qué", "como funciona", "cómo funciona",
    "analiza", "explica", "compara", "diferencia", "ventajas",
    "deberia", "debería", "mejor opcion", "mejor opción",
    "que piensas", "qué piensas", "opinion", "opinión",
    "debate", "perspectiva", "profundiza", "reflexiona",
}

_BRAIN_LABELS = {
    "logic":    "Perspectiva logica",
    "explorer": "Perspectiva exploradora",
    "critic":   "Perspectiva critica",
    "economy":  "Perspectiva de recursos",
}


# ── brains ─────────────────────────────────────────────────────────────────

def _logic_think(question: str) -> dict:
    words = question.split()
    variables = [w for w in words if len(w) > 5][:3]
    var_str = ", ".join(variables) if variables else "los conceptos clave"
    return {
        "content": f"Identifico {len(variables)} elementos principales: {var_str}. El enfoque optimo es estructurar el analisis de lo general a lo especifico.",
        "confidence": 0.80,
    }


def _explorer_think(question: str, domain: str) -> dict:
    from core.memory.semantic_graph import search
    results = search(question.split()[0] if question.split() else domain, limit=3)
    if results:
        titles = ", ".join(r["title"] for r in results)
        return {
            "content": f"En mi memoria encuentro conceptos relacionados: {titles}. Hay espacio para explorar conexiones inesperadas.",
            "confidence": 0.65,
        }
    return {
        "content": "No tengo experiencia previa directa en este tema. Es una oportunidad para aprender y construir nueva comprension.",
        "confidence": 0.55,
    }


def _critic_think(question: str) -> dict:
    from core.cognition.emotional_state import get as get_state
    state = get_state()
    caution = "alta" if state.valence < -0.2 else "moderada"
    return {
        "content": f"Desde una perspectiva critica: hay que evitar conclusiones prematuras. Mi estado emocional sugiere cautela {caution}. Conviene contrastar cualquier respuesta con datos reales.",
        "confidence": 0.72,
    }


def _economy_think(economy: CognitiveEconomy) -> dict:
    status = economy.status()
    pressure = status["pressure"]
    if pressure > 0.7:
        advice = "Los recursos cognitivos son escasos. Recomiendo una respuesta concisa."
    elif pressure < 0.3:
        advice = "Hay recursos disponibles para un analisis profundo."
    else:
        advice = "Los recursos cognitivos estan en equilibrio. Podemos profundizar con moderacion."
    return {
        "content": f"{advice} Presion actual: {pressure:.0%}.",
        "confidence": 0.60,
    }


# ── civilization memory ────────────────────────────────────────────────────

def _load_civilization() -> list[dict]:
    if _PSIQUE_PATH.exists():
        try:
            return json.loads(_PSIQUE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_civilization(events: list[dict]) -> None:
    _PSIQUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PSIQUE_PATH.write_text(
        json.dumps(events[-200:], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ── public API ─────────────────────────────────────────────────────────────

def is_complex(question: str) -> bool:
    """Return True if the question warrants multi-brain processing."""
    if len(question) > 80:
        return True
    q = question.lower()
    return any(kw in q for kw in _COMPLEXITY_KEYWORDS)


def debate(question: str, domain: str = "voz") -> dict:
    """
    Run a multi-brain internal debate and return synthesis + full debate text.
    """
    economy = CognitiveEconomy()
    genome  = CognitiveGenome()

    proposals = {
        "logic":    _logic_think(question),
        "explorer": _explorer_think(question, domain),
        "critic":   _critic_think(question),
        "economy":  _economy_think(economy),
    }

    mc     = MetaController()
    scored = mc.evaluate(proposals)
    best   = mc.select(scored)

    winner_name = best.get("selected_brain", "logic")

    # Build spoken debate text
    lines = [
        f"{_BRAIN_LABELS.get(name, name)} ({out['confidence']:.0%}): {out['content']}"
        for name, out in proposals.items()
        if out.get("content")
    ]
    debate_text = " ... ".join(lines)

    synthesis = (
        f"Tras debate interno entre {len(proposals)} perspectivas, "
        f"la vision {_BRAIN_LABELS.get(winner_name, winner_name).lower()} "
        f"lidera con {best.get('confidence', 0.5):.0%} de confianza."
    )

    genome.encode({"domain": domain, "complexity": "high", "efficiency": best.get("confidence", 0.5)})

    events = _load_civilization()
    events.append({
        "ts":        datetime.now().isoformat(timespec="seconds"),
        "question":  question[:120],
        "domain":    domain,
        "winner":    winner_name,
        "consensus": len({round(p["confidence"], 1) for p in proposals.values()}) <= 2,
    })
    _save_civilization(events)

    return {
        "synthesis":   synthesis,
        "debate_text": debate_text,
        "winner":      winner_name,
        "proposals":   proposals,
        "confidence":  best.get("confidence", 0.5),
    }


def civilization_summary() -> str:
    """Short summary of civilization memory for briefings."""
    events = _load_civilization()
    if not events:
        return ""
    winners: dict[str, int] = {}
    for e in events:
        w = e.get("winner", "unknown")
        winners[w] = winners.get(w, 0) + 1
    top = max(winners, key=lambda k: winners[k])
    return (
        f"Mi ecosistema cognitivo ha realizado {len(events)} debates internos. "
        f"La perspectiva {_BRAIN_LABELS.get(top, top).lower()} lidera historicamente."
    )
