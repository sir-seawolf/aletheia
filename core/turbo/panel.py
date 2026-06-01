"""TurboPanel — parallel multi-provider LLM execution.

Strategies:
  SPECIALIST  fire all candidates simultaneously, return by priority order
  RACE        return the absolute first valid response from any provider
  PANEL       collect up to 3 responses and synthesize them

STATUS: IMPLEMENTED (TURBO v1)
"""

import importlib
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
    wait,
    FIRST_COMPLETED,
)
from typing import Any, Dict, List

from core.turbo.mode import (
    turbo_mode,
    SPECIALIST_TABLE,
    STRATEGY_RACE,
    STRATEGY_PANEL,
)

CALL_TIMEOUT  = 15.0   # seconds — live calls
PROBE_TIMEOUT = 10.0   # seconds — per-provider during activation probe

_PING_PROMPT = "Responde solo con: OK"

_REGISTRY: Dict[str, Dict[str, str]] = {
    "claude":   {"module": "core.llm.providers.claude_provider",   "class": "ClaudeProvider"},
    "openai":   {"module": "core.llm.providers.openai_provider",   "class": "OpenAIProvider"},
    "deepseek": {"module": "core.llm.providers.deepseek_provider", "class": "DeepSeekProvider"},
    "groq":     {"module": "core.llm.providers.groq_provider",     "class": "GroqProvider"},
    "mistral":  {"module": "core.llm.providers.mistral_provider",  "class": "MistralProvider"},
}


def _make(name: str):
    r = _REGISTRY[name]
    return getattr(importlib.import_module(r["module"]), r["class"])()


def _call(name: str, prompt: str, temp: float) -> str:
    return _make(name).generate(prompt, temp=temp)


class TurboPanel:

    # ── activation probe ──────────────────────────────────────────────────────

    def probe_all(self) -> Dict[str, Any]:
        """Parallel probe of all providers. Runs on POST /turbo/on."""

        def _probe_one(name: str) -> tuple[str, Dict[str, Any]]:
            try:
                prov = _make(name)
                if not prov.is_available():
                    return name, {"status": "no_key", "model": None, "latency_ms": None}
                t0 = time.time()
                prov.generate(_PING_PROMPT, temp=0.0)
                ms    = round((time.time() - t0) * 1000)
                model = getattr(prov, "model", None)
                return name, {"status": "ok", "model": model, "latency_ms": ms}
            except Exception as exc:
                return name, {
                    "status": "error",
                    "model": None,
                    "latency_ms": None,
                    "error": str(exc)[:120],
                }

        results: Dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=len(_REGISTRY)) as ex:
            future_map = {ex.submit(_probe_one, name): name for name in _REGISTRY}
            try:
                for future in as_completed(future_map, timeout=PROBE_TIMEOUT + 3):
                    try:
                        name, data = future.result(timeout=1)
                        results[name] = data
                    except Exception:
                        results[future_map[future]] = {
                            "status": "timeout", "model": None, "latency_ms": None
                        }
            except Exception:
                pass

        # Fill any that never yielded
        for name in _REGISTRY:
            if name not in results:
                results[name] = {"status": "timeout", "model": None, "latency_ms": None}

        return results

    # ── main entry point ──────────────────────────────────────────────────────

    def run(self, task: str, prompt: str, temp: float) -> str:
        available = turbo_mode.available_providers()

        # If probe was never run or all failed, do a quick key-only check
        if not available:
            available = [n for n in _REGISTRY if _make(n).is_available()]
        if not available:
            raise RuntimeError("TURBO: ningún provider tiene API key configurada.")

        strategy = turbo_mode.get_strategy()

        if strategy == STRATEGY_RACE:
            return self._race(available, prompt, temp)

        if strategy == STRATEGY_PANEL:
            return self._panel(available, prompt, temp)

        # SPECIALIST (default)
        ordered = SPECIALIST_TABLE.get(task, SPECIALIST_TABLE["_default"])
        candidates = [p for p in ordered if p in set(available)]
        if not candidates:
            candidates = available
        return self._specialist(candidates, prompt, temp)

    # ── strategies ───────────────────────────────────────────────────────────

    def _specialist(self, ordered: List[str], prompt: str, temp: float) -> str:
        """Fire all candidates simultaneously, return highest-priority success."""
        completed: Dict[str, str] = {}
        failed:    set[str]       = set()

        with ThreadPoolExecutor(max_workers=len(ordered)) as ex:
            futures = {ex.submit(_call, name, prompt, temp): name for name in ordered}
            try:
                for future in as_completed(futures, timeout=CALL_TIMEOUT):
                    name = futures[future]
                    try:
                        result = future.result()
                        if result and not result.startswith("[ERROR]"):
                            completed[name] = result
                        else:
                            failed.add(name)
                    except Exception:
                        failed.add(name)

                    # Yield the highest-priority result we can confirm right now
                    for p in ordered:
                        if p in completed:
                            tag = "primario" if p == ordered[0] else "suplente"
                            print(f"  [TURBO:SPECIALIST] {p} ({tag})")
                            return completed[p]
                        if p not in failed:
                            break   # still waiting for a higher-priority provider
            except Exception:
                pass

        # Final fallback: best completed by priority
        for p in ordered:
            if p in completed:
                print(f"  [TURBO:SPECIALIST] {p} (último recurso)")
                return completed[p]

        raise RuntimeError(f"TURBO SPECIALIST: fallaron todos ({', '.join(ordered)})")

    def _race(self, providers: List[str], prompt: str, temp: float) -> str:
        """Return the absolute first valid response, cycling through all providers on failure."""
        with ThreadPoolExecutor(max_workers=len(providers)) as ex:
            futures = {ex.submit(_call, name, prompt, temp): name for name in providers}
            remaining = set(futures.keys())
            while remaining:
                done, remaining = wait(remaining, timeout=CALL_TIMEOUT, return_when=FIRST_COMPLETED)
                if not done:
                    break  # global timeout reached
                for f in done:
                    try:
                        result = f.result()
                        if result and not result.startswith("[ERROR]"):
                            winner = futures[f]
                            print(f"  [TURBO:RACE] {winner} ganó")
                            for pf in remaining:
                                pf.cancel()
                            return result
                    except Exception:
                        pass
        raise RuntimeError(f"TURBO RACE: fallaron todos ({', '.join(providers)})")

    def _panel(self, providers: List[str], prompt: str, temp: float) -> str:
        """Collect responses from top 3 providers, then synthesize."""
        top = providers[:3]
        responses: Dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=len(top)) as ex:
            futures = {ex.submit(_call, name, prompt, temp): name for name in top}
            try:
                for future in as_completed(futures, timeout=CALL_TIMEOUT):
                    name = futures[future]
                    try:
                        result = future.result()
                        if result and not result.startswith("[ERROR]"):
                            responses[name] = result
                    except Exception:
                        pass
            except Exception:
                pass

        if not responses:
            raise RuntimeError(f"TURBO PANEL: fallaron todos ({', '.join(top)})")
        if len(responses) == 1:
            only = next(iter(responses.items()))
            print(f"  [TURBO:PANEL] solo {only[0]} respondió")
            return only[1]

        # Synthesize with best available provider
        synthesis_prompt = (
            f"Tienes {len(responses)} respuestas de distintos modelos al mismo prompt.\n\n"
            + "\n\n".join(
                f"=== {name.upper()} ===\n{text}"
                for name, text in responses.items()
            )
            + "\n\nSintetiza la mejor respuesta combinando lo mejor de cada una. "
              "Responde directamente sin mencionar que estás sintetizando."
        )
        synth_order = SPECIALIST_TABLE.get("validation", list(responses.keys()))
        for synth_name in synth_order:
            if synth_name in responses:
                try:
                    print(f"  [TURBO:PANEL] sintetizando con {synth_name}")
                    return _call(synth_name, synthesis_prompt, 0.2)
                except Exception:
                    pass

        # Absolute fallback: longest response
        return max(responses.values(), key=len)


turbo_panel = TurboPanel()
