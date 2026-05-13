"""
TraceStore — SQLite persistence for CognitiveTrace records.

Table: cognitive_traces in memory/data/aletheia.db (shared DB).
Migration is idempotent — safe to call init_traces_table() on every startup.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from core.tracing.trace import CognitiveTrace

_DB_PATH = "memory/data/aletheia.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS cognitive_traces (
    trace_id              TEXT PRIMARY KEY,
    session_id            TEXT NOT NULL,
    timestamp             TEXT NOT NULL,
    source                TEXT NOT NULL,
    domain                TEXT,
    question_preview      TEXT,
    mode_activated        TEXT,
    observer_routing_reason TEXT,
    provider_used         TEXT,
    model_tier            TEXT,
    routing_reasoning     TEXT,
    memory_sources        TEXT,
    memory_items_used     INTEGER,
    fatigue_before        REAL,
    fatigue_after         REAL,
    fatigue_delta         REAL,
    tokens_used           INTEGER,
    latency_ms            REAL,
    confidence            REAL,
    output_preview        TEXT,
    error                 TEXT
)
"""

_INSERT = """
INSERT OR REPLACE INTO cognitive_traces (
    trace_id, session_id, timestamp, source, domain, question_preview,
    mode_activated, observer_routing_reason, provider_used, model_tier,
    routing_reasoning, memory_sources, memory_items_used,
    fatigue_before, fatigue_after, fatigue_delta,
    tokens_used, latency_ms, confidence, output_preview, error
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


class TraceStore:

    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._db = db_path
        self._init()

    def _init(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(_CREATE_TABLE)
                # Idempotent migration for divergences table
                from core.tracing.divergence import _CREATE_DIVERGENCES_TABLE
                conn.execute(_CREATE_DIVERGENCES_TABLE)
        except Exception:
            pass

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Write ────────────────────────────────────────────────────────────────

    def save(self, trace: CognitiveTrace) -> None:
        try:
            with self._connect() as conn:
                conn.execute(_INSERT, (
                    trace.trace_id,
                    trace.session_id,
                    trace.timestamp,
                    trace.source,
                    trace.domain,
                    trace.question_preview,
                    trace.mode_activated,
                    trace.observer_routing_reason,
                    trace.provider_used,
                    trace.model_tier,
                    trace.routing_reasoning,
                    json.dumps(trace.memory_sources),
                    trace.memory_items_used,
                    trace.fatigue_before,
                    trace.fatigue_after,
                    trace.fatigue_delta,
                    trace.tokens_used,
                    trace.latency_ms,
                    trace.confidence,
                    trace.output_preview,
                    trace.error,
                ))
        except Exception:
            pass  # traces are best-effort; never break the pipeline

    # ── Read ─────────────────────────────────────────────────────────────────

    def recent(
        self,
        limit: int = 50,
        session_id: Optional[str] = None,
        source: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        where, params = self._build_where(session_id, source, mode)
        sql = (
            f"SELECT * FROM cognitive_traces"
            f"{where} ORDER BY timestamp DESC LIMIT ?"
        )
        params.append(limit)
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]
        except Exception:
            return []

    def get(self, trace_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM cognitive_traces WHERE trace_id = ?",
                    (trace_id,),
                ).fetchone()
            return self._row_to_dict(row) if row else None
        except Exception:
            return None

    def summary(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregate stats: mode counts, avg latency, avg fatigue delta, top providers."""
        where, params = self._build_where(session_id)
        sql = (
            f"SELECT mode_activated, provider_used, model_tier, "
            f"AVG(latency_ms) as avg_latency, AVG(fatigue_delta) as avg_fatigue, "
            f"AVG(tokens_used) as avg_tokens, COUNT(*) as count "
            f"FROM cognitive_traces{where} "
            f"GROUP BY mode_activated, provider_used, model_tier "
            f"ORDER BY count DESC"
        )
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
            return {"groups": [dict(r) for r in rows], "total": sum(r["count"] for r in rows)}
        except Exception:
            return {"groups": [], "total": 0}

    def divergences(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Shadow traces where output_preview differs significantly from the paired v1 trace."""
        sql = """
        SELECT s.trace_id, s.session_id, s.timestamp,
               s.mode_activated, s.output_preview as shadow_output,
               v.output_preview as v1_output,
               s.latency_ms as shadow_latency, v.latency_ms as v1_latency,
               s.fatigue_delta as shadow_fatigue, v.fatigue_delta as v1_fatigue
        FROM cognitive_traces s
        JOIN cognitive_traces v ON s.session_id = v.session_id
            AND s.question_preview = v.question_preview
            AND s.source = 'shadow_3.0'
            AND v.source = 'v1_pipeline'
        WHERE s.output_preview != v.output_preview
        ORDER BY s.timestamp DESC
        LIMIT ?
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, (limit,)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def analyzed_divergences(
        self,
        limit: int = 50,
        winner: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return persisted DivergenceReports from trace_divergences table.
        If the table is empty, triggers a fresh analysis pass first.
        """
        # Lazy-trigger analysis if table is empty
        try:
            with self._connect() as conn:
                count = conn.execute("SELECT COUNT(*) FROM trace_divergences").fetchone()[0]
            if count == 0:
                from core.tracing.divergence import divergence_analyzer
                divergence_analyzer.analyze(limit=limit)
        except Exception:
            pass

        clauses, params = [], []
        if winner:
            clauses.append("overall_winner = ?")
            params.append(winner)
        if mode:
            clauses.append("mode_activated = ?")
            params.append(mode)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM trace_divergences{where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def divergence_stats(self) -> Dict[str, Any]:
        """Aggregate stats from persisted divergence reports."""
        try:
            from core.tracing.divergence import divergence_analyzer
            return divergence_analyzer.aggregate_stats()
        except Exception:
            return {}

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_where(
        session_id: Optional[str] = None,
        source: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        clauses, params = [], []
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if source:
            clauses.append("source = ?")
            params.append(source)
        if mode:
            clauses.append("mode_activated = ?")
            params.append(mode)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return where, params

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        if d.get("memory_sources"):
            try:
                d["memory_sources"] = json.loads(d["memory_sources"])
            except Exception:
                d["memory_sources"] = []
        return d


# Singleton
trace_store = TraceStore()


def init_traces_table() -> None:
    """Idempotent migration — call at startup."""
    trace_store._init()
