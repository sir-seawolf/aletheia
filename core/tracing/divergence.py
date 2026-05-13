"""
DivergenceAnalyzer — multidimensional scoring of shadow vs v1 trace pairs.

For each paired (v1_pipeline, shadow_3.0) request, produces a DivergenceReport
that classifies which system performed better and why, across 6 dimensions:

  reasoning_depth   — confidence quality (shadow vs v1)
  cost_efficiency   — token economy
  coherence         — confidence / fatigue_delta ratio
  context_alignment — memory retrieval depth
  fatigue_impact    — cognitive cost to the system
  memory_retrieval  — breadth of memory sources used

The overall_score is a weighted sum in [-1, +1]:
  > +0.10 → shadow_3.0 wins
  < -0.10 → v1_pipeline wins
  else    → tie

Scores feed the Adaptive Learning Loop (TraceLearner) to bias future routing.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_DB_PATH = "memory/data/aletheia.db"

# Dimension weights (must sum to 1.0)
_WEIGHTS: Dict[str, float] = {
    "reasoning_depth":   0.35,
    "cost_efficiency":   0.20,
    "coherence":         0.20,
    "fatigue_impact":    0.15,
    "context_alignment": 0.05,
    "memory_retrieval":  0.05,
}

_WIN_THRESHOLD  =  0.10   # shadow wins above this
_LOSE_THRESHOLD = -0.10   # v1 wins below this


@dataclass
class DivergenceScore:
    """Per-dimension score in [-1, +1]. Positive = shadow_3.0 better."""
    reasoning_depth:   float  # shadow.confidence − v1.confidence
    cost_efficiency:   float  # (v1_tokens − shadow_tokens) / max_tokens
    coherence:         float  # confidence/fatigue ratio delta
    context_alignment: float  # shadow memory items vs v1
    fatigue_impact:    float  # v1_fatigue_delta − shadow_fatigue_delta
    memory_retrieval:  float  # shadow source breadth vs v1

    def overall(self) -> float:
        return sum(
            getattr(self, dim) * weight
            for dim, weight in _WEIGHTS.items()
        )

    def winner(self) -> str:
        s = self.overall()
        if s > _WIN_THRESHOLD:
            return "shadow_3.0"
        if s < _LOSE_THRESHOLD:
            return "v1_pipeline"
        return "tie"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning_depth":   round(self.reasoning_depth, 4),
            "cost_efficiency":   round(self.cost_efficiency, 4),
            "coherence":         round(self.coherence, 4),
            "context_alignment": round(self.context_alignment, 4),
            "fatigue_impact":    round(self.fatigue_impact, 4),
            "memory_retrieval":  round(self.memory_retrieval, 4),
            "overall_score":     round(self.overall(), 4),
            "winner":            self.winner(),
        }


@dataclass
class DivergenceReport:
    session_id:       str
    question_preview: str
    timestamp:        str
    v1_trace_id:      str
    shadow_trace_id:  str
    mode_activated:   Optional[str]   # mode used in shadow run
    scores:           DivergenceScore
    v1_output:        str
    shadow_output:    str
    analysis:         str = ""        # human-readable explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id":       self.session_id,
            "question_preview": self.question_preview,
            "timestamp":        self.timestamp,
            "v1_trace_id":      self.v1_trace_id,
            "shadow_trace_id":  self.shadow_trace_id,
            "mode_activated":   self.mode_activated,
            "scores":           self.scores.to_dict(),
            "winner":           self.scores.winner(),
            "v1_output":        self.v1_output,
            "shadow_output":    self.shadow_output,
            "analysis":         self.analysis,
        }


# ── SQL ─────────────────────────────────────────────────────────────────────

_PAIRS_SQL = """
SELECT
    s.trace_id        AS shadow_trace_id,
    v.trace_id        AS v1_trace_id,
    s.session_id,
    s.question_preview,
    s.timestamp,
    s.confidence      AS s_conf,
    v.confidence      AS v_conf,
    s.tokens_used     AS s_tokens,
    v.tokens_used     AS v_tokens,
    s.fatigue_delta   AS s_fatigue,
    v.fatigue_delta   AS v_fatigue,
    s.memory_items_used AS s_items,
    v.memory_items_used AS v_items,
    s.memory_sources  AS s_sources,
    v.memory_sources  AS v_sources,
    s.mode_activated,
    s.output_preview  AS s_output,
    v.output_preview  AS v_output
FROM cognitive_traces s
JOIN cognitive_traces v
    ON  s.session_id       = v.session_id
    AND s.question_preview = v.question_preview
    AND s.source           = 'shadow_3.0'
    AND v.source           = 'v1_pipeline'
ORDER BY s.timestamp DESC
LIMIT ?
"""


class DivergenceAnalyzer:
    """
    Queries paired traces, scores them across 6 dimensions, and persists reports.
    """

    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._db = db_path

    def analyze(self, limit: int = 50) -> List[DivergenceReport]:
        """Pull unanalyzed pairs, score them, persist and return reports."""
        rows = self._fetch_pairs(limit)
        reports = [self._score_pair(r) for r in rows]
        self._persist(reports)
        return reports

    def analyze_latest(self, n: int = 5) -> List[Dict[str, Any]]:
        """Convenience: analyze the N most recent pairs and return dicts."""
        return [r.to_dict() for r in self.analyze(n)]

    def aggregate_stats(self) -> Dict[str, Any]:
        """
        High-level stats over all persisted divergence reports:
        win rates, avg scores per dimension, top winning modes.
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT overall_winner, overall_score, mode_activated, "
                    "reasoning_depth, cost_efficiency, coherence, "
                    "fatigue_impact, context_alignment, memory_retrieval "
                    "FROM trace_divergences"
                ).fetchall()
        except Exception:
            return {}

        if not rows:
            return {"total": 0}

        total       = len(rows)
        shadow_wins = sum(1 for r in rows if r[0] == "shadow_3.0")
        v1_wins     = sum(1 for r in rows if r[0] == "v1_pipeline")
        ties        = total - shadow_wins - v1_wins

        dim_avgs: Dict[str, float] = {}
        for i, dim in enumerate(
            ["overall_score", "reasoning_depth", "cost_efficiency", "coherence",
             "fatigue_impact", "context_alignment", "memory_retrieval"], start=1
        ):
            vals = [r[i] for r in rows if r[i] is not None]
            dim_avgs[dim] = round(sum(vals) / len(vals), 4) if vals else 0.0

        mode_wins: Dict[str, int] = {}
        for r in rows:
            mode = r[2] or "unknown"
            if r[0] == "shadow_3.0":
                mode_wins[mode] = mode_wins.get(mode, 0) + 1

        return {
            "total":        total,
            "shadow_wins":  shadow_wins,
            "v1_wins":      v1_wins,
            "ties":         ties,
            "shadow_win_rate": round(shadow_wins / total, 3),
            "dim_averages": dim_avgs,
            "top_winning_modes": sorted(mode_wins.items(), key=lambda x: -x[1])[:5],
        }

    # ── Internal ─────────────────────────────────────────────────────────────

    def _fetch_pairs(self, limit: int) -> List[sqlite3.Row]:
        try:
            with self._connect() as conn:
                return conn.execute(_PAIRS_SQL, (limit,)).fetchall()
        except Exception:
            return []

    def _score_pair(self, row: sqlite3.Row) -> DivergenceReport:
        s_conf    = float(row["s_conf"]    or 0)
        v_conf    = float(row["v_conf"]    or 0)
        s_tokens  = int(row["s_tokens"]    or 0)
        v_tokens  = int(row["v_tokens"]    or 0)
        s_fatigue = float(row["s_fatigue"] or 0)
        v_fatigue = float(row["v_fatigue"] or 0)
        s_items   = int(row["s_items"]     or 0)
        v_items   = int(row["v_items"]     or 0)

        s_src_count = len(json.loads(row["s_sources"] or "[]"))
        v_src_count = len(json.loads(row["v_sources"] or "[]"))

        # ── dimension scores ────────────────────────────────────────────────
        reasoning_depth = _clamp(s_conf - v_conf)

        max_tok = max(s_tokens, v_tokens, 1)
        cost_efficiency = _clamp((v_tokens - s_tokens) / max_tok)

        s_coh = s_conf / (s_fatigue + 0.01)
        v_coh = v_conf / (v_fatigue + 0.01)
        coherence = _clamp((s_coh - v_coh) / max(abs(s_coh - v_coh), 0.01) * 0.5)

        max_items = max(s_items, v_items, 1)
        context_alignment = _clamp((s_items - v_items) / max_items)

        fatigue_impact = _clamp(v_fatigue - s_fatigue)

        max_src = max(s_src_count, v_src_count, 1)
        memory_retrieval = _clamp((s_src_count - v_src_count) / max_src)

        scores = DivergenceScore(
            reasoning_depth   = reasoning_depth,
            cost_efficiency   = cost_efficiency,
            coherence         = coherence,
            context_alignment = context_alignment,
            fatigue_impact    = fatigue_impact,
            memory_retrieval  = memory_retrieval,
        )

        return DivergenceReport(
            session_id       = row["session_id"],
            question_preview = row["question_preview"] or "",
            timestamp        = row["timestamp"] or "",
            v1_trace_id      = row["v1_trace_id"],
            shadow_trace_id  = row["shadow_trace_id"],
            mode_activated   = row["mode_activated"],
            scores           = scores,
            v1_output        = row["v_output"] or "",
            shadow_output    = row["s_output"] or "",
            analysis         = _build_analysis(scores),
        )

    def _persist(self, reports: List[DivergenceReport]) -> None:
        if not reports:
            return
        try:
            with self._connect() as conn:
                conn.execute(_CREATE_DIVERGENCES_TABLE)
                for r in reports:
                    s = r.scores
                    conn.execute(_INSERT_DIVERGENCE, (
                        r.shadow_trace_id,     # use shadow_trace_id as PK
                        r.session_id, r.question_preview, r.timestamp,
                        r.v1_trace_id, r.shadow_trace_id,
                        r.mode_activated,
                        s.reasoning_depth, s.cost_efficiency, s.coherence,
                        s.context_alignment, s.fatigue_impact, s.memory_retrieval,
                        s.overall(), s.winner(),
                        r.v1_output, r.shadow_output, r.analysis,
                    ))
        except Exception:
            pass

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn


# ── SQL helpers ──────────────────────────────────────────────────────────────

_CREATE_DIVERGENCES_TABLE = """
CREATE TABLE IF NOT EXISTS trace_divergences (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_id           TEXT UNIQUE,
    session_id        TEXT,
    question_preview  TEXT,
    timestamp         TEXT,
    v1_trace_id       TEXT,
    shadow_trace_id   TEXT,
    mode_activated    TEXT,
    reasoning_depth   REAL,
    cost_efficiency   REAL,
    coherence         REAL,
    context_alignment REAL,
    fatigue_impact    REAL,
    memory_retrieval  REAL,
    overall_score     REAL,
    overall_winner    TEXT,
    v1_output         TEXT,
    shadow_output     TEXT,
    analysis          TEXT
)
"""

_INSERT_DIVERGENCE = """
INSERT OR REPLACE INTO trace_divergences (
    pair_id, session_id, question_preview, timestamp,
    v1_trace_id, shadow_trace_id, mode_activated,
    reasoning_depth, cost_efficiency, coherence,
    context_alignment, fatigue_impact, memory_retrieval,
    overall_score, overall_winner, v1_output, shadow_output, analysis
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


# ── Utilities ────────────────────────────────────────────────────────────────

def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _build_analysis(s: DivergenceScore) -> str:
    """One-line human-readable explanation of the dominant dimension."""
    dims = {
        "reasoning_depth":   s.reasoning_depth,
        "cost_efficiency":   s.cost_efficiency,
        "coherence":         s.coherence,
        "fatigue_impact":    s.fatigue_impact,
        "context_alignment": s.context_alignment,
        "memory_retrieval":  s.memory_retrieval,
    }
    dominant = max(dims, key=lambda k: abs(dims[k]))
    val      = dims[dominant]
    winner   = "shadow_3.0" if val > 0 else "v1_pipeline"
    labels   = {
        "reasoning_depth":   "mayor confianza en el razonamiento",
        "cost_efficiency":   "menor coste de tokens",
        "coherence":         "mayor coherencia relativa al coste",
        "fatigue_impact":    "menor impacto en fatiga",
        "context_alignment": "mejor alineación de contexto de memoria",
        "memory_retrieval":  "mayor amplitud de fuentes de memoria",
    }
    return f"{winner} destaca por {labels[dominant]} (Δ={val:+.3f})."


# Singleton
divergence_analyzer = DivergenceAnalyzer()
