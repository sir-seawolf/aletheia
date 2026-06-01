"""
ConsolidationEngine — motor de "sueño cognitivo".

Durante conversaciones activas el sistema responde rápido sin procesar en
profundidad. Este motor ejecuta el trabajo pesado diferido:

  Pasos de consolidación:
    1. Drena RawBuffer (entradas encoladas durante conversaciones)
    2. PALACE → semantic graph   (consolidator.consolidate)
    3. Recomputa insights        (TraceLearner.compute_insights)
    4. Revisa degradación        (StrategyDegradation)
    5. Comprime working memory   (FatigueEngine.compress_context)

Modos de ejecución:
  run_now()          — síncrono, bloquea hasta terminar
  start_background() — hilo daemon, no bloquea
  stop()             — señal de parada limpia (espera hasta 30 s)
  set_schedule(h, m) — dispara diariamente a esa hora (hilo de guardia)
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any

_SCHEDULE_KEY = "consolidation_schedule"   # key inside preferences.json → system section


class _Progress:
    """Thread-safe step tracker."""

    def __init__(self) -> None:
        self._lock  = threading.Lock()
        self._step  = ""
        self._done  = 0
        self._total = 0

    def set(self, step: str, done: int = 0, total: int = 0) -> None:
        with self._lock:
            self._step, self._done, self._total = step, done, total

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"step": self._step, "done": self._done, "total": self._total}


class ConsolidationEngine:

    def __init__(self) -> None:
        self._state      = "idle"        # "idle" | "running" | "scheduled"
        self._thread: threading.Thread | None = None
        self._guard:  threading.Thread | None = None
        self._stop_ev    = threading.Event()
        self._last_result: dict[str, Any] = {}
        self._last_run:    str | None     = None
        self._progress     = _Progress()
        self._schedule: dict[str, Any] | None = None
        self._lock         = threading.Lock()
        self._load_schedule()

    # ── Public API ──────────────────────────────────────────────────────────

    def run_now(self) -> dict[str, Any]:
        """Run full consolidation synchronously. Returns stats dict."""
        with self._lock:
            if self._state == "running":
                return {"error": "Ya hay una consolidación en curso."}
            self._state = "running"
            self._stop_ev.clear()

        try:
            result = self._consolidate()
        finally:
            with self._lock:
                self._state = "scheduled" if self._schedule and self._schedule.get("enabled") else "idle"

        return result

    def start_background(self) -> bool:
        """
        Start consolidation in a daemon background thread.
        Returns False if one is already running.
        """
        with self._lock:
            if self._state == "running":
                return False
            self._state = "running"
            self._stop_ev.clear()

        self._thread = threading.Thread(
            target=self._bg_run,
            daemon=True,
            name="aletheia-consolidation",
        )
        self._thread.start()
        return True

    def stop(self) -> None:
        """Signal a running consolidation to stop gracefully."""
        self._stop_ev.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=30)

    def set_schedule(self, hour: int, minute: int = 0, enabled: bool = True) -> None:
        """Set a daily consolidation schedule. Persists to preferences.json."""
        schedule = {"hour": hour, "minute": minute, "enabled": enabled}
        with self._lock:
            self._schedule = schedule
        self._save_schedule(schedule)
        if enabled:
            self._ensure_guard()
            with self._lock:
                if self._state == "idle":
                    self._state = "scheduled"
        else:
            with self._lock:
                if self._state == "scheduled":
                    self._state = "idle"

    def status(self) -> dict[str, Any]:
        """Return current engine state."""
        with self._lock:
            state     = self._state
            last_run  = self._last_run
            last_res  = dict(self._last_result)
            schedule  = dict(self._schedule) if self._schedule else None

        try:
            from core.memory.raw_buffer import raw_buffer
            queue = raw_buffer.stats()
        except Exception:
            queue = {"pending": 0, "total": 0}

        return {
            "state":       state,
            "last_run":    last_run,
            "last_result": last_res,
            "progress":    self._progress.snapshot(),
            "schedule":    schedule,
            "queue":       queue,
        }

    # ── Internal ────────────────────────────────────────────────────────────

    def _bg_run(self) -> None:
        try:
            result = self._consolidate()
            with self._lock:
                self._last_result = result
        finally:
            with self._lock:
                self._state = "scheduled" if self._schedule and self._schedule.get("enabled") else "idle"

    def _consolidate(self) -> dict[str, Any]:
        """Execute all consolidation steps. Returns stats."""
        start    = time.time()
        stats: dict[str, Any] = {
            "started_at":  datetime.now().isoformat(timespec="seconds"),
            "buffer_items": 0,
            "nodes":        0,
            "insights":     0,
            "errors":       [],
        }

        # Step 1 — drain raw buffer
        self._progress.set("Drenando cola de conversaciones…")
        try:
            from core.memory.raw_buffer import raw_buffer
            items = raw_buffer.drain(limit=500)
            stats["buffer_items"] = len(items)
            # Persist drained items to SQLite episodic (best-effort)
            if items:
                from memory.service import store_result
                for item in items:
                    if self._stop_ev.is_set():
                        break
                    try:
                        store_result(item["domain"], item["content"])
                    except Exception:
                        pass
        except Exception as e:
            stats["errors"].append(f"buffer: {e}")

        if self._stop_ev.is_set():
            stats["stopped"] = True
            self._last_run = stats["started_at"]
            return stats

        # Step 2 — PALACE → semantic graph
        self._progress.set("Consolidando PALACE → grafo semántico…")
        try:
            from core.memory.consolidator import consolidate
            nodes = consolidate(verbose=False)
            stats["nodes"] = nodes
        except Exception as e:
            stats["errors"].append(f"consolidator: {e}")

        if self._stop_ev.is_set():
            stats["stopped"] = True
            self._last_run = stats["started_at"]
            return stats

        # Step 3 — TraceLearner insights
        self._progress.set("Recomputando insights de modos y proveedores…")
        try:
            from core.cognition.trace_learner import trace_learner
            modes, providers = trace_learner.compute_insights(force=True)
            stats["insights"] = len(modes) + len(providers)
        except Exception as e:
            stats["errors"].append(f"trace_learner: {e}")

        # Step 4 — strategy degradation review
        self._progress.set("Revisando degradación de estrategias…")
        try:
            from core.cognition.degradation import strategy_degradation
            # Trigger auto-recovery evaluation (already done in compute_insights,
            # but explicit call ensures fresh state)
            strategy_degradation.get_all()
        except Exception as e:
            stats["errors"].append(f"degradation: {e}")

        # Step 5 — compress working memory via FatigueEngine
        self._progress.set("Comprimiendo contexto de trabajo…")
        try:
            from core.fatigue.engine import fatigue_engine
            from core.session_state import get_state
            state = get_state("local")
            if state.fatigue > 0.3:
                fatigue_engine.compress_context(state)
        except Exception as e:
            stats["errors"].append(f"compress: {e}")

        # Step 6 — detect cognitive patterns
        self._progress.set("Detectando patrones cognitivos…")
        try:
            from core.cognition.pattern_detector import pattern_detector
            patterns = pattern_detector.detect(since_hours=48)
            stats["patterns_found"] = len(patterns)
        except Exception as e:
            stats["errors"].append(f"patterns: {e}")
            stats["patterns_found"] = 0

        elapsed = round(time.time() - start, 1)
        stats["elapsed_s"]   = elapsed
        stats["finished_at"] = datetime.now().isoformat(timespec="seconds")

        with self._lock:
            self._last_result = stats
            self._last_run    = stats["finished_at"]

        self._progress.set("Completado", 1, 1)
        return stats

    # ── Scheduler guard ─────────────────────────────────────────────────────

    def _ensure_guard(self) -> None:
        """Start the scheduler guard thread if not already running."""
        if self._guard and self._guard.is_alive():
            return
        self._guard = threading.Thread(
            target=self._schedule_loop,
            daemon=True,
            name="aletheia-consolidation-guard",
        )
        self._guard.start()

    def _schedule_loop(self) -> None:
        """Check every 60 s whether it's time to run scheduled consolidation."""
        while True:
            time.sleep(60)
            with self._lock:
                sched = self._schedule
                state = self._state
            if not sched or not sched.get("enabled"):
                break
            now = datetime.now()
            if now.hour == sched["hour"] and now.minute == sched["minute"]:
                if state != "running":
                    self.start_background()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_schedule(self) -> None:
        try:
            from core.config.preferences import load
            prefs = load()
            sched = prefs.get("system", {}).get(_SCHEDULE_KEY)
            if sched and isinstance(sched, dict):
                self._schedule = sched
                if sched.get("enabled"):
                    self._state = "scheduled"
                    self._ensure_guard()
        except Exception:
            pass

    def _save_schedule(self, schedule: dict[str, Any]) -> None:
        try:
            from core.config.preferences import update
            update("system", {_SCHEDULE_KEY: schedule})
        except Exception:
            pass


# Process-level singleton
consolidation_engine = ConsolidationEngine()
