"""
PatternDetector — heuristic SQL analysis over cognitive_traces + memory_nodes.

No LLM used. Pure SQL aggregation run after consolidation (step 6).
Produces CognitivePattern records stored in the cognitive_patterns table.
"""
from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_DB = "memory/data/aletheia.db"

_CREATE_PATTERNS_TABLE = """
CREATE TABLE IF NOT EXISTS cognitive_patterns (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL,
    title       TEXT NOT NULL,
    description TEXT,
    relevance   REAL DEFAULT 0.5,
    domain      TEXT,
    detected_at TEXT NOT NULL,
    shown       INTEGER DEFAULT 0
);
"""

# Icons per pattern type
_ICONS: dict[str, str] = {
    "recurring_topic":    "🔁",
    "dominant_mode":      "🧠",
    "new_concept":        "✨",
    "cross_domain_link":  "🔗",
    "high_fatigue_session": "⚡",
    "low_confidence_zone":  "❓",
}


@dataclass
class CognitivePattern:
    id:           str
    type:         str
    title:        str
    description:  str
    relevance:    float
    domain:       str | None
    detected_at:  str
    shown:        bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id":          self.id,
            "type":        self.type,
            "icon":        _ICONS.get(self.type, "◇"),
            "title":       self.title,
            "description": self.description,
            "relevance":   self.relevance,
            "domain":      self.domain,
            "detected_at": self.detected_at,
            "shown":       self.shown,
        }


class PatternDetector:

    def __init__(self, db_path: str = _DB) -> None:
        self._db = db_path
        self._init()

    def _connect(self) -> sqlite3.Connection:
        Path(self._db).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(_CREATE_PATTERNS_TABLE)
                conn.commit()
        except Exception:
            pass

    # ── Detection ─────────────────────────────────────────────────────────

    def detect(self, since_hours: int = 24) -> list[CognitivePattern]:
        """Run all heuristics and persist new patterns. Returns list found."""
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=since_hours)
        ).isoformat()

        patterns: list[CognitivePattern] = []
        patterns += self._recurring_topics(cutoff)
        patterns += self._dominant_mode(cutoff)
        patterns += self._new_concepts(cutoff)
        patterns += self._cross_domain_links(cutoff)
        patterns += self._high_fatigue_sessions(cutoff)
        patterns += self._low_confidence_zones(cutoff)

        if patterns:
            self._save(patterns)
        return patterns

    def _recurring_topics(self, cutoff: str) -> list[CognitivePattern]:
        """Domain that appears ≥3 times in traces → recurring conversation topic."""
        sql = """
            SELECT domain, COUNT(*) AS c
            FROM cognitive_traces
            WHERE timestamp >= ? AND domain IS NOT NULL AND domain != ''
            GROUP BY domain
            HAVING c >= 3
            ORDER BY c DESC
            LIMIT 5
        """
        results = []
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, (cutoff,)).fetchall()
            for row in rows:
                domain, count = row["domain"], row["c"]
                relevance = min(1.0, count / 10)
                results.append(CognitivePattern(
                    id=str(uuid.uuid4()),
                    type="recurring_topic",
                    title=f"Tema recurrente: {domain}",
                    description=f"Has hablado de '{domain}' {count} veces en las últimas horas. Es un área de atención activa.",
                    relevance=round(relevance, 2),
                    domain=domain,
                    detected_at=datetime.now(timezone.utc).isoformat(),
                ))
        except Exception:
            pass
        return results

    def _dominant_mode(self, cutoff: str) -> list[CognitivePattern]:
        """Mode used most frequently → signals Aletheia's current cognitive style."""
        sql = """
            SELECT mode_activated, COUNT(*) AS c
            FROM cognitive_traces
            WHERE timestamp >= ? AND mode_activated IS NOT NULL AND mode_activated != ''
            GROUP BY mode_activated
            ORDER BY c DESC
            LIMIT 1
        """
        results = []
        try:
            with self._connect() as conn:
                row = conn.execute(sql, (cutoff,)).fetchone()
            if row and row["c"] >= 2:
                mode, count = row["mode_activated"], row["c"]
                results.append(CognitivePattern(
                    id=str(uuid.uuid4()),
                    type="dominant_mode",
                    title=f"Modo dominante: {mode}",
                    description=f"El modo '{mode}' se activó {count} veces. Tu patrón de consultas favorece este estilo cognitivo.",
                    relevance=round(min(1.0, count / 8), 2),
                    domain=None,
                    detected_at=datetime.now(timezone.utc).isoformat(),
                ))
        except Exception:
            pass
        return results

    def _new_concepts(self, cutoff: str) -> list[CognitivePattern]:
        """Memory nodes created recently → new knowledge ingested."""
        sql = """
            SELECT COUNT(*) AS c
            FROM memory_nodes
            WHERE created_at >= ? AND active = 1
        """
        results = []
        try:
            with self._connect() as conn:
                row = conn.execute(sql, (cutoff,)).fetchone()
            count = row["c"] if row else 0
            if count > 0:
                results.append(CognitivePattern(
                    id=str(uuid.uuid4()),
                    type="new_concept",
                    title=f"{count} concepto{'s' if count != 1 else ''} nuevo{'s' if count != 1 else ''} aprendido{'s' if count != 1 else ''}",
                    description=f"El grafo semántico creció {count} nodo{'s' if count != 1 else ''} en las últimas {cutoff[:10].split('T')[0]} horas. La base de conocimiento se amplió.",
                    relevance=round(min(1.0, count / 20), 2),
                    domain=None,
                    detected_at=datetime.now(timezone.utc).isoformat(),
                ))
        except Exception:
            pass
        return results

    def _cross_domain_links(self, cutoff: str) -> list[CognitivePattern]:
        """Topics that appeared across ≥2 different domains → cross-domain insight."""
        sql = """
            SELECT question_preview, COUNT(DISTINCT domain) AS domains
            FROM cognitive_traces
            WHERE timestamp >= ? AND question_preview IS NOT NULL
                AND domain IS NOT NULL AND domain != ''
            GROUP BY question_preview
            HAVING domains >= 2
            ORDER BY domains DESC
            LIMIT 3
        """
        results = []
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, (cutoff,)).fetchall()
            for row in rows:
                preview = (row["question_preview"] or "")[:60]
                domains = row["domains"]
                results.append(CognitivePattern(
                    id=str(uuid.uuid4()),
                    type="cross_domain_link",
                    title="Conexión entre dominios detectada",
                    description=f"«{preview}…» apareció en {domains} dominios distintos — indica pensamiento transversal o una pregunta con múltiples ángulos.",
                    relevance=round(min(1.0, domains / 4), 2),
                    domain=None,
                    detected_at=datetime.now(timezone.utc).isoformat(),
                ))
        except Exception:
            pass
        return results

    def _high_fatigue_sessions(self, cutoff: str) -> list[CognitivePattern]:
        """Sessions with cumulative fatigue_delta > 0.4 → cognitive overload signal."""
        sql = """
            SELECT session_id, SUM(fatigue_delta) AS total_fatigue, COUNT(*) AS calls
            FROM cognitive_traces
            WHERE timestamp >= ? AND fatigue_delta IS NOT NULL
            GROUP BY session_id
            HAVING total_fatigue > 0.4
            ORDER BY total_fatigue DESC
            LIMIT 3
        """
        results = []
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, (cutoff,)).fetchall()
            for row in rows:
                fatigue = round(row["total_fatigue"] * 100)
                calls = row["calls"]
                results.append(CognitivePattern(
                    id=str(uuid.uuid4()),
                    type="high_fatigue_session",
                    title=f"Sesión de alta carga cognitiva ({fatigue}%)",
                    description=f"Una sesión acumuló {fatigue}% de fatiga en {calls} llamadas. Considera dividir sesiones largas o usar el modo diferido.",
                    relevance=round(min(1.0, row["total_fatigue"] / 0.8), 2),
                    domain=None,
                    detected_at=datetime.now(timezone.utc).isoformat(),
                ))
        except Exception:
            pass
        return results

    def _low_confidence_zones(self, cutoff: str) -> list[CognitivePattern]:
        """Domains with avg confidence < 0.4 → knowledge gaps."""
        sql = """
            SELECT domain, AVG(confidence) AS avg_conf, COUNT(*) AS c
            FROM cognitive_traces
            WHERE timestamp >= ? AND confidence IS NOT NULL
                AND domain IS NOT NULL AND domain != ''
            GROUP BY domain
            HAVING avg_conf < 0.4 AND c >= 2
            ORDER BY avg_conf ASC
            LIMIT 3
        """
        results = []
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, (cutoff,)).fetchall()
            for row in rows:
                domain = row["domain"]
                conf = round(row["avg_conf"] * 100)
                results.append(CognitivePattern(
                    id=str(uuid.uuid4()),
                    type="low_confidence_zone",
                    title=f"Zona de baja confianza: {domain}",
                    description=f"Confianza media del {conf}% en '{domain}'. Considera añadir documentos o contexto para mejorar las respuestas en este dominio.",
                    relevance=round(1.0 - row["avg_conf"], 2),
                    domain=domain,
                    detected_at=datetime.now(timezone.utc).isoformat(),
                ))
        except Exception:
            pass
        return results

    # ── Persistence ───────────────────────────────────────────────────────

    def _save(self, patterns: list[CognitivePattern]) -> None:
        try:
            with self._connect() as conn:
                conn.executemany(
                    """INSERT OR REPLACE INTO cognitive_patterns
                       (id, type, title, description, relevance, domain, detected_at, shown)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
                    [
                        (p.id, p.type, p.title, p.description, p.relevance, p.domain, p.detected_at)
                        for p in patterns
                    ],
                )
                conn.commit()
        except Exception:
            pass

    # ── Read API ──────────────────────────────────────────────────────────

    def get_patterns(
        self, limit: int = 20, unread_only: bool = False
    ) -> list[dict[str, Any]]:
        where = "WHERE shown = 0" if unread_only else ""
        sql = f"""
            SELECT * FROM cognitive_patterns
            {where}
            ORDER BY detected_at DESC
            LIMIT ?
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, (limit,)).fetchall()
            return [
                CognitivePattern(
                    id=r["id"], type=r["type"], title=r["title"],
                    description=r["description"], relevance=r["relevance"],
                    domain=r["domain"], detected_at=r["detected_at"],
                    shown=bool(r["shown"]),
                ).to_dict()
                for r in rows
            ]
        except Exception:
            return []

    def mark_read(self, pattern_id: str) -> bool:
        try:
            with self._connect() as conn:
                n = conn.execute(
                    "UPDATE cognitive_patterns SET shown = 1 WHERE id = ?",
                    (pattern_id,),
                ).rowcount
                conn.commit()
            return n > 0
        except Exception:
            return False

    def mark_all_read(self) -> int:
        try:
            with self._connect() as conn:
                n = conn.execute(
                    "UPDATE cognitive_patterns SET shown = 1 WHERE shown = 0"
                ).rowcount
                conn.commit()
            return n
        except Exception:
            return 0

    def unread_count(self) -> int:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM cognitive_patterns WHERE shown = 0"
                ).fetchone()
            return row[0] if row else 0
        except Exception:
            return 0


# Singleton
pattern_detector = PatternDetector()
