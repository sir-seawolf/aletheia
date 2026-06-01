"""
EXECUTIVE mode — convert plans into actions, task orchestration, workflow execution.

Delegates to core.agency for intent parsing and action execution.
"""

from __future__ import annotations

from typing import Any, Dict

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult


class ExecutiveMode(CognitiveMode):
    mode_id      = ModeID.EXECUTIVE
    fatigue_cost = 0.08
    min_energy   = 0.2

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")

        # Defer if fatigued — executive actions are irreversible
        if state.is_fatigued:
            return ModeResult(
                mode_id         = ModeID.EXECUTIVE,
                output          = {
                    "deferred": True,
                    "reason":   f"fatigue={state.fatigue:.2f}: action deferred for safety",
                },
                confidence      = 0.9,
                tokens_used     = 0,
                reasoning_depth = "minimal",
            )

        action_result: Dict[str, Any] = {}
        try:
            from core.agency.intent_parser import detect_intent
            from core.agency.action_executor import execute_action
            intent = detect_intent(question)
            if intent and intent.get("action"):
                action_result = execute_action(intent, domain=domain)
            else:
                action_result = {"no_action": True, "intent": intent}
        except Exception as exc:
            action_result = {"error": str(exc)}

        return ModeResult(
            mode_id         = ModeID.EXECUTIVE,
            output          = action_result,
            confidence      = 0.75,
            tokens_used     = 0,
            reasoning_depth = state.preferred_depth,
        )
