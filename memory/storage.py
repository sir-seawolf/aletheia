"""Almacenamiento simple en SQLite para memoria."""

import sqlite3
import os
from datetime import datetime
from typing import List
from memory.models import MemoryItem
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

