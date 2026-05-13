"""
Cognitive Replay — re-execute historical traces with different parameters.

Allows answering questions like:
  "What would have happened with STRATEGIC instead of ANALYTICAL?"
  "How would Aletheia respond under high fatigue (0.8)?"
  "Which provider would have been most efficient here?"

Core flow:
  1. Fetch original CognitiveTrace by trace_id.
  2. Apply ReplayConfig overrides (mode, provider, cognitive state).
  3. Run through ModeRegistry or LLMRouter with trace context active.
  4. Persist new CognitiveTrace with source="replay".
  5. Optionally run DivergenceAnalyzer against the original → DivergenceReport.

batch_replay() runs N ReplayConfigs against the same original,
returns ranked ReplayResults — the "simulation" capability.

ReplayStore persists results in cognitive_replays SQLite table.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_DB_PATH = "memory/data/aletheia.db"

_CREATE_REPLAYS_TABLE = """
CREATE TABLE IF NOT EXISTS cognitive_replays (
    replay_id           TEXT PRIMARY KEY,
    original_trace_id   TEXT NOT NULL,
    new_trace_id        TEXT,
    timestamp           TEXT NOT NULL,
    config              TEXT,
    improvement         TEXT,
    divergence_score    REAL,
    divergence_winner   TEXT,
    summary             TEXT
)
"""


# ── Config & Result ───────────────────────────────────────────────────────────

@dataclass
class ReplayConfig:
    """
    Parameters for a cognitive replay run.
    All fields are optional — omit to keep the original behaviour.
    """
    target_mode:          Optional[str] = None   # ModeID.value or blend preset name
    target_provider:      Optional[str] = None   # "ollama" | "claude" | ...
    state_override:       Optional[Dict[str, Any]] = None  # {"fatigue": 0.8, ...}
    synthesis:            str = "weighted_prompt"
    compare_with_original: bool = True
    label:                str = ""               # human description of this scenario

    def __post_init__(self) -> None:
        if not self.label:
            parts = []
            if self.target_mode:
                parts.append(f"mode={self.target_mode}")
            if self.target_provider:
                parts.append(f"provider={self.target_provider}")
            if self.state_override:
                parts += [f"{k}={v}" for k, v in self.state_override.items()]
            self.label = "|".join(parts) or "default"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_mode":          self.target_mode,
            "target_provider":      self.target_provider,
            "state_override":       self.state_override,
            "synthesis":            self.synthesis,
            "compare_with_original": self.compare_with_original,
            "label":                self.label,
        }


@dataclass
class ReplayResult:
    replay_id:         str
    original_trace_id: str
    new_trace_id:      Optional[str]
    config:            ReplayConfig
    improvement:       str    # "better" | "worse" | "tie" | "no_comparison"
    divergence_score:  Optional[float]
    divergence_winner: Optional[str]
    summary:           str
    new_trace:         Optional[Any] = field(default=None, repr=False)  # CognitiveTrace

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replay_id":         self.replay_id,
            "original_trace_id": self.original_trace_id,
            "new_trace_id":      self.new_trace_id,
            "config":            self.config.to_dict(),
            "improvement":       self.improvement,
            "divergence_score":  self.divergence_score,
            "divergence_winner": self.divergence_winner,
            "summary":           self.summary,
        }


# ── Core engine ───────────────────────────────────────────────────────────────

class CognitiveReplayer:
    """
    Replays a historical CognitiveTrace with modified parameters.
    """

    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._db    = db_path
        self._store = ReplayStore(db_path)

    def replay(
        self,
        trace_id: str,
        config: ReplayConfig,
    ) -> ReplayResult:
        """
        Re-run the question from trace_id under config overrides.
        Returns a ReplayResult with the new trace and optional divergence report.
        """
        from core.tracing.store import trace_store
        original = trace_store.get(trace_id)
        if not original:
            return self._error_result(trace_id, config, f"trace {trace_id} not found")

        domain   = original.get("domain", "general")
        question = original.get("question_preview", "")
        session  = original.get("session_id", "replay")

        # Build cognitive state (fresh + optional overrides)
        state = self._build_state(config.state_override)

        # Run with tracing
        from core.tracing.context import begin_trace
        from core.tracing.store import trace_store as ts

        with begin_trace(session, domain, question, source="replay") as tb:
            output = self._run(config, domain, question, session, state)
            new_trace = tb.finish(output=output, confidence=state.confidence)

        ts.save(new_trace)

        # Compare
        improvement, div_score, div_winner = "no_comparison", None, None
        if config.compare_with_original:
            improvement, div_score, div_winner = self._compare(original, new_trace)

        summary = self._summarise(config, original, new_trace, improvement)
        result = ReplayResult(
            replay_id         = str(uuid.uuid4()),
            original_trace_id = trace_id,
            new_trace_id      = new_trace.trace_id,
            config            = config,
            improvement       = improvement,
            divergence_score  = div_score,
            divergence_winner = div_winner,
            summary           = summary,
            new_trace         = new_trace,
        )
        self._store.save(result)
        return result

    def batch_replay(
        self,
        trace_id: str,
        configs: List[ReplayConfig],
    ) -> List[ReplayResult]:
        """
        Run multiple ReplayConfigs against the same trace.
        Returns results sorted by divergence_score (best first).
        """
        results = [self.replay(trace_id, cfg) for cfg in configs]
        return sorted(
            results,
            key=lambda r: (r.divergence_score or 0),
            reverse=True,
        )

    # ── Internal ─────────────────────────────────────────────────────────────

    def _run(
        self,
        config: ReplayConfig,
        domain: str,
        question: str,
        session: str,
        state: Any,
    ) -> str:
        context = {
            "domain":     domain,
            "question":   question,
            "session_id": session,
        }

        # Force a specific mode/blend
        if config.target_mode:
            from core.modes.registry import mode_registry
            from core.modes.base import ModeID
            from core.modes.blend import BLEND_PRESETS, ModeBlend

            if config.target_mode in BLEND_PRESETS:
                blend = ModeBlend.from_preset(config.target_mode, config.synthesis)
                result = mode_registry.blend_and_activate(blend, context, state)
            else:
                try:
                    mode_id = ModeID(config.target_mode)
                    result = mode_registry.activate(mode_id, context, state)
                except ValueError:
                    result = mode_registry.route_and_activate(context, state)
            return str(result.output)

        # Force a specific provider (via LLMRouter directly)
        if config.target_provider:
            from core.llm.router import router
            prompt = (
                f"Dominio: {domain}\n"
                f"Solicitud: {question}\n\n"
                "Responde de forma concisa y útil."
            )
            return router._call_configured(
                prompt, 0.4,
                route_provider=config.target_provider,
            )

        # Default: route normally through Observer
        from core.modes.registry import mode_registry
        result = mode_registry.route_and_activate(context, state)
        return str(result.output)

    @staticmethod
    def _build_state(overrides: Optional[Dict[str, Any]]) -> Any:
        from core.cognitive_state import CognitiveState
        state = CognitiveState()
        if overrides:
            for key, val in overrides.items():
                if hasattr(state, key):
                    try:
                        setattr(state, key, type(getattr(state, key))(val))
                    except Exception:
                        pass
        return state

    @staticmethod
    def _compare(
        original: Dict[str, Any],
        new_trace: Any,
    ):
        """
        Quick comparison using the same dimension logic as DivergenceAnalyzer.
        Returns (improvement, overall_score, winner).
        """
        try:
            from core.tracing.divergence import DivergenceScore, _clamp

            o_conf   = float(original.get("confidence", 0))
            n_conf   = float(new_trace.confidence)
            o_tok    = int(original.get("tokens_used", 0))
            n_tok    = int(new_trace.tokens_used)
            o_fat    = float(original.get("fatigue_delta", 0))
            n_fat    = float(new_trace.fatigue_delta)
            o_items  = int(original.get("memory_items_used", 0))
            n_items  = int(new_trace.memory_items_used)
            o_src    = len(original.get("memory_sources") or [])
            n_src    = len(new_trace.memory_sources)

            max_tok  = max(o_tok, n_tok, 1)
            max_items = max(o_items, n_items, 1)
            max_src  = max(o_src, n_src, 1)

            scores = DivergenceScore(
                reasoning_depth   = _clamp(n_conf - o_conf),
                cost_efficiency   = _clamp((o_tok - n_tok) / max_tok),
                coherence         = _clamp(
                    n_conf / (n_fat + 0.01) - o_conf / (o_fat + 0.01)
                ),
                context_alignment = _clamp((n_items - o_items) / max_items),
                fatigue_impact    = _clamp(o_fat - n_fat),
                memory_retrieval  = _clamp((n_src - o_src) / max_src),
            )
            overall = scores.overall()
            winner  = scores.winner()
            improvement = (
                "better" if winner == "shadow_3.0"
                else "worse" if winner == "v1_pipeline"
                else "tie"
            )
            return improvement, round(overall, 4), winner
        except Exception:
            return "no_comparison", None, None

    @staticmethod
    def _summarise(
        config: ReplayConfig,
        original: Dict[str, Any],
        new_trace: Any,
        improvement: str,
    ) -> str:
        orig_mode = original.get("mode_activated") or "v1_pipeline"
        new_mode  = new_trace.mode_activated or config.target_mode or "auto"
        icon = {"better": "↑", "worse": "↓", "tie": "=", "no_comparison": "?"}.get(improvement, "?")
        return (
            f"{icon} {config.label}: "
            f"{orig_mode}→{new_mode} | "
            f"conf {original.get('confidence', 0):.2f}→{new_trace.confidence:.2f} | "
            f"tokens {original.get('tokens_used', 0)}→{new_trace.tokens_used}"
        )

    @staticmethod
    def _error_result(trace_id: str, config: ReplayConfig, reason: str) -> ReplayResult:
        return ReplayResult(
            replay_id         = str(uuid.uuid4()),
            original_trace_id = trace_id,
            new_trace_id      = None,
            config            = config,
            improvement       = "no_comparison",
            divergence_score  = None,
            divergence_winner = None,
            summary           = f"ERROR: {reason}",
        )


# ── ReplayStore ───────────────────────────────────────────────────────────────

class ReplayStore:

    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._db = db_path
        self._init()

    def _init(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(_CREATE_REPLAYS_TABLE)
        except Exception:
            pass

    def save(self, result: ReplayResult) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cognitive_replays
                    (replay_id, original_trace_id, new_trace_id, timestamp,
                     config, improvement, divergence_score, divergence_winner, summary)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        result.replay_id,
                        result.original_trace_id,
                        result.new_trace_id,
                        datetime.now(timezone.utc).isoformat(),
                        json.dumps(result.config.to_dict()),
                        result.improvement,
                        result.divergence_score,
                        result.divergence_winner,
                        result.summary,
                    ),
                )
        except Exception:
            pass

    def history(
        self,
        limit: int = 50,
        original_trace_id: Optional[str] = None,
        improvement: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clauses, params = [], []
        if original_trace_id:
            clauses.append("original_trace_id = ?")
            params.append(original_trace_id)
        if improvement:
            clauses.append("improvement = ?")
            params.append(improvement)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql   = f"SELECT * FROM cognitive_replays{where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                if d.get("config"):
                    try:
                        d["config"] = json.loads(d["config"])
                    except Exception:
                        pass
                results.append(d)
            return results
        except Exception:
            return []

    def stats(self) -> Dict[str, Any]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT improvement, COUNT(*) as count,
                           AVG(divergence_score) as avg_score
                    FROM cognitive_replays
                    GROUP BY improvement
                    """
                ).fetchall()
            total = sum(r["count"] for r in rows)
            return {
                "total":    total,
                "by_improvement": {r["improvement"]: {
                    "count":     r["count"],
                    "avg_score": round(r["avg_score"] or 0, 4),
                } for r in rows},
            }
        except Exception:
            return {"total": 0}

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn


# ── Singletons ────────────────────────────────────────────────────────────────

cognitive_replayer = CognitiveReplayer()
replay_store       = ReplayStore()
