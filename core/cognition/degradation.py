"""
StrategyDegradation — automatic penalty and recovery for cognitive strategies.

Tracks a penalty_score per (domain, mode_or_blend) in [0.0, 1.0]:

  Penalty grows   (+0.10) when rank_score < POOR_THRESHOLD  (0.35)
  Penalty shrinks (-0.08) when rank_score > GOOD_THRESHOLD  (0.65)
  consecutive_good resets on any poor result

  degraded = True  when penalty_score > DEGRADED_AT       (0.70)
  degraded = False when penalty_score < RECOVER_AT + 3
                   consecutive_good results                (auto-recovery)

Degraded strategies are excluded from TraceLearner recommendations.
They can still be activated manually or via keyword routing.

State is persisted in SQLite (strategy_degradation table) so degradation
survives restarts and accumulates across sessions.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_DB_PATH      = "memory/data/aletheia.db"
POOR_THRESHOLD  = 0.35   # rank below this → penalty++
GOOD_THRESHOLD  = 0.65   # rank above this → penalty--
DEGRADED_AT     = 0.70   # penalty above this → mode marked degraded
RECOVER_AT      = 0.30   # penalty below this + consecutive_good ≥ 3 → recovery
PENALTY_STEP    = 0.10
RECOVERY_STEP   = 0.08
CONSECUTIVE_GOOD_NEEDED = 3

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS strategy_degradation (
    domain          TEXT NOT NULL,
    mode_or_blend   TEXT NOT NULL,
    penalty_score   REAL DEFAULT 0.0,
    consecutive_good INTEGER DEFAULT 0,
    last_updated    TEXT,
    PRIMARY KEY (domain, mode_or_blend)
)
"""


class StrategyDegradation:

    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._db = db_path
        self._init()

    def _init(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(_CREATE_TABLE)
        except Exception:
            pass

    # ── Core API ─────────────────────────────────────────────────────────────

    def record_result(
        self,
        domain: str,
        mode_or_blend: str,
        rank_score: float,
    ) -> None:
        """
        Update penalty/recovery for one (domain, mode_or_blend) observation.
        Best-effort — never raises.
        """
        try:
            row = self._get(domain, mode_or_blend)
            penalty  = row["penalty_score"]       if row else 0.0
            consec   = row["consecutive_good"]    if row else 0

            if rank_score < POOR_THRESHOLD:
                penalty = min(1.0, penalty + PENALTY_STEP)
                consec  = 0
            elif rank_score > GOOD_THRESHOLD:
                penalty = max(0.0, penalty - RECOVERY_STEP)
                consec  += 1
            # neutral: no change

            self._upsert(domain, mode_or_blend, penalty, consec)
        except Exception:
            pass

    def is_degraded(self, domain: str, mode_or_blend: str) -> bool:
        """True if this strategy's penalty_score exceeds DEGRADED_AT."""
        try:
            row = self._get(domain, mode_or_blend)
            if not row:
                return False
            penalty = float(row["penalty_score"] or 0)
            consec  = int(row["consecutive_good"] or 0)
            # Auto-recovery: sufficiently good recent history
            if penalty < RECOVER_AT and consec >= CONSECUTIVE_GOOD_NEEDED:
                return False
            return penalty >= DEGRADED_AT
        except Exception:
            return False

    def all_degraded(self) -> List[Dict[str, Any]]:
        """All (domain, mode_or_blend) pairs currently degraded."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM strategy_degradation WHERE penalty_score >= ?",
                    (DEGRADED_AT,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def all_entries(self) -> List[Dict[str, Any]]:
        """Full penalty table for monitoring."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM strategy_degradation ORDER BY penalty_score DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def reset(self, domain: Optional[str] = None, mode_or_blend: Optional[str] = None) -> int:
        """
        Reset penalty scores. Pass both args to reset one entry,
        one arg to reset by domain or mode, no args to reset all.
        Returns number of rows affected.
        """
        try:
            with self._connect() as conn:
                if domain and mode_or_blend:
                    c = conn.execute(
                        "DELETE FROM strategy_degradation WHERE domain=? AND mode_or_blend=?",
                        (domain, mode_or_blend),
                    )
                elif domain:
                    c = conn.execute(
                        "DELETE FROM strategy_degradation WHERE domain=?", (domain,)
                    )
                elif mode_or_blend:
                    c = conn.execute(
                        "DELETE FROM strategy_degradation WHERE mode_or_blend=?",
                        (mode_or_blend,),
                    )
                else:
                    c = conn.execute("DELETE FROM strategy_degradation")
            return c.rowcount
        except Exception:
            return 0

    # ── Internal ─────────────────────────────────────────────────────────────

    def _get(self, domain: str, mode_or_blend: str) -> Optional[sqlite3.Row]:
        try:
            with self._connect() as conn:
                return conn.execute(
                    "SELECT * FROM strategy_degradation WHERE domain=? AND mode_or_blend=?",
                    (domain, mode_or_blend),
                ).fetchone()
        except Exception:
            return None

    def _upsert(
        self,
        domain: str,
        mode_or_blend: str,
        penalty: float,
        consec: int,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO strategy_degradation
                    (domain, mode_or_blend, penalty_score, consecutive_good, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(domain, mode_or_blend) DO UPDATE SET
                    penalty_score    = excluded.penalty_score,
                    consecutive_good = excluded.consecutive_good,
                    last_updated     = excluded.last_updated
                """,
                (domain, mode_or_blend, round(penalty, 4), consec, ts),
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn


# Singleton
strategy_degradation = StrategyDegradation()
