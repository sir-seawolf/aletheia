"""
ShadowRunner — runs Aletheia 3.0 modes in parallel with the v1 pipeline.

The v1 pipeline continues to serve the user response without delay.
ShadowRunner fires an asyncio task that:
  1. Activates ModeRegistry.route_and_activate() with the same context.
  2. Captures a CognitiveTrace with source="shadow_3.0".
  3. Persists it to TraceStore.
  4. Logs divergences if the output differs significantly from v1.

Toggle: set shadow_mode=true in PALACE/config/preferences.json,
or set env var ALETHEIA_SHADOW=1.

The shadow task NEVER raises — it is entirely best-effort and must
not impact the user-facing response in any way.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional


def is_shadow_enabled() -> bool:
    if os.getenv("ALETHEIA_SHADOW", "0") == "1":
        return True
    try:
        from core.config.preferences import get_preference
        return bool(get_preference("shadow_mode", False))
    except Exception:
        return False


async def run_shadow(
    session_id: str,
    domain: str,
    question: str,
    v1_output: str,
) -> None:
    """
    Async shadow task. Call with asyncio.create_task() — never await directly.
    Completes silently; any exception is swallowed.
    """
    if not is_shadow_enabled():
        return

    try:
        from core.session_state import get_state
        from core.modes.registry import mode_registry
        from core.tracing.context import begin_trace
        from core.tracing.store import trace_store

        state = get_state(session_id)
        context: Dict[str, Any] = {
            "domain":     domain,
            "question":   question,
            "session_id": session_id,
        }

        with begin_trace(session_id, domain, question, source="shadow_3.0") as tb:
            # Snapshot fatigue before shadow run
            tb.set_fatigue(state.fatigue, state.fatigue)

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: mode_registry.route_and_activate(context, state),
            )

            shadow_output = str(result.output)[:120]
            tb.confidence = result.confidence
            tb.add_tokens(result.tokens_used)

            trace = tb.finish(output=shadow_output, confidence=result.confidence)

        trace_store.save(trace)

        # Log divergence when outputs differ meaningfully
        _log_divergence(trace.trace_id, v1_output, shadow_output, session_id)

    except Exception:
        pass  # shadow must never raise


def _log_divergence(trace_id: str, v1: str, shadow: str, session_id: str) -> None:
    if v1[:60].strip() == shadow[:60].strip():
        return
    try:
        from core.event_bus import build_event, emit_event
        emit_event(build_event(
            session_id=session_id,
            agent="shadow_runner",
            stage="compare",
            event_type="shadow_divergence",
            payload={
                "trace_id":      trace_id,
                "v1_preview":    v1[:80],
                "shadow_preview": shadow[:80],
            },
            confidence=0.5,
        ))
    except Exception:
        pass


def schedule_shadow(
    session_id: str,
    domain: str,
    question: str,
    v1_output: str,
) -> None:
    """
    Fire-and-forget: schedules the shadow task on the running event loop.
    Safe to call from sync or async context.
    """
    if not is_shadow_enabled():
        return
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(run_shadow(session_id, domain, question, v1_output))
    except Exception:
        pass
