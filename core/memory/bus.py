"""
MemoryBus — unified memory access layer for Aletheia.

Aggregates all memory backends behind a single interface:
  - SQLite episodic  (memory.service)
  - PALACE semantic  (core.palace)
  - Semantic graph   (core.memory.semantic_graph)
  - Working memory   (core.memory.working_memory)

All cognitive modes MUST access memory through this bus — never directly.
"""

from __future__ import annotations

import hashlib
import threading
from typing import Any, Dict, List, Optional

_lock = threading.Lock()


class MemoryBus:

    def __init__(self) -> None:
        self._working: Dict[str, Any] = {}       # in-process, ephemeral
        self._contradiction_log: List[Dict] = []

    # ── Primary API ─────────────────────────────────────────────────────────

    def retrieve(
        self,
        domain: str,
        query: str = "",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Unified retrieval — merges SQLite episodic + PALACE + working memory.
        Returns a deduplicated, salience-sorted list.
        """
        results: List[Dict[str, Any]] = []

        # 1. SQLite episodic
        try:
            from memory.service import retrieve_context
            for item in retrieve_context(domain)[-limit:]:
                results.append(self._norm(item, "episodic"))
        except Exception:
            pass

        # 2. PALACE domain entries
        try:
            from core.palace.reader import read_palace
            for item in read_palace(domain)[:limit]:
                results.append(self._norm(item, "palace"))
        except Exception:
            pass

        # 3. Working memory
        with _lock:
            if domain in self._working:
                results.append(self._norm(self._working[domain], "working"))

        deduped = self._deduplicate(results)[:limit]
        # Write memory sources to active trace (best-effort)
        try:
            from core.tracing.context import trace_memory
            for src in {r.get("_source", "") for r in deduped}:
                if src:
                    trace_memory(src, 0)
            if deduped:
                from core.tracing.context import get_trace
                tb = get_trace()
                if tb:
                    tb.set_memory_count(len(deduped))
        except Exception:
            pass
        return deduped

    def search(
        self,
        domain: str,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search — PALACE search engine + semantic graph.
        Falls back to retrieve() if search backends are unavailable.
        """
        results: List[Dict[str, Any]] = []

        try:
            from core.palace.search import PalaceSearchEngine
            hits = PalaceSearchEngine().search(domain, query)
            for h in hits[:limit]:
                results.append(self._norm(h, "palace_search"))
        except Exception:
            pass

        try:
            from core.memory.semantic_graph import find_concepts
            concepts = find_concepts(query, domain)
            for c in concepts[:limit]:
                results.append(self._norm(c, "semantic_graph"))
        except Exception:
            pass

        if not results:
            results = self.retrieve(domain, query, limit)

        return self._deduplicate(results)[:limit]

    def store(
        self,
        domain: str,
        content: Any,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Write to working memory and persist to SQLite."""
        with _lock:
            self._working[domain] = content
        try:
            from memory.service import store_result
            store_result(domain, content)
        except Exception:
            pass

    def set_working(self, key: str, value: Any) -> None:
        with _lock:
            self._working[key] = value

    def get_working(self, key: str, default: Any = None) -> Any:
        with _lock:
            return self._working.get(key, default)

    def consolidate(self) -> int:
        """Trigger PALACE → semantic graph consolidation. Returns nodes processed."""
        try:
            from core.memory.consolidator import consolidate
            return consolidate(verbose=False)
        except Exception:
            return 0

    def log_contradiction(self, fact_a: str, fact_b: str, domain: str) -> None:
        self._contradiction_log.append({"domain": domain, "a": fact_a, "b": fact_b})

    def get_contradictions(self) -> List[Dict]:
        return list(self._contradiction_log)

    # ── State metrics ────────────────────────────────────────────────────────

    def pressure(self) -> float:
        """Memory pressure 0.0–1.0 based on working memory load."""
        with _lock:
            return min(1.0, len(self._working) / 50.0)

    def working_summary(self) -> str:
        """Compact string of current working memory for prompt injection."""
        try:
            from core.memory.working_memory import session as wm
            return wm.to_context_str(last_n=4)
        except Exception:
            return ""

    # ── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _norm(item: Any, source: str) -> Dict[str, Any]:
        if isinstance(item, dict):
            return {**item, "_source": source}
        return {"content": str(item)[:500], "_source": source}

    @staticmethod
    def _deduplicate(items: List[Dict]) -> List[Dict]:
        seen: set = set()
        out: List[Dict] = []
        for item in items:
            key = hashlib.md5(str(item.get("content", item))[:80].encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                out.append(item)
        return out


# Singleton — shared across all cognitive modes
memory_bus = MemoryBus()
