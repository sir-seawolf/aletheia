"""HestiaMemory — Persistent storage for HESTIA strategic observer.

STATUS: IMPLEMENTED (Hestia v1)
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path("memory/data/hestia.db")

_INITIAL_GOAL = {
    "title": "Clase media España",
    "description": (
        "Alcanzar ingresos de clase media en España. "
        "Referencia actual: ~30.000€/año brutos. "
        "Plazo orientativo: 2 años desde creación. "
        "Este objetivo puede evolucionar en forma, cifra y plazo — "
        "pero la dirección no cambia."
    ),
    "target_value": 30000.0,
    "target_unit": "€/año brutos",
    "current_value": 0.0,
    "deadline": None,
    "priority": 1,
    "active": 1,
    "notes": None,
}


class HestiaMemory:

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def _conn(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS strategic_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    target_value REAL,
                    target_unit TEXT,
                    current_value REAL DEFAULT 0,
                    deadline TEXT,
                    priority INTEGER DEFAULT 1,
                    active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS strategic_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    session_id TEXT,
                    domain TEXT,
                    summary TEXT,
                    strategic_relevance REAL,
                    flags TEXT
                );

                CREATE TABLE IF NOT EXISTS hestia_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    hours_analyzed INTEGER,
                    goal_ids TEXT,
                    analysis TEXT,
                    alignment_score REAL,
                    verdict TEXT
                );

                CREATE TABLE IF NOT EXISTS hestia_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    updated_at TEXT
                );
            """)
            count = conn.execute("SELECT COUNT(*) FROM strategic_goals").fetchone()[0]
            if count == 0:
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    """
                    INSERT INTO strategic_goals
                    (title, description, target_value, target_unit, current_value,
                     deadline, priority, active, created_at, updated_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        _INITIAL_GOAL["title"],
                        _INITIAL_GOAL["description"],
                        _INITIAL_GOAL["target_value"],
                        _INITIAL_GOAL["target_unit"],
                        _INITIAL_GOAL["current_value"],
                        _INITIAL_GOAL["deadline"],
                        _INITIAL_GOAL["priority"],
                        _INITIAL_GOAL["active"],
                        now, now,
                        _INITIAL_GOAL["notes"],
                    ),
                )

    # ── goals ────────────────────────────────────────────────────────────────

    def save_goal(self, goal: Dict[str, Any]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO strategic_goals
                (title, description, target_value, target_unit, current_value,
                 deadline, priority, active, created_at, updated_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal.get("title"), goal.get("description"),
                    goal.get("target_value"), goal.get("target_unit"),
                    goal.get("current_value", 0.0),
                    goal.get("deadline"), goal.get("priority", 1),
                    goal.get("active", 1),
                    now, now,
                    goal.get("notes"),
                ),
            )
            return cur.lastrowid

    def update_goal(self, goal_id: int, updates: Dict[str, Any]) -> None:
        allowed = {
            "title", "description", "target_value", "target_unit",
            "current_value", "deadline", "priority", "active", "notes",
        }
        fields = {k: v for k, v in updates.items() if k in allowed}
        if not fields:
            return
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [goal_id]
        with self._conn() as conn:
            conn.execute(
                f"UPDATE strategic_goals SET {set_clause} WHERE id = ?", values
            )

    def get_active_goals(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM strategic_goals WHERE active = 1 ORDER BY priority"
            ).fetchall()
            return [dict(r) for r in rows]

    def deactivate_goal(self, goal_id: int) -> None:
        self.update_goal(goal_id, {"active": 0})

    # ── observations ─────────────────────────────────────────────────────────

    def save_observation(self, obs: Dict[str, Any]) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO strategic_observations
                (timestamp, session_id, domain, summary, strategic_relevance, flags)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    obs.get("timestamp"), obs.get("session_id"),
                    obs.get("domain"), obs.get("summary"),
                    obs.get("strategic_relevance"), obs.get("flags"),
                ),
            )
            return cur.lastrowid

    def get_observations(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM strategic_observations
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                """,
                (cutoff,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── analyses ─────────────────────────────────────────────────────────────

    def save_analysis(self, analysis: Dict[str, Any]) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO hestia_analyses
                (timestamp, hours_analyzed, goal_ids, analysis, alignment_score, verdict)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis.get("timestamp"),
                    analysis.get("hours_analyzed"),
                    json.dumps(analysis.get("goal_ids", [])),
                    json.dumps(analysis.get("analysis", {})),
                    analysis.get("alignment_score"),
                    analysis.get("verdict"),
                ),
            )
            return cur.lastrowid

    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM hestia_analyses ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["analysis"] = json.loads(result["analysis"] or "{}")
            result["goal_ids"] = json.loads(result["goal_ids"] or "[]")
            return result

    def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM hestia_analyses ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            results = []
            for row in rows:
                r = dict(row)
                r["analysis"] = json.loads(r["analysis"] or "{}")
                r["goal_ids"] = json.loads(r["goal_ids"] or "[]")
                results.append(r)
            return results

    # ── profile ──────────────────────────────────────────────────────────────

    def save_profile_key(self, key: str, value: Any) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO hestia_profile (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE
                SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, json.dumps(value), now),
            )

    def get_profile_key(self, key: str) -> Optional[Any]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM hestia_profile WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None
            return json.loads(row["value"])
