"""Almacenamiento simple en SQLite para memoria."""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Optional
from memory.models import MemoryItem, FeedbackItem
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


