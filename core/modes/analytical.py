"""
ANALYTICAL mode — structured logic, debugging, decomposition, fact extraction.

Absorbs agents/explorer logic: memory keyword search, LLM fact extraction (JSON
with regex/text fallback), gap detection, confidence scoring.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

_SYSTEM = (
    "Eres el modo ANALÍTICO de Aletheia. Tu función es razonar con lógica estructurada, "
    "descomponer problemas complejos, detectar inconsistencias y validar hipótesis. "
    "Sé preciso, exhaustivo y sistemático. Evita especulaciones sin base."
)

_EXTRACTION_PROMPT = """\
Eres un analista de decisiones personales. Analiza la siguiente pregunta y extrae los datos clave.

Dominio: {domain}
Pregunta: {question}{memory_section}

Tu tarea:
1. Extrae los hechos concretos que están en la pregunta o en el contexto de memoria.
2. Identifica qué información falta para poder responder con precisión.
3. Estima tu confianza en los datos disponibles (0.0 a 1.0).

Responde SOLO con este JSON (sin markdown, sin texto antes ni después):
{{"facts": ["hecho 1", "hecho 2"], "gaps": ["dato faltante 1"], "confidence": 0.7}}"""


class AnalyticalMode(CognitiveMode):
    mode_id      = ModeID.ANALYTICAL
    fatigue_cost = 0.07
    min_energy   = 0.15

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")
        memory   = context.get("memory", [])
        depth    = state.preferred_depth

        # Step 1 — keyword-based fact extraction from context memory
        facts_kw = _extract_facts_from_memory(memory, domain, question)

        # Step 2 — LLM-based extraction with JSON fallback
        ai = self._try_extract_with_ai(question, domain, facts_kw)
        facts      = ai["facts"]
        gaps       = ai["gaps"]
        confidence = ai["confidence"]

        # Step 3 — full structured analysis with enriched context
        steps     = self._decompose(question) if depth != "minimal" else [question]
        facts_str = "\n".join(f"• {f}" for f in facts) if facts else "(sin datos de memoria)"
        gaps_str  = "\n".join(f"• {g}" for g in gaps)  if gaps  else "(sin vacíos detectados)"

        prompt = (
            f"{_SYSTEM}\n\n"
            f"Dominio: {domain}\n"
            f"Pregunta: {question}\n\n"
            f"Hechos extraídos:\n{facts_str}\n\n"
            f"Vacíos de información:\n{gaps_str}\n\n"
            f"Pasos identificados: {steps}\n"
            f"Profundidad de razonamiento: {depth}. "
            "Responde con análisis estructurado."
        )

        response = self._llm(
            task="analytical",
            prompt=prompt,
            context={"domain": domain, "mode": "analytical"},
            temp=0.2,
        )

        return ModeResult(
            mode_id         = ModeID.ANALYTICAL,
            output          = {
                "analysis":   response,
                "steps":      steps,
                "facts":      facts,
                "gaps":       gaps,
                "confidence": confidence,
            },
            confidence      = confidence,
            tokens_used     = len(prompt.split()) + len(response.split()),
            reasoning_depth = depth,
        )

    def _try_extract_with_ai(
        self,
        question: str,
        domain: str,
        memory_facts: List[str],
    ) -> Dict[str, Any]:
        """LLM fact extraction with JSON → regex → text-lines fallback."""
        memory_section = ""
        if memory_facts:
            lines = "\n".join(f"  - {f}" for f in memory_facts[:5])
            memory_section = f"\n\nContexto de memoria:\n{lines}"

        prompt = _EXTRACTION_PROMPT.format(
            domain=domain,
            question=question,
            memory_section=memory_section,
        )
        try:
            raw = self._llm(
                task="analytical_extract",
                prompt=prompt,
                context={"domain": domain},
                temp=0.2,
            )
            if not raw or raw.startswith("[ERROR]") or raw.startswith("[MOCK]"):
                raise ValueError("bad response")

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(
                    l for l in cleaned.splitlines() if not l.startswith("```")
                ).strip()

            # 1. direct JSON parse
            try:
                data = json.loads(cleaned)
                if isinstance(data, dict):
                    return {
                        "facts":      data.get("facts", memory_facts),
                        "gaps":       data.get("gaps", []),
                        "confidence": float(data.get("confidence", 0.6)),
                    }
            except (ValueError, TypeError):
                pass

            # 2. regex: first {...} block containing "facts"
            m = re.search(r'\{[^{}]*"facts"[^{}]*\}', cleaned, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group())
                    return {
                        "facts":      data.get("facts", memory_facts),
                        "gaps":       data.get("gaps", []),
                        "confidence": float(data.get("confidence", 0.5)),
                    }
                except (ValueError, TypeError):
                    pass

            # 3. free-text: non-empty lines as facts
            lines = [
                l.strip().lstrip("•-*▸1234567890.)").strip()
                for l in cleaned.split("\n")
                if l.strip() and len(l.strip()) > 15
            ]
            return {
                "facts":      lines[:5] or memory_facts,
                "gaps":       ["Respuesta LLM sin estructura JSON — análisis de texto libre"],
                "confidence": 0.5,
            }
        except Exception:
            gaps = _detect_gaps(memory_facts)
            return {
                "facts":      memory_facts,
                "gaps":       gaps,
                "confidence": _calculate_confidence(memory_facts, gaps),
            }

    def _decompose(self, question: str) -> list[str]:
        parts = [s.strip() for s in question.replace("?", ".").split(".") if len(s.strip()) > 10]
        return parts[:5] if parts else [question]


# ── module-level helpers (reusable by other modes) ──────────────────────────

def _extract_facts_from_memory(memory: list, domain: str, question: str) -> List[str]:
    """Keyword-based extraction from a raw memory list (strings, dicts, or objects)."""
    keywords = set(question.lower().split()) | {domain.lower()}
    facts: List[str] = []
    for item in memory:
        if isinstance(item, str):
            text = item
        elif isinstance(item, dict):
            text = str(item.get("content", item))
        else:
            text = str(item)
        if any(kw in text.lower() for kw in keywords):
            facts.append(text[:200])
    return facts[:10]


def _detect_gaps(facts: List[str]) -> List[str]:
    if len(facts) < 2:
        return ["Información insuficiente para análisis completo"]
    return []


def _calculate_confidence(facts: List[str], gaps: List[str]) -> float:
    base = 0.7
    score = base + min(len(facts) * 0.05, 0.2) - min(len(gaps) * 0.1, 0.3)
    return round(max(0.0, min(1.0, score)), 2)
