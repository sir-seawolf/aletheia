"""
ModeRegistry — central registry for all Aletheia cognitive modes.

Provides:
- get(mode_id) → CognitiveMode instance
- activate(mode_id, context, state) → ModeResult
- blend_and_activate(blend, context, state) → ModeResult
- route_and_activate(context, state) → ModeResult  (OBSERVER → blend or single mode)
- available_modes(state) → list of activatable ModeIDs
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult


class ModeRegistry:

    def __init__(self) -> None:
        self._modes: Dict[ModeID, CognitiveMode] = {}
        self._load_modes()

    def _load_modes(self) -> None:
        from core.modes.observer        import ObserverMode
        from core.modes.analytical      import AnalyticalMode
        from core.modes.strategic       import StrategicMode
        from core.modes.kronos          import KronosMode
        from core.modes.creative        import CreativeMode
        from core.modes.reflective      import ReflectiveMode
        from core.modes.guardian        import GuardianMode
        from core.modes.executive       import ExecutiveMode
        from core.modes.memory_curator  import MemoryCuratorMode
        from core.modes.researcher      import ResearcherMode
        from core.modes.world_model     import WorldModelMode

        for cls in [
            ObserverMode, AnalyticalMode, StrategicMode, KronosMode,
            CreativeMode, ReflectiveMode, GuardianMode, ExecutiveMode,
            MemoryCuratorMode, ResearcherMode, WorldModelMode,
        ]:
            instance = cls()
            self._modes[instance.mode_id] = instance

    # ── Core activation ──────────────────────────────────────────────────────

    def get(self, mode_id: ModeID) -> Optional[CognitiveMode]:
        return self._modes.get(mode_id)

    def activate(
        self,
        mode_id: ModeID,
        context: dict,
        state: CognitiveState,
    ) -> ModeResult:
        mode = self._modes.get(mode_id)
        if mode is None:
            return ModeResult(
                mode_id=mode_id,
                output={"error": f"Mode {mode_id} not registered"},
                confidence=0.0,
            )
        if not mode.can_activate(state):
            return ModeResult(
                mode_id=mode_id,
                output={
                    "skipped": True,
                    "reason":  f"energy={state.energy:.2f} below min={mode.min_energy}",
                },
                confidence=0.0,
            )
        return mode.activate(context, state)

    def available_modes(self, state: CognitiveState) -> List[ModeID]:
        return [mid for mid, m in self._modes.items() if m.can_activate(state)]

    # ── Blended activation ───────────────────────────────────────────────────

    def blend_and_activate(
        self,
        blend: Any,   # ModeBlend — typed as Any to avoid circular import at class level
        context: dict,
        state: CognitiveState,
    ) -> ModeResult:
        """
        Execute a ModeBlend using the BlendedModeExecutor.
        Writes blend info to the active trace (best-effort).
        """
        from core.modes.blend import BlendedModeExecutor
        executor = BlendedModeExecutor(self)
        result = executor.execute(blend, context, state)

        # Write to active trace
        try:
            from core.tracing.context import trace_mode
            trace_mode(f"BLEND:{blend.label}", f"synthesis={blend.synthesis}")
        except Exception:
            pass

        return result

    # ── Orchestration entry point ────────────────────────────────────────────

    def route_and_activate(
        self,
        context: dict,
        state: CognitiveState,
    ) -> ModeResult:
        """
        Full routing pipeline:
          1. OBSERVER analyses context → may propose blend or single mode
          2. If blend proposed and state allows → BlendedModeExecutor
          3. Else single mode activation
          4. Falls back to OBSERVER result if no routing available
        """
        observer_result = self.activate(ModeID.OBSERVER, context, state)

        # Priority 1: blend (multi-domain request + sufficient energy)
        blend = observer_result.next_blend
        if blend is not None:
            try:
                return self.blend_and_activate(blend, context, state)
            except Exception:
                pass  # blend failed → fall through to single mode

        # Priority 2: single mode
        target        = observer_result.next_mode
        routing_reason = observer_result.output.get("routed_to")

        try:
            from core.tracing.context import trace_mode
            mode_str = target.value if target else ModeID.OBSERVER.value
            trace_mode(mode_str, routing_reason)
        except Exception:
            pass

        if target and target != ModeID.OBSERVER:
            return self.activate(target, context, state)

        return observer_result

    # ── Introspection ────────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        return {
            "registered_modes": [m.value for m in self._modes],
            "blend_presets":    list(__import__("core.modes.blend", fromlist=["BLEND_PRESETS"]).BLEND_PRESETS.keys()),
        }


# Singleton
mode_registry = ModeRegistry()
