"""
Tests for core/cognition/pattern_detector.py
Uses an isolated DB per test — no production data touched.
"""
import pytest
import sqlite3
from datetime import datetime, timedelta, timezone


def _seed_traces(db_path: str, domain: str, count: int, mode: str = "ANALYTICAL",
                 fatigue_delta: float = 0.05, confidence: float = 0.7,
                 same_session: bool = False):
    """Insert fake cognitive_traces rows for testing pattern detection."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cognitive_traces (
            trace_id TEXT PRIMARY KEY, session_id TEXT, timestamp TEXT,
            source TEXT, domain TEXT, question_preview TEXT,
            mode_activated TEXT, observer_routing_reason TEXT,
            provider_used TEXT, model_tier TEXT, routing_reasoning TEXT,
            memory_sources TEXT, memory_items_used INTEGER,
            fatigue_before REAL, fatigue_after REAL, fatigue_delta REAL,
            tokens_used INTEGER, latency_ms REAL, confidence REAL,
            output_preview TEXT, error TEXT
        )
    """)
    import uuid
    now = datetime.now(timezone.utc)
    shared_session = str(uuid.uuid4())
    for i in range(count):
        ts = (now - timedelta(hours=1)).isoformat()
        session = shared_session if same_session else f"session_{i}"
        conn.execute(
            "INSERT OR IGNORE INTO cognitive_traces VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), session, ts, "v3", domain,
             f"pregunta sobre {domain}", mode, None, "ollama", "local", None,
             "[]", 0, 0.1, 0.1 + fatigue_delta, fatigue_delta,
             100, 300.0, confidence, "respuesta ok", None)
        )
    conn.commit()
    conn.close()


def _seed_memory_nodes(db_path: str, count: int):
    """Insert fake memory_nodes rows."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_nodes (
            id TEXT PRIMARY KEY, type TEXT, title TEXT, content TEXT,
            meta TEXT, created_at TEXT, updated_at TEXT,
            valid_from TEXT, valid_to TEXT, version INTEGER, active INTEGER
        )
    """)
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    for i in range(count):
        conn.execute(
            "INSERT OR IGNORE INTO memory_nodes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), "concept", f"concepto_{i}", f"contenido {i}",
             None, now, now, None, None, 1, 1)
        )
    conn.commit()
    conn.close()


class TestPatternDetector:

    def test_init_creates_table(self, pattern_det):
        # Table should exist after __init__
        conn = sqlite3.connect(pattern_det._db)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        assert "cognitive_patterns" in tables

    def test_no_patterns_on_empty_db(self, pattern_det):
        patterns = pattern_det.detect(since_hours=24)
        assert isinstance(patterns, list)
        assert len(patterns) == 0

    def test_recurring_topic_detected(self, pattern_det):
        _seed_traces(pattern_det._db, domain="finanzas", count=5)
        patterns = pattern_det.detect(since_hours=24)
        types = [p.type for p in patterns]
        assert "recurring_topic" in types

    def test_recurring_topic_domain_matches(self, pattern_det):
        _seed_traces(pattern_det._db, domain="salud", count=4)
        patterns = pattern_det.detect(since_hours=24)
        recurring = [p for p in patterns if p.type == "recurring_topic"]
        assert any("salud" in p.title.lower() for p in recurring)

    def test_dominant_mode_detected(self, pattern_det):
        _seed_traces(pattern_det._db, domain="tecnologia", count=3, mode="KRONOS")
        patterns = pattern_det.detect(since_hours=24)
        types = [p.type for p in patterns]
        assert "dominant_mode" in types

    def test_new_concept_detected(self, pattern_det):
        _seed_memory_nodes(pattern_det._db, count=3)
        patterns = pattern_det.detect(since_hours=24)
        types = [p.type for p in patterns]
        assert "new_concept" in types

    def test_high_fatigue_session_detected(self, pattern_det):
        _seed_traces(pattern_det._db, domain="trabajo", count=5,
                     fatigue_delta=0.12, same_session=True)  # same session → 5×0.12=0.60 > 0.4
        patterns = pattern_det.detect(since_hours=24)
        types = [p.type for p in patterns]
        assert "high_fatigue_session" in types

    def test_low_confidence_zone_detected(self, pattern_det):
        _seed_traces(pattern_det._db, domain="legal", count=3, confidence=0.25)
        patterns = pattern_det.detect(since_hours=24)
        types = [p.type for p in patterns]
        assert "low_confidence_zone" in types

    def test_relevance_between_0_and_1(self, pattern_det):
        _seed_traces(pattern_det._db, domain="relaciones", count=4)
        patterns = pattern_det.detect(since_hours=24)
        for p in patterns:
            assert 0.0 <= p.relevance <= 1.0

    def test_patterns_saved_to_db(self, pattern_det):
        _seed_traces(pattern_det._db, domain="creatividad", count=4)
        pattern_det.detect(since_hours=24)
        saved = pattern_det.get_patterns()
        assert len(saved) > 0
        assert all("id" in p and "title" in p and "relevance" in p for p in saved)

    def test_get_patterns_unread_only(self, pattern_det):
        _seed_traces(pattern_det._db, domain="objetivos", count=4)
        pattern_det.detect(since_hours=24)
        unread = pattern_det.get_patterns(unread_only=True)
        assert all(not p["shown"] for p in unread)

    def test_mark_read(self, pattern_det):
        _seed_traces(pattern_det._db, domain="aprendizaje", count=4)
        pattern_det.detect(since_hours=24)
        patterns = pattern_det.get_patterns()
        assert len(patterns) > 0
        pid = patterns[0]["id"]
        ok = pattern_det.mark_read(pid)
        assert ok
        updated = pattern_det.get_patterns()
        marked = next(p for p in updated if p["id"] == pid)
        assert marked["shown"] is True

    def test_mark_all_read(self, pattern_det):
        _seed_traces(pattern_det._db, domain="carrera", count=4)
        pattern_det.detect(since_hours=24)
        n = pattern_det.mark_all_read()
        assert n > 0
        assert pattern_det.unread_count() == 0

    def test_unread_count(self, pattern_det):
        _seed_traces(pattern_det._db, domain="negocios", count=4)
        pattern_det.detect(since_hours=24)
        count_before = pattern_det.unread_count()
        assert count_before > 0
        pattern_det.mark_all_read()
        assert pattern_det.unread_count() == 0

    def test_to_dict_has_icon(self, pattern_det):
        _seed_traces(pattern_det._db, domain="deportes", count=4)
        patterns = pattern_det.detect(since_hours=24)
        for p in patterns:
            d = p.to_dict()
            assert "icon" in d
            assert len(d["icon"]) > 0


class TestPatternsAPI:

    def test_patterns_endpoint_returns_list(self, client):
        r = client.get("/api/consolidation/patterns")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_mark_all_read_endpoint(self, client):
        r = client.post("/api/consolidation/patterns/mark_all_read")
        assert r.status_code == 200
        assert "marked" in r.json()

    def test_unread_count_endpoint(self, client):
        r = client.get("/api/consolidation/patterns/unread_count")
        assert r.status_code == 200
        data = r.json()
        assert "count" in data
        assert isinstance(data["count"], int)

    def test_detect_endpoint(self, client):
        r = client.post("/api/consolidation/patterns/detect?since_hours=48")
        assert r.status_code == 200
        data = r.json()
        assert "found" in data
        assert "patterns" in data
        assert isinstance(data["patterns"], list)
