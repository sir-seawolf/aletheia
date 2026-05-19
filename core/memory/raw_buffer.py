"""
RawBuffer — cola diferida de contenido pendiente de consolidación.

Durante conversaciones activas, el sistema escribe aquí de forma ligera
(O(1), sin procesamiento semántico). La ConsolidationEngine drena esta
cola durante el "sueño cognitivo" y procesa cada entrada en profundidad.

Tabla SQLite: consolidation_queue (comparte memory/data/aletheia.db)
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

_DB_PATH = Path("memory/data/aletheia.db")
_lock    = threading.Lock()

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS consolidation_queue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    domain      TEXT    NOT NULL,
    content     TEXT    NOT NULL DEFAULT '{}',
    session_id  TEXT    NOT NULL DEFAULT 'local',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    processed   INTEGER NOT NULL DEFAULT 0,
    processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_cq_processed ON consolidation_queue(processed);
"""


def _conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(_DB_PATH), timeout=10)
    c.row_factory = sqlite3.Row
    return c


def _init() -> None:
    with _conn() as c:
        c.executescript(_INIT_SQL)


class RawBuffer:
    """Lightweight append-only queue for deferred consolidation."""

    def __init__(self) -> None:
        _init()

    # ── Write ──────────────────────────────────────────────────────────────

    def append(
        self,
        domain: str,
        content: dict[str, Any] | str,
        session_id: str = "local",
    ) -> None:
        """Enqueue one item for later consolidation. Never raises."""
        try:
            payload = json.dumps(content, ensure_ascii=False) if isinstance(content, dict) else str(content)[:2000]
            with _lock, _conn() as c:
                c.execute(
                    "INSERT INTO consolidation_queue (domain, content, session_id) VALUES (?, ?, ?)",
                    (domain, payload, session_id),
                )
        except Exception:
            pass

    # ── Read ───────────────────────────────────────────────────────────────

    def count(self) -> int:
        """Number of unprocessed items in the queue."""
        try:
            with _conn() as c:
                return c.execute("SELECT COUNT(*) FROM consolidation_queue WHERE processed = 0").fetchone()[0]
        except Exception:
            return 0

    def drain(self, limit: int = 500) -> list[dict[str, Any]]:
        """
        Return up to *limit* unprocessed items and mark them as processed.
        Thread-safe — won't return the same item twice.
        """
        rows: list[dict] = []
        try:
            with _lock, _conn() as c:
                raw = c.execute(
                    "SELECT id, domain, content, session_id, created_at "
                    "FROM consolidation_queue WHERE processed = 0 ORDER BY id LIMIT ?",
                    (limit,),
                ).fetchall()
                if not raw:
                    return []
                ids = [r["id"] for r in raw]
                now = datetime.now().isoformat(timespec="seconds")
                c.execute(
                    f"UPDATE consolidation_queue SET processed = 1, processed_at = ? WHERE id IN ({','.join('?' * len(ids))})",
                    [now, *ids],
                )
                rows = [
                    {
                        "id":         r["id"],
                        "domain":     r["domain"],
                        "content":    json.loads(r["content"]),
                        "session_id": r["session_id"],
                        "created_at": r["created_at"],
                    }
                    for r in raw
                ]
        except Exception:
            pass
        return rows

    def stats(self) -> dict[str, Any]:
        """Return queue statistics."""
        try:
            with _conn() as c:
                total     = c.execute("SELECT COUNT(*) FROM consolidation_queue").fetchone()[0]
                pending   = c.execute("SELECT COUNT(*) FROM consolidation_queue WHERE processed = 0").fetchone()[0]
                last_row  = c.execute(
                    "SELECT processed_at FROM consolidation_queue WHERE processed = 1 ORDER BY processed_at DESC LIMIT 1"
                ).fetchone()
                last_proc = last_row["processed_at"] if last_row else None
            return {"total": total, "pending": pending, "last_processed": last_proc}
        except Exception:
            return {"total": 0, "pending": 0, "last_processed": None}


# Singleton
raw_buffer = RawBuffer()
