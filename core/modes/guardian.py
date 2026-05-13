"""
GUARDIAN mode — security, risk analysis, constraint enforcement, privacy, permission validation.

Wraps agents.guardian for pipeline-level validation; adds mode-level risk scoring.
"""

from __future__ import annotations

from typing import Any, Dict

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

# Hard risk keywords — always block regardless of state
_HARD_BLOCK = {"borrar todo", "delete all", "rm -rf", "drop table", "format disk"}


class GuardianMode(CognitiveMode):
    mode_id      = ModeID.GUARDIAN
    fatigue_cost = 0.03  # guardian runs frequently; keep cost low
    min_energy   = 0.0   # always activatable

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "").lower()
        domain   = context.get("domain", "general")

        # Hard-block check (deterministic, no LLM)
        for trigger in _HARD_BLOCK:
            if trigger in question:
                return ModeResult(
                    mode_id         = ModeID.GUARDIAN,
                    output          = {"blocked": True, "reason": f"hard_block: '{trigger}'"},
                    confidence      = 1.0,
                    tokens_used     = 0,
                    reasoning_depth = "minimal",
                )

        risk_score = self._score_risk(context, state)
        blocked    = risk_score > 0.8

        output: Dict[str, Any] = {
            "blocked":    blocked,
            "risk_score": round(risk_score, 3),
            "issues":     [],
        }

        # Use existing pipeline guardian for deeper validation when not blocked
        if not blocked:
            try:
                from agents.guardian import validate
                pipeline_output = context.get("pipeline_output", {})
                if pipeline_output:
                    validated = validate(pipeline_output, policy=context.get("aco_policy", {}))
                    output["pipeline_validation"] = validated
                    output["issues"] = validated.get("issues", [])
            except Exception:
                pass

        return ModeResult(
            mode_id         = ModeID.GUARDIAN,
            output          = output,
            confidence      = 0.9,
            tokens_used     = 0,
            reasoning_depth = "shallow",
        )

    def _score_risk(self, context: Dict[str, Any], state: CognitiveState) -> float:
        score = 0.0
        question = context.get("question", "").lower()

        risk_keywords = {
            "eliminar": 0.3, "borrar": 0.3, "sobreescribir": 0.4,
            "publicar": 0.2, "enviar": 0.2, "transferir": 0.3,
            "contraseña": 0.2, "token": 0.2, "api key": 0.3,
        }
        for kw, w in risk_keywords.items():
            if kw in question:
                score += w

        # Fatigued systems make riskier decisions
        if state.fatigue > 0.7:
            score += 0.2

        return min(score, 1.0)
