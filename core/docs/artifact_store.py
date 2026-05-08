"""
Artifact Store — PALACE/artifacts/

Every ingested piece of content (email body excerpt, PDF, doc) gets a SHA-256
identity.  The store prevents duplicates and tracks updates.

Index structure (PALACE/artifacts/index.json):
[
  {
    "id":        "sha256hex",
    "prev_id":   "sha256hex | null",   # previous version hash
    "source":    "gmail:msg_id | drive:path | upload:filename",
    "source_date": "ISO date",
    "domain":    "finanzas | ...",
    "type":      "invoice | expense | email_excerpt | document",
    "filename":  "FAC-2025-0042.pdf",
    "stored_at": "ISO datetime",
    "version":   1,
    "financial": { ... } | null,       # extracted structured data
    "text_path": "PALACE/artifacts/sha256hex.txt"
  },
  ...
]
"""

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BASE    = Path(__file__).parent.parent.parent / "PALACE" / "artifacts"
_INDEX   = _BASE / "index.json"
_TEXTS   = _BASE / "texts"


def _load_index() -> list[dict]:
    if not _INDEX.exists():
        return []
    try:
        return json.loads(_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_index(index: list[dict]) -> None:
    _BASE.mkdir(parents=True, exist_ok=True)
    _INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── public API ─────────────────────────────────────────────────────────────

class IngestResult:
    __slots__ = ("status", "artifact_id", "prev_id", "version")

    def __init__(self, status: str, artifact_id: str, prev_id: str | None = None, version: int = 1):
        self.status      = status      # "new" | "duplicate" | "updated"
        self.artifact_id = artifact_id
        self.prev_id     = prev_id
        self.version     = version

    def to_dict(self) -> dict:
        return {
            "status":      self.status,
            "artifact_id": self.artifact_id,
            "prev_id":     self.prev_id,
            "version":     self.version,
        }


def ingest(
    text: str,
    source: str,
    domain: str = "general",
    artifact_type: str = "document",
    filename: str = "",
    source_date: str = "",
    financial: dict | None = None,
) -> IngestResult:
    """
    Store *text* as an artifact.

    Returns IngestResult with status:
      "new"       — first time we see this content
      "duplicate" — identical hash already stored, nothing written
      "updated"   — same source, different content → new version created
    """
    index = _load_index()
    new_hash = _sha256(text)

    # 1. Exact duplicate?
    for entry in index:
        if entry["id"] == new_hash:
            return IngestResult("duplicate", new_hash, version=entry["version"])

    # 2. Same source, different content → update
    prev_id: str | None = None
    version = 1
    for entry in index:
        if entry.get("source") == source and entry["id"] != new_hash:
            prev_id = entry["id"]
            version = entry.get("version", 1) + 1
            entry["superseded_by"] = new_hash  # mark old entry
            break

    # 3. Write text file
    _TEXTS.mkdir(parents=True, exist_ok=True)
    text_path = _TEXTS / f"{new_hash}.txt"
    text_path.write_text(text, encoding="utf-8")

    # 4. Append to index
    entry = {
        "id":          new_hash,
        "prev_id":     prev_id,
        "source":      source,
        "source_date": source_date or "",
        "domain":      domain,
        "type":        artifact_type,
        "filename":    filename,
        "stored_at":   datetime.now(timezone.utc).isoformat(),
        "version":     version,
        "financial":   financial,
        "text_path":   str(text_path),
    }
    index.append(entry)
    _save_index(index)

    status = "updated" if prev_id else "new"
    return IngestResult(status, new_hash, prev_id=prev_id, version=version)


def get_text(artifact_id: str) -> str | None:
    path = _TEXTS / f"{artifact_id}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else None


def query(
    domain: str | None = None,
    artifact_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    source_prefix: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return index entries matching all supplied filters."""
    index = _load_index()
    results = []
    for entry in index:
        if entry.get("superseded_by"):
            continue
        if domain and entry.get("domain") != domain:
            continue
        if artifact_type and entry.get("type") != artifact_type:
            continue
        if source_prefix and not entry.get("source", "").startswith(source_prefix):
            continue
        sd = entry.get("source_date", "")
        if date_from and sd and sd < date_from:
            continue
        if date_to and sd and sd > date_to:
            continue
        results.append(entry)
        if len(results) >= limit:
            break
    return results


def financial_summary(year: int | None = None) -> dict[str, Any]:
    """Aggregate financial data from all invoice/expense artifacts."""
    filters: dict[str, Any] = {"artifact_type": "invoice"}
    if year:
        filters["date_from"] = f"{year}-01-01"
        filters["date_to"]   = f"{year}-12-31"

    entries = query(domain="finanzas", **{k: v for k, v in filters.items() if v})
    entries += query(domain="finanzas", artifact_type="expense",
                     **{k: v for k, v in {"date_from": filters.get("date_from"), "date_to": filters.get("date_to")}.items() if v})

    total = 0.0
    total_vat = 0.0
    by_vendor: dict[str, float] = {}
    by_month: dict[str, float] = {}
    items = []

    for e in entries:
        fin = e.get("financial") or {}
        amount = float(fin.get("amount") or 0)
        vat    = float(fin.get("vat") or 0)
        vendor = fin.get("vendor", "Desconocido")
        date   = e.get("source_date", "")[:7]  # YYYY-MM

        total     += amount
        total_vat += vat
        by_vendor[vendor] = by_vendor.get(vendor, 0) + amount
        if date:
            by_month[date] = by_month.get(date, 0) + amount
        items.append({
            "filename": e.get("filename", ""),
            "date":     e.get("source_date", ""),
            "vendor":   vendor,
            "amount":   amount,
            "vat":      vat,
            "concept":  fin.get("concept", ""),
        })

    return {
        "year":      year,
        "total":     round(total, 2),
        "total_vat": round(total_vat, 2),
        "count":     len(items),
        "by_vendor": by_vendor,
        "by_month":  dict(sorted(by_month.items())),
        "items":     items,
    }


def stats() -> dict:
    index = _load_index()
    active = [e for e in index if not e.get("superseded_by")]
    return {
        "total_artifacts": len(active),
        "by_type":   _count(active, "type"),
        "by_domain": _count(active, "domain"),
        "by_source": _count_prefix(active),
    }


def _count(entries: list, key: str) -> dict:
    out: dict[str, int] = {}
    for e in entries:
        v = e.get(key, "?")
        out[v] = out.get(v, 0) + 1
    return out


def _count_prefix(entries: list) -> dict:
    out: dict[str, int] = {}
    for e in entries:
        prefix = (e.get("source") or "?").split(":")[0]
        out[prefix] = out.get(prefix, 0) + 1
    return out
