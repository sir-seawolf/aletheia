"""Almacenamiento simple en SQLite para memoria."""

import sqlite3
import json
import os
from typing import List, Optional
from memory.models import MemoryItem
from config import MEMORY_DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Obtiene conexión a la base de datos."""
    os.makedirs(os.path.dirname(MEMORY_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Inicializa la tabla si no existe."""
    conn = _get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_items (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            date TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            source TEXT,
            domain TEXT,
            tags TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save(item: MemoryItem) -> str:
    """Guarda un item en la base de datos."""
    _init_db()
    conn = _get_connection()
    conn.execute(
        """
        INSERT OR REPLACE INTO memory_items
        (id, type, content, date, confidence, source, domain, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item.id,
            item.type,
            item.content,
            item.date,
            item.confidence,
            item.source,
            item.domain,
            json.dumps(item.tags),
        ),
    )
    conn.commit()
    conn.close()
    return item.id


def get_all(domain: Optional[str] = None) -> List[MemoryItem]:
    """Obtiene todos los items, opcionalmente filtrados por dominio."""
    _init_db()
    conn = _get_connection()

    if domain:
        rows = conn.execute(
            "SELECT * FROM memory_items WHERE domain = ? ORDER BY date DESC",
            (domain,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM memory_items ORDER BY date DESC").fetchall()

    conn.close()
    return [_row_to_item(row) for row in rows]


def search(query: str) -> List[MemoryItem]:
    """Búsqueda simple por contenido."""
    _init_db()
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM memory_items WHERE content LIKE ? ORDER BY date DESC",
        (f"%{query}%",),
    ).fetchall()
    conn.close()
    return [_row_to_item(row) for row in rows]


def _row_to_item(row: sqlite3.Row) -> MemoryItem:
    """Convierte una fila de SQLite a MemoryItem."""
    return MemoryItem(
        id=row["id"],
        type=row["type"],
        content=row["content"],
        date=row["date"],
        confidence=row["confidence"],
        source=row["source"],
        domain=row["domain"],
        tags=json.loads(row["tags"]) if row["tags"] else [],
    )

