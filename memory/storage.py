"""Almacenamiento simple en SQLite para memoria."""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Optional

from config import MEMORY_DB_PATH


def init_db():
    """Inicializa la tabla de memoria si no existe."""
    os.makedirs(os.path.dirname(MEMORY_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        content TEXT,
        domain TEXT,
        confidence REAL,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT,
        preference TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interaction_id TEXT,
        rating INTEGER,
        signals TEXT,
        comment TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        timestamp TEXT,
        agent TEXT,
        stage TEXT,
        event_type TEXT,
        payload TEXT,
        confidence REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_nodes (
        id TEXT PRIMARY KEY,
        type TEXT,
        title TEXT,
        content TEXT,
        meta TEXT,
        created_at TEXT,
        updated_at TEXT,
        valid_from TEXT,
        valid_to TEXT,
        version INTEGER,
        active INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_refs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT,
        target_id TEXT,
        relation TEXT,
        weight REAL
    )
    """)

    conn.commit()
    conn.close()


def save_memory(item: MemoryItem) -> int:
    """Guarda un item en la base de datos y retorna su id."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO memory (type, content, domain, confidence, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        item.type,
        item.content,
        item.domain,
        item.confidence,
        item.created_at.isoformat(),
    ))

    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id if item_id is not None else -1


def get_by_domain(domain: str, limit: int = 20) -> List[MemoryItem]:
    """Recupera los últimos items de memoria para un dominio dado."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, type, content, domain, confidence, created_at
    FROM memory
    WHERE domain = ?
    ORDER BY created_at DESC
    LIMIT ?
    """, (domain, limit))

    rows = cursor.fetchall()
    conn.close()

    return [
        MemoryItem(
            id=row[0],
            type=row[1],
            content=row[2],
            domain=row[3],
            confidence=row[4],
            created_at=datetime.fromisoformat(row[5]),
        )
        for row in rows
    ]


def get_all(limit: int = 100) -> List[MemoryItem]:
    """Recupera los últimos items de memoria sin filtrar por dominio."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, type, content, domain, confidence, created_at
    FROM memory
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [
        MemoryItem(
            id=row[0],
            type=row[1],
            content=row[2],
            domain=row[3],
            confidence=row[4],
            created_at=datetime.fromisoformat(row[5]),
        )
        for row in rows
    ]


def save_preference(domain: str, preference: str) -> int:
    """Guarda una preferencia observada para un dominio."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO profile_preferences (domain, preference, created_at)
    VALUES (?, ?, ?)
    """, (domain, preference, datetime.now().isoformat()))

    conn.commit()
    pref_id = cursor.lastrowid
    conn.close()
    return pref_id if pref_id is not None else -1


def get_preferences_by_domain(domain: str, limit: int = 10) -> List[str]:
    """Recupera las preferencias observadas más recientes para un dominio."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT preference FROM profile_preferences
    WHERE domain = ?
    ORDER BY created_at DESC
    LIMIT ?
    """, (domain, limit))

    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def save_feedback(item: FeedbackItem) -> int:
    """Guarda un feedback en la base de datos y retorna su id."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO feedback (interaction_id, rating, signals, comment, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        item.interaction_id,
        item.rating,
        json.dumps(item.signals),
        item.comment,
        item.created_at.isoformat(),
    ))

    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id if item_id is not None else -1


def get_feedback_by_interaction(interaction_id: str) -> List[FeedbackItem]:
    """Recupera feedback para una interacción específica."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, interaction_id, rating, signals, comment, created_at
    FROM feedback
    WHERE interaction_id = ?
    ORDER BY created_at DESC
    """, (interaction_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        FeedbackItem(
            id=row[0],
            interaction_id=row[1],
            rating=row[2],
            signals=json.loads(row[3]) if row[3] else {},
            comment=row[4],
            created_at=datetime.fromisoformat(row[5]),
        )
        for row in rows
    ]


def get_recent_feedback_signals(signal_key: str, min_count: int = 3) -> List[FeedbackItem]:
    """Recupera feedback recientes donde una señal específica está activa.

    Útil para detectar patrones repetidos antes de aplicar ajustes.
    """
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, interaction_id, rating, signals, comment, created_at
    FROM feedback
    ORDER BY created_at DESC
    LIMIT 50
    """)

    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        signals = json.loads(row[3]) if row[3] else {}
        if signals.get(signal_key, False):
            items.append(FeedbackItem(
                id=row[0],
                interaction_id=row[1],
                rating=row[2],
                signals=signals,
                comment=row[4],
                created_at=datetime.fromisoformat(row[5]),
            ))

    return items[:min_count]


def save_session_event(event: dict) -> int:
    """Guarda un evento cognitivo asociado a una sesión."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO session_events (
        session_id, timestamp, agent, stage, event_type, payload, confidence
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event.get("session_id", "local"),
        event.get("timestamp", datetime.now().isoformat()),
        event.get("agent", "unknown"),
        event.get("stage", "unknown"),
        event.get("event_type", "unknown"),
        json.dumps(event.get("payload", {})),
        float(event.get("confidence", 0.0)),
    ))

    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id if row_id is not None else -1


def get_session_events(session_id: str, limit: int = 1000) -> List[dict]:
    """Recupera historial de eventos por sesión, ordenados por inserción."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT session_id, timestamp, agent, stage, event_type, payload, confidence
    FROM session_events
    WHERE session_id = ?
    ORDER BY id ASC
    LIMIT ?
    """, (session_id, limit))

    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        events.append({
            "session_id": row[0],
            "timestamp": row[1],
            "agent": row[2],
            "stage": row[3],
            "event_type": row[4],
            "payload": json.loads(row[5]) if row[5] else {},
            "confidence": row[6],
        })
    return events


def save_memory_node(node: MemoryNode) -> None:
    """Guarda o reemplaza un MemoryNode con sus referencias."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO memory_nodes
    (id, type, title, content, meta, created_at, updated_at, valid_from, valid_to, version, active)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        node.id,
        node.type,
        node.title,
        json.dumps(node.content),
        json.dumps({
            "source": node.meta.source,
            "confidence": node.meta.confidence,
            "tags": node.meta.tags,
            "emotion": node.meta.emotion,
            "domain": node.meta.domain,
        }),
        node.created_at.isoformat(),
        node.updated_at.isoformat(),
        node.valid_from.isoformat() if node.valid_from else None,
        node.valid_to.isoformat() if node.valid_to else None,
        node.version,
        1 if node.active else 0,
    ))

    cursor.execute("DELETE FROM memory_refs WHERE source_id = ?", (node.id,))
    for ref in node.refs:
        cursor.execute("""
        INSERT INTO memory_refs (source_id, target_id, relation, weight)
        VALUES (?, ?, ?, ?)
        """, (node.id, ref.target_id, ref.relation, ref.weight))

    conn.commit()
    conn.close()


def get_memory_nodes_by_domain(domain: str, limit: int = 50) -> List[MemoryNode]:
    """Recupera nodos de memoria activos filtrados por domain (meta.domain)."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, type, title, content, meta, created_at, updated_at, valid_from, valid_to, version, active
    FROM memory_nodes
    ORDER BY updated_at DESC
    LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    nodes: List[MemoryNode] = []
    for row in rows:
        meta_raw = json.loads(row[4]) if row[4] else {}
        node_domain = meta_raw.get("domain")
        if node_domain and node_domain != domain:
            continue

        refs = _get_refs_for_source(row[0])

        node = MemoryNode(
            id=row[0],
            type=row[1],
            title=row[2],
            content=json.loads(row[3]) if row[3] else {},
            meta=MemoryMeta(
                source=meta_raw.get("source", "system"),
                confidence=float(meta_raw.get("confidence", 0.7)),
                tags=meta_raw.get("tags", []),
                emotion=meta_raw.get("emotion"),
                domain=meta_raw.get("domain"),
            ),
            refs=refs,
            created_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
            updated_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
            valid_from=datetime.fromisoformat(row[7]) if row[7] else None,
            valid_to=datetime.fromisoformat(row[8]) if row[8] else None,
            version=int(row[9]) if row[9] is not None else 1,
            active=bool(row[10]),
        )
        nodes.append(node)

    return nodes


def _get_refs_for_source(source_id: str) -> List[MemoryRef]:
    """Recupera referencias para un nodo fuente."""
    conn = sqlite3.connect(MEMORY_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT target_id, relation, weight
    FROM memory_refs
    WHERE source_id = ?
    """, (source_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        MemoryRef(target_id=row[0], relation=row[1], weight=float(row[2]) if row[2] is not None else 1.0)
        for row in rows
    ]


