"""TURBO mode state — active strategy, persistence, and routing table.

STATUS: IMPLEMENTED (TURBO v1)
"""

from typing import Any, Dict

STRATEGY_RACE       = "race"
STRATEGY_SPECIALIST = "specialist"
STRATEGY_PANEL      = "panel"

# Primary + ordered substitutes per pipeline stage.
# On activation, entries that lack an API key are silently skipped.
SPECIALIST_TABLE: Dict[str, list[str]] = {
    "exploration":      ["groq",     "mistral",  "deepseek", "openai",  "claude"],
    "simulation":       ["deepseek", "groq",     "mistral",  "openai",  "claude"],
    "validation":       ["claude",   "openai",   "deepseek", "groq",    "mistral"],
    "hestia_analysis":  ["claude",   "openai",   "deepseek", "groq",    "mistral"],
    "chat":             ["groq",     "mistral",  "openai",   "deepseek","claude"],
    "_default":         ["groq",     "claude",   "openai",   "deepseek","mistral"],
}


class TurboMode:

    def __init__(self):
        self._active: bool = False
        self._strategy: str = STRATEGY_SPECIALIST
        self._probe: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        try:
            from core.config.preferences import load
            t = load().get("turbo", {})
            self._active   = bool(t.get("active", False))
            self._strategy = t.get("strategy", STRATEGY_SPECIALIST)
        except Exception:
            pass

    def _persist(self) -> None:
        try:
            from core.config.preferences import update
            update("turbo", {"active": self._active, "strategy": self._strategy})
        except Exception:
            pass

    def activate(self, strategy: str = STRATEGY_SPECIALIST) -> None:
        self._strategy = strategy
        self._active   = True
        self._persist()

    def deactivate(self) -> None:
        self._active = False
        self._persist()

    def is_active(self) -> bool:
        return self._active

    def get_strategy(self) -> str:
        return self._strategy

    def set_probe(self, probe: Dict[str, Any]) -> None:
        self._probe = probe

    def get_probe(self) -> Dict[str, Any]:
        return self._probe

    def available_providers(self) -> list[str]:
        return [name for name, d in self._probe.items() if d.get("status") == "ok"]

    def effective_routing(self) -> Dict[str, str]:
        """Resolves the actual provider for each task given current availability."""
        available = set(self.available_providers())
        routing: Dict[str, str] = {}
        for task, ordered in SPECIALIST_TABLE.items():
            if task == "_default":
                continue
            for p in ordered:
                if p in available:
                    routing[task] = p
                    break
            else:
                routing[task] = "mock (sin providers disponibles)"
        return routing


turbo_mode = TurboMode()
