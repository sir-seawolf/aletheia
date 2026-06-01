"""
RAG store — ChromaDB + Ollama nomic-embed-text.

Storage: PALACE/rag/chroma/  (excluded from git via PALACE/ gitignore rule)
Embeddings: Ollama nomic-embed-text (run: ollama pull nomic-embed-text)

Degrades silently when Ollama or ChromaDB is unavailable so that
ingestion never fails because of RAG.
"""

import requests
from pathlib import Path

_PERSIST_DIR  = Path(__file__).parent.parent.parent / "PALACE" / "rag" / "chroma"
_OLLAMA_URL   = "http://localhost:11434"
_EMBED_MODEL  = "nomic-embed-text"
_COLLECTION   = "aletheia_docs"
_CHUNK_SIZE   = 500
_CHUNK_OVERLAP = 50

_collection = None


def _get_collection():
    global _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        _PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(_PERSIST_DIR))
        _collection = client.get_or_create_collection(
            name=_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except Exception as exc:
        print(f"[RAG] ChromaDB init failed: {exc}")
        return None


def _embed(texts: list[str]) -> list[list[float]] | None:
    try:
        out = []
        for text in texts:
            r = requests.post(
                f"{_OLLAMA_URL}/api/embeddings",
                json={"model": _EMBED_MODEL, "prompt": text},
                timeout=30,
            )
            r.raise_for_status()
            out.append(r.json()["embedding"])
        return out
    except Exception as exc:
        print(f"[RAG] Embedding failed ({_EMBED_MODEL}): {exc}")
        return None


def _chunk(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        piece = text[start : start + _CHUNK_SIZE]
        if piece.strip():
            chunks.append(piece)
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


# ── public API ─────────────────────────────────────────────────────────────

def index(artifact_id: str, text: str, metadata: dict | None = None) -> bool:
    """
    Chunk + embed + upsert one artifact. Returns True on success.
    Silent no-op if Ollama or ChromaDB unavailable.
    """
    col = _get_collection()
    if col is None:
        return False

    chunks = _chunk(text)
    if not chunks:
        return False

    embeddings = _embed(chunks)
    if embeddings is None:
        return False

    meta_base = metadata or {}
    ids    = [f"{artifact_id}__chunk_{i}" for i in range(len(chunks))]
    metas  = [{**meta_base, "artifact_id": artifact_id, "chunk_index": i} for i in range(len(chunks))]

    try:
        # Remove stale chunks for this artifact before re-indexing
        existing = col.get(where={"artifact_id": artifact_id})
        if existing["ids"]:
            col.delete(ids=existing["ids"])
        col.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metas)
        return True
    except Exception as exc:
        print(f"[RAG] Index error for {artifact_id}: {exc}")
        return False


def search(query: str, n_results: int = 5, domain: str | None = None) -> list[dict]:
    """
    Semantic search over indexed documents.
    Returns list of {text, score, metadata}, empty list on failure.
    """
    col = _get_collection()
    if col is None:
        return []

    total = col.count()
    if total == 0:
        return []

    emb = _embed([query])
    if emb is None:
        return []

    where = {"domain": domain} if domain else None

    try:
        results = col.query(
            query_embeddings=emb,
            n_results=min(n_results, total),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        out = []
        for i, doc in enumerate(results["documents"][0]):
            score = 1.0 - results["distances"][0][i]  # cosine: lower dist = higher sim
            out.append({
                "text":     doc,
                "score":    round(score, 3),
                "metadata": results["metadatas"][0][i],
            })
        return out
    except Exception as exc:
        print(f"[RAG] Search error: {exc}")
        return []


def index_all() -> dict:
    """Re-index all artifacts from artifact_store. Returns {indexed, skipped, failed, total}."""
    from core.docs import artifact_store

    entries  = artifact_store.query(limit=10_000)
    indexed = skipped = failed = 0

    for entry in entries:
        text = artifact_store.get_text(entry["id"])
        if not text:
            skipped += 1
            continue
        meta = {
            "domain":   entry.get("domain", "general"),
            "type":     entry.get("type", "document"),
            "source":   entry.get("source", ""),
            "filename": entry.get("filename", ""),
            "date":     entry.get("source_date", ""),
        }
        if index(entry["id"], text, meta):
            indexed += 1
        else:
            failed += 1

    return {"indexed": indexed, "skipped": skipped, "failed": failed, "total": len(entries)}


def count() -> int:
    col = _get_collection()
    if col is None:
        return 0
    try:
        return col.count()
    except Exception:
        return 0
