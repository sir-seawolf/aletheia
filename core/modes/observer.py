"""
OBSERVER mode — orchestration, supervision, routing, and continuity.

The Observer is the entry point for all external requests. It:
- analyses incoming context to decide which mode(s) to activate,
- detects multi-domain requests and proposes ModeBlend when appropriate,
- monitors cognitive state and applies fatigue-based throttling,
- maintains continuity across mode transitions,
- arbitrates conflicts between mode outputs.

Blend detection fires when:
  1. The question matches keywords from ≥2 distinct cognitive domains, AND
  2. CognitiveState has enough energy to afford multi-mode reasoning (energy > 0.5).

Single-mode routing fires in all other cases.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult


# ── Single-mode keyword routing ───────────────────────────────────────────────

_ROUTING_KEYWORDS: Dict[str, ModeID] = {
    # financial / sustainability
    "dinero": ModeID.KRONOS, "gasto": ModeID.KRONOS, "ahorro": ModeID.KRONOS,
    "inversion": ModeID.KRONOS, "deuda": ModeID.KRONOS, "finance": ModeID.KRONOS,
    "sueldo": ModeID.KRONOS, "ingreso": ModeID.KRONOS, "factura": ModeID.KRONOS,
    # analysis / logic
    "debug": ModeID.ANALYTICAL, "error": ModeID.ANALYTICAL, "analiza": ModeID.ANALYTICAL,
    "valida": ModeID.ANALYTICAL, "comprueba": ModeID.ANALYTICAL, "falla": ModeID.ANALYTICAL,
    # strategy / planning
    "plan": ModeID.STRATEGIC, "estrategia": ModeID.STRATEGIC, "prioridad": ModeID.STRATEGIC,
    "objetivo": ModeID.STRATEGIC, "largo plazo": ModeID.STRATEGIC, "meta": ModeID.STRATEGIC,
    # creativity
    "idea": ModeID.CREATIVE, "crea": ModeID.CREATIVE, "imagina": ModeID.CREATIVE,
    "diseña": ModeID.CREATIVE, "inventa": ModeID.CREATIVE, "innovar": ModeID.CREATIVE,
    # reflection
    "contradiccion": ModeID.REFLECTIVE, "patron": ModeID.REFLECTIVE,
    "por qué": ModeID.REFLECTIVE, "reflexiona": ModeID.REFLECTIVE,
    "coherencia": ModeID.REFLECTIVE, "inconsistencia": ModeID.REFLECTIVE,
    # research
    "busca": ModeID.RESEARCHER, "investiga": ModeID.RESEARCHER,
    "buscar": ModeID.RESEARCHER, "web": ModeID.RESEARCHER, "fuente": ModeID.RESEARCHER,
    # execution
    "ejecuta": ModeID.EXECUTIVE, "haz": ModeID.EXECUTIVE, "automatiza": ModeID.EXECUTIVE,
    "corre": ModeID.EXECUTIVE, "accion": ModeID.EXECUTIVE, "hacer": ModeID.EXECUTIVE,
    # memory
    "recuerda": ModeID.MEMORY_CURATOR, "olvida": ModeID.MEMORY_CURATOR,
    "consolida": ModeID.MEMORY_CURATOR,
    # security
    "riesgo": ModeID.GUARDIAN, "seguridad": ModeID.GUARDIAN,
    "permiso": ModeID.GUARDIAN, "peligro": ModeID.GUARDIAN,
    # systems / world model
    "sistema": ModeID.WORLD_MODEL, "consecuencia": ModeID.WORLD_MODEL,
    "impacto": ModeID.WORLD_MODEL, "causa": ModeID.WORLD_MODEL,
}

# ── Blend trigger patterns ────────────────────────────────────────────────────
# Each tuple: (preset_name, trigger_keywords, synthesis_strategy)
# Activated when ≥2 trigger keywords are present.

_BLEND_TRIGGERS: List[Tuple[str, List[str], str]] = [
    ("strategic_analytical",  ["analiza", "plan", "estrategia", "objetivo", "prioridad", "debug"], "sequential"),
    ("reflective_kronos",     ["dinero", "coherencia", "sostenibilidad", "gasto", "patron", "reflexiona"], "weighted_prompt"),
    ("creative_world",        ["idea", "impacto", "futuro", "sistema", "innovar", "consecuencia"], "weighted_prompt"),
    ("analytical_reflective", ["error", "contradiccion", "por qué", "falla", "inconsistencia", "comprueba"], "sequential"),
    ("strategic_creative",    ["plan", "idea", "diseña", "meta", "inventa", "estrategia"], "weighted_prompt"),
    ("kronos_strategic",      ["dinero", "plan", "objetivo", "ahorro", "largo plazo", "meta"], "sequential"),
]

# Minimum energy to activate a blend
_BLEND_MIN_ENERGY = 0.5


class ObserverMode(CognitiveMode):
    mode_id      = ModeID.OBSERVER
    fatigue_cost = 0.01   # always on; minimal cost
    min_energy   = 0.0    # activates even when exhausted

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "").lower()
        domain   = context.get("domain", "general")

        blend  = None
        routed = None
        source = "keyword"

        # Priority 1 — TraceLearner blend recommendation (data-driven)
        if state.energy >= _BLEND_MIN_ENERGY and not state.is_fatigued:
            learned_blend = self._learned_blend(domain, state)
            if learned_blend is not None:
                blend  = learned_blend
                source = "learned_blend"

        # Priority 2 — TraceLearner single-mode recommendation (data-driven)
        if blend is None:
            learned_mode = self._learned_mode(domain, state)
            if learned_mode is not None:
                routed = learned_mode
                source = "learned_mode"

        # Priority 3 — keyword blend detection
        if blend is None and routed is None:
            if state.energy >= _BLEND_MIN_ENERGY and not state.is_fatigued:
                blend = self._detect_blend(question)
                if blend:
                    source = "blend_keyword"

        # Priority 4 — keyword single-mode routing (always-on fallback)
        if blend is None and routed is None:
            routed = self._route(question, state)
            source = "keyword"

        output: Dict[str, Any] = {
            "routed_to":       routed.value if routed else None,
            "blend":           blend.to_dict() if blend else None,
            "routing_source":  source,
            "cognitive_state": state.snapshot(),
            "can_continue":    not state.is_critical,
            "adaptations":     self._adaptations(state),
        }

        return ModeResult(
            mode_id         = ModeID.OBSERVER,
            output          = output,
            confidence      = 0.9,
            tokens_used     = 0,
            reasoning_depth = "minimal",
            next_mode       = routed,
            next_blend      = blend,
        )

    # ── Routing ──────────────────────────────────────────────────────────────

    def _route(self, text: str, state: CognitiveState) -> Optional[ModeID]:
        if state.is_critical:
            return None
        for keyword, mode in _ROUTING_KEYWORDS.items():
            if keyword in text:
                return mode
        return ModeID.ANALYTICAL   # default

    def _detect_blend(self, text: str) -> Optional[Any]:
        """
        Returns a ModeBlend if ≥2 blend-trigger keywords are found.
        Checks triggers in order; returns the first match.
        """
        from core.modes.blend import ModeBlend, BLEND_PRESETS

        for preset_name, keywords, synthesis in _BLEND_TRIGGERS:
            hits = [kw for kw in keywords if kw in text]
            if len(hits) >= 2:
                weights = BLEND_PRESETS.get(preset_name)
                if weights:
                    return ModeBlend(
                        weights=dict(weights),
                        synthesis=synthesis,
                        label=preset_name,
                    )
        return None

    def _learned_mode(
        self, domain: str, state: CognitiveState
    ) -> Optional[ModeID]:
        """Consult TraceLearner for data-driven single-mode recommendation."""
        try:
            from core.cognition.trace_learner import trace_learner
            rec = trace_learner.recommend_mode(domain, state)
            if rec:
                return ModeID(rec)
        except Exception:
            pass
        return None

    def _learned_blend(
        self, domain: str, state: CognitiveState
    ) -> Optional[Any]:
        """Consult TraceLearner for data-driven blend recommendation."""
        try:
            from core.cognition.trace_learner import trace_learner
            preset_name = trace_learner.recommend_blend(domain, state)
            if preset_name:
                from core.modes.blend import ModeBlend
                return ModeBlend.from_preset(preset_name)
        except Exception:
            pass
        return None

    def _adaptations(self, state: CognitiveState) -> Dict[str, Any]:
        f = state.fatigue
        return {
            "depth":            state.preferred_depth,
            "model_tier":       state.preferred_model_tier,
            "compress_context": f > 0.4,
            "defer_heavy":      f > 0.6,
            "ask_first":        f > 0.7,
            "blend_available":  state.energy >= _BLEND_MIN_ENERGY,
        }
