"""
Blended Cognition — weighted combinations of multiple cognitive modes.

A ModeBlend specifies which modes to activate and at what weight.
BlendedModeExecutor synthesises their outputs using one of three strategies:

  weighted_prompt  — combines mode system prompts weighted by their scores,
                     then makes a single LLM call. Most token-efficient.

  sequential       — chains modes: each mode receives the previous mode's
                     output as additional context. N LLM calls. Highest fidelity
                     for ordered pipelines (e.g. ANALYTICAL → GUARDIAN).

  parallel         — (stub) intended for future concurrent execution with
                     a final meta-synthesis LLM call.

The Observer activates blends when a request crosses multiple cognitive domains
or when CognitiveState has sufficient energy to afford multi-mode reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

if TYPE_CHECKING:
    from core.modes.registry import ModeRegistry


# ── Mode system-prompt fragments ──────────────────────────────────────────────
# Used to build weighted combined prompts.
_MODE_PROMPTS: Dict[ModeID, str] = {
    ModeID.ANALYTICAL:  "Razona con lógica estructurada, descompone el problema y valida hipótesis.",
    ModeID.STRATEGIC:   "Piensa a largo plazo, prioriza objetivos y analiza trade-offs reales.",
    ModeID.KRONOS:      "Analiza el impacto financiero y de sostenibilidad vital. El dinero es energía almacenada.",
    ModeID.CREATIVE:    "Genera ideas originales, conecta conceptos inesperados y propone soluciones innovadoras.",
    ModeID.REFLECTIVE:  "Detecta contradicciones, identifica patrones y ejerce metacognición honesta.",
    ModeID.GUARDIAN:    "Evalúa riesgos, valida permisos y aplica restricciones de seguridad.",
    ModeID.EXECUTIVE:   "Convierte planes en acciones concretas y gestionables.",
    ModeID.RESEARCHER:  "Busca, valida y sintetiza información de fuentes externas.",
    ModeID.WORLD_MODEL: "Modela sistemas complejos, analiza causalidades y simula consecuencias.",
    ModeID.OBSERVER:    "Supervisa y orquesta. Mantén coherencia y continuidad.",
    ModeID.MEMORY_CURATOR: "Consolida y comprime contexto relevante antes de responder.",
}


# ── Predefined blend presets ─────────────────────────────────────────────────

BLEND_PRESETS: Dict[str, Dict[ModeID, float]] = {
    "strategic_analytical": {ModeID.STRATEGIC: 0.55, ModeID.ANALYTICAL: 0.45},
    "reflective_kronos":    {ModeID.REFLECTIVE: 0.50, ModeID.KRONOS: 0.50},
    "creative_world":       {ModeID.CREATIVE: 0.55, ModeID.WORLD_MODEL: 0.45},
    "analytical_reflective": {ModeID.ANALYTICAL: 0.60, ModeID.REFLECTIVE: 0.40},
    "strategic_creative":   {ModeID.STRATEGIC: 0.50, ModeID.CREATIVE: 0.50},
    "kronos_strategic":     {ModeID.KRONOS: 0.60, ModeID.STRATEGIC: 0.40},
}


@dataclass
class ModeBlend:
    """
    Specifies a weighted combination of modes and how to synthesise them.

    weights must sum to ~1.0 (normalised automatically if not).
    label is human-readable; auto-generated from modes if empty.
    """
    weights:   Dict[ModeID, float]
    synthesis: str = "weighted_prompt"   # "weighted_prompt" | "sequential"
    label:     str = field(default="")

    def __post_init__(self) -> None:
        # Normalise weights
        total = sum(self.weights.values())
        if total > 0 and abs(total - 1.0) > 0.01:
            self.weights = {k: v / total for k, v in self.weights.items()}
        # Auto-label
        if not self.label:
            parts = sorted(self.weights, key=lambda m: -self.weights[m])
            self.label = "+".join(m.value.lower() for m in parts[:3])

    @property
    def total_fatigue_cost(self) -> float:
        from core.modes.base import CognitiveMode  # avoid circular at class level
        # Approximate: each mode contributes its fatigue_cost × weight
        return sum(self.weights.values()) * 0.06  # conservative estimate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label":     self.label,
            "synthesis": self.synthesis,
            "weights":   {k.value: round(v, 3) for k, v in self.weights.items()},
        }

    @classmethod
    def from_preset(cls, preset_name: str, synthesis: str = "weighted_prompt") -> ModeBlend:
        weights = BLEND_PRESETS.get(preset_name)
        if not weights:
            raise ValueError(f"Unknown blend preset: {preset_name}")
        return cls(weights=dict(weights), synthesis=synthesis, label=preset_name)


class BlendedModeExecutor:
    """
    Executes a ModeBlend using the configured synthesis strategy.
    Registered in ModeRegistry as a virtual mode.
    """

    def __init__(self, registry: ModeRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        blend: ModeBlend,
        context: Dict[str, Any],
        state: CognitiveState,
    ) -> ModeResult:
        if blend.synthesis == "sequential":
            return self._sequential(blend, context, state)
        return self._weighted_prompt(blend, context, state)

    # ── Strategies ─────────────────────────────────────────────────────────

    def _weighted_prompt(
        self,
        blend: ModeBlend,
        context: Dict[str, Any],
        state: CognitiveState,
    ) -> ModeResult:
        """
        Build a single LLM prompt that combines mode instructions proportionally.
        One LLM call — most token-efficient strategy.
        """
        domain   = context.get("domain", "general")
        question = context.get("question", "")
        depth    = state.preferred_depth

        # Compose weighted system instructions
        instructions = _build_weighted_instructions(blend.weights)

        prompt = (
            f"Eres Aletheia en modo cognitivo combinado [{blend.label}].\n\n"
            f"Instrucciones ponderadas:\n{instructions}\n\n"
            f"Dominio: {domain}\n"
            f"Pregunta: {question}\n"
            f"Profundidad de razonamiento: {depth}\n\n"
            "Responde integrando todas las perspectivas indicadas según su peso."
        )

        from core.llm.router import router
        response = router.generate(
            task="blended",
            prompt=prompt,
            context={"domain": domain, "blend": blend.label, "mode": "blended"},
            temp=0.4,
        )

        token_est = len(prompt.split()) + len(response.split())
        state.apply_fatigue_delta(blend.total_fatigue_cost)
        state.record_llm_call(token_est)

        return ModeResult(
            mode_id         = ModeID.OBSERVER,  # blend uses OBSERVER as carrier
            output          = {
                "blend_label": blend.label,
                "synthesis":   "weighted_prompt",
                "weights":     {k.value: round(v, 3) for k, v in blend.weights.items()},
                "response":    response,
            },
            confidence      = 0.75,
            tokens_used     = token_est,
            reasoning_depth = depth,
        )

    def _sequential(
        self,
        blend: ModeBlend,
        context: Dict[str, Any],
        state: CognitiveState,
    ) -> ModeResult:
        """
        Chain modes in descending weight order.
        Each mode's output is injected into the next mode's context.
        """
        ordered = sorted(blend.weights.items(), key=lambda x: -x[1])
        accumulated_output = ""
        last_result: Optional[ModeResult] = None

        for mode_id, weight in ordered:
            if not state.can_afford_mode(weight):
                break

            augmented_context = dict(context)
            if accumulated_output:
                augmented_context["prior_output"] = accumulated_output[:500]
                augmented_context["question"] = (
                    f"{context.get('question', '')}\n\n"
                    f"[Contexto previo: {accumulated_output[:300]}]"
                )

            result = self._registry.activate(mode_id, augmented_context, state)
            accumulated_output = str(result.output)[:600]
            last_result = result

        if last_result is None:
            return ModeResult(
                mode_id    = ModeID.OBSERVER,
                output     = {"error": "sequential blend exhausted state"},
                confidence = 0.0,
            )

        last_result.output["blend_label"] = blend.label
        last_result.output["synthesis"]   = "sequential"
        return last_result


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_weighted_instructions(weights: Dict[ModeID, float]) -> str:
    ordered = sorted(weights.items(), key=lambda x: -x[1])
    lines = []
    for mode_id, w in ordered:
        prompt = _MODE_PROMPTS.get(mode_id, mode_id.value)
        pct    = int(w * 100)
        lines.append(f"  [{pct}%] {prompt}")
    return "\n".join(lines)
