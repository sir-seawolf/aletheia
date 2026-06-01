"""
Semantic memory graph — query layer over the existing memory_nodes / memory_refs
SQLite tables already defined in memory/storage.py.

No schema changes needed. Provides:
  add_concept()   — upsert a knowledge node
  add_relation()  — upsert a directed edge between concepts
  get_related()   — BFS neighborhood of a concept (depth-limited)
  search()        — text search over titles and meta
  get_by_domain() — all nodes for a domain
"""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime

from memory.models import MemoryMeta, MemoryNode, MemoryRef
from memory.storage import MEMORY_DB_PATH, init_db, save_memory_node


@contextmanager
def _db():
    """Yield a SQLite connection that auto-commits and always closes."""
    init_db()
    conn = sqlite3.connect(MEMORY_DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _stable_id(domain: str, title: str) -> str:
    """Deterministic UUID so the same concept always maps to the same node."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{domain}:{title.lower().strip()}"))


# ── write API ──────────────────────────────────────────────────────────────

def add_concept(
    title: str,
    domain: str,
    content: dict | None = None,
    emotion: str = "neutro",
    tags: list[str] | None = None,
    confidence: float = 0.7,
) -> str:
    """Add or update a semantic concept node. Returns node id."""
    if not title or not domain:
        return ""
    node_id = _stable_id(domain, title)
    node = MemoryNode(
        id=node_id,
        type="concept",
        title=title,
        content=content or {},
        meta=MemoryMeta(
            source="semantic_graph",
            confidence=confidence,
            tags=tags or [domain],
            emotion=emotion,
            domain=domain,
        ),
        refs=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        active=True,
    )
    save_memory_node(node)
    return node_id


def add_relation(
    from_title: str,
    to_title: str,
    domain: str,
    relation: str = "relacionado_con",
    weight: float = 0.7,
) -> None:
    """Add a directed relation between two concept titles."""
    from_id = _stable_id(domain, from_title)
    to_id   = _stable_id(domain, to_title)
    with _db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO memory_refs (source_id, target_id, relation, weight) VALUES (?, ?, ?, ?)",
            (from_id, to_id, relation, weight),
        )


# ── read API ───────────────────────────────────────────────────────────────

def get_related(title: str, domain: str, depth: int = 2) -> list[dict]:
    """BFS over memory_refs starting from a concept. Returns enriched node list."""
    start_id = _stable_id(domain, title)
    visited: set[str] = set()
    frontier = [start_id]
    results: list[dict] = []

    with _db() as conn:
        for _ in range(depth):
            next_frontier: list[str] = []
            for node_id in frontier:
                if node_id in visited:
                    continue
                visited.add(node_id)

                row = conn.execute(
                    "SELECT id, title, content, meta FROM memory_nodes WHERE id = ? AND active = 1",
                    (node_id,),
                ).fetchone()
                if row:
                    results.append({
                        "id": row[0],
                        "title": row[1],
                        "content": json.loads(row[2] or "{}"),
                        "meta": json.loads(row[3] or "{}"),
                    })

                neighbors = conn.execute(
                    "SELECT target_id FROM memory_refs WHERE source_id = ? ORDER BY weight DESC LIMIT 10",
                    (node_id,),
                ).fetchall()
                next_frontier.extend(n[0] for n in neighbors if n[0] not in visited)

            frontier = next_frontier
            if not frontier:
                break

    return results


def search(query: str, limit: int = 10) -> list[dict]:
    """Text search over node titles, meta, and content fields."""
    if not query:
        return []
    with _db() as conn:
        rows = conn.execute(
            """SELECT id, title, content, meta FROM memory_nodes
               WHERE active = 1 AND (title LIKE ? OR meta LIKE ? OR content LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    return [
        {
            "id": r[0],
            "title": r[1],
            "content": json.loads(r[2] or "{}"),
            "meta": json.loads(r[3] or "{}"),
        }
        for r in rows
    ]


def find_concepts(query: str, domain: str = "", limit: int = 10) -> list[dict]:
    """Search concepts by query text, optionally scoped to a domain."""
    if domain:
        domain_hits = get_by_domain(domain, limit * 2)
        q = query.lower()
        filtered = [
            r for r in domain_hits
            if q in r.get("title", "").lower() or q in str(r.get("content", "")).lower()
        ]
        if filtered:
            return filtered[:limit]
    return search(query, limit)


def get_by_domain(domain: str, limit: int = 20) -> list[dict]:
    """Return active concept nodes for a domain."""
    with _db() as conn:
        rows = conn.execute(
            """SELECT id, title, content, meta FROM memory_nodes
               WHERE active = 1 AND meta LIKE ?
               ORDER BY updated_at DESC LIMIT ?""",
            (f'%"domain": "{domain}"%', limit),
        ).fetchall()
    return [
        {
            "id": r[0],
            "title": r[1],
            "content": json.loads(r[2] or "{}"),
            "meta": json.loads(r[3] or "{}"),
        }
        for r in rows
    ]
