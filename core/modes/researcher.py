"""
RESEARCHER mode — web/document research, validation, retrieval augmentation.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult


class ResearcherMode(CognitiveMode):
    mode_id      = ModeID.RESEARCHER
    fatigue_cost = 0.07
    min_energy   = 0.15

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")

        sources: List[Dict[str, Any]] = []
        rag_results: List[str] = []

        # 1. Web search (DuckDuckGo, no API key required)
        try:
            from core.docs.web_search import search as web_search
            hits = web_search(question)
            sources = hits[:5] if hits else []
        except Exception:
            pass

        # 2. RAG retrieval
        try:
            from core.docs.rag import query as rag_query
            rag_results = rag_query(question, n_results=3)
        except Exception:
            pass

        combined = _format_sources(sources, rag_results)

        prompt = (
            f"Eres el modo INVESTIGADOR de Aletheia. Analiza la siguiente información "
            f"y responde a la pregunta con los datos encontrados.\n\n"
            f"Pregunta: {question}\n\n"
            f"Fuentes:\n{combined}\n\n"
            "Sintetiza la información. Cita fuentes cuando sea relevante."
        )

        response = self._llm(
            task="research",
            prompt=prompt,
            context={"domain": domain, "mode": "researcher"},
            temp=0.3,
        )

        return ModeResult(
            mode_id         = ModeID.RESEARCHER,
            output          = {"synthesis": response, "sources": sources, "rag": rag_results},
            confidence      = 0.7,
            tokens_used     = len(prompt.split()) + len(response.split()),
            reasoning_depth = state.preferred_depth,
        )


def _format_sources(web: List[Dict], rag: List[str]) -> str:
    lines = []
    for i, s in enumerate(web, 1):
        title = s.get("title", "Sin título")
        url   = s.get("url", "")
        lines.append(f"[Web {i}] {title} — {url}")
    for i, r in enumerate(rag, 1):
        lines.append(f"[Doc {i}] {str(r)[:200]}")
    return "\n".join(lines) if lines else "(sin fuentes encontradas)"
