"""
KRONOS financial cache — PALACE/financial_cache.json

Computed once from all artifact texts + bank_parser re-parse.
All agents read from here; no repeated text parsing.

Public API:
  load()              → dict  (empty structure if not built)
  rebuild()           → dict  (full rebuild, overwrites cache)
  rebuild_if_stale()  → dict  (rebuild only if artifacts newer than cache)
  summary_text(mode)  → str   (context block for LLM prompts)
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.kronos.enricher import enrich

_PALACE      = Path(__file__).parent.parent.parent / "PALACE"
_CACHE_PATH  = _PALACE / "financial_cache.json"
_INDEX_PATH  = _PALACE / "artifacts" / "index.json"
_TEXTS_DIR   = _PALACE / "artifacts" / "texts"

_EMPTY: dict[str, Any] = {
    "built_at": None,
    "artifact_ids": [],
    "transactions": [],
    "summary": {
        "total_income": 0.0,
        "total_expenses": 0.0,
        "net": 0.0,
        "count": 0,
        "by_month": {},
        "by_category": {},
        "by_merchant": {},
    },
}


# ── helpers ────────────────────────────────────────────────────────────────

def _load_index() -> list[dict]:
    try:
        return json.loads(_INDEX_PATH.read_text(encoding="utf-8")) if _INDEX_PATH.exists() else []
    except Exception:
        return []


def _financial_artifact_ids() -> list[str]:
    return [
        e["id"] for e in _load_index()
        if not e.get("superseded_by")
        and e.get("domain") == "finanzas"
        and e.get("type") in ("bank_statement", "invoice", "expense")
    ]


def _parse_text_transactions(artifact_id: str) -> list[dict]:
    """Re-extract transactions from the stored artifact text."""
    path = _TEXTS_DIR / f"{artifact_id}.txt"
    if not path.exists():
        return []

    txns: list[dict] = []
    in_txns = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "Transacciones:":
            in_txns = True
            continue
        if not in_txns or not line.strip():
            continue
        # Format: "YYYY-MM-DD  concept  amount €  [category]"
        parts = line.rsplit("[", 1)
        if len(parts) != 2:
            continue
        category = parts[1].rstrip("]").strip()
        left = parts[0].strip()
        tokens = left.split()
        if len(tokens) < 3:
            continue
        date = tokens[0]
        try:
            amount = float(tokens[-2])
        except (ValueError, IndexError):
            continue
        concept = " ".join(tokens[1:-2]).strip()
        txns.append({
            "date": date,
            "concept": concept,
            "observation": "",
            "amount": amount,
            "balance": None,
            "category": category,
        })
    return txns


def _compute_summary(txns: list[dict]) -> dict:
    income = sum(t["amount"] for t in txns if t["amount"] > 0)
    expenses = sum(t["amount"] for t in txns if t["amount"] < 0)

    by_month: dict[str, float] = {}
    by_category: dict[str, float] = {}
    by_merchant: dict[str, float] = {}

    for t in txns:
        month = t["date"][:7]
        if month:
            by_month[month] = round(by_month.get(month, 0.0) + t["amount"], 2)

        cat = t.get("category", "otro")
        if t["amount"] < 0:
            by_category[cat] = round(by_category.get(cat, 0.0) + abs(t["amount"]), 2)

        merchant = t.get("merchant", t.get("concept", ""))
        if merchant and t["amount"] < 0:
            by_merchant[merchant] = round(
                by_merchant.get(merchant, 0.0) + abs(t["amount"]), 2
            )

    return {
        "total_income":   round(income, 2),
        "total_expenses": round(abs(expenses), 2),
        "net":            round(income + expenses, 2),
        "count":          len(txns),
        "by_month":       dict(sorted(by_month.items())),
        "by_category":    dict(sorted(by_category.items(), key=lambda x: x[1], reverse=True)),
        "by_merchant":    dict(sorted(by_merchant.items(), key=lambda x: x[1], reverse=True)),
    }


# ── public API ─────────────────────────────────────────────────────────────

def load() -> dict:
    """Load cache from disk. Returns empty structure if not built."""
    if not _CACHE_PATH.exists():
        return dict(_EMPTY)
    try:
        return json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return dict(_EMPTY)


def rebuild() -> dict:
    """Full rebuild from all financial artifacts. Writes and returns cache."""
    artifact_ids = _financial_artifact_ids()
    all_txns: list[dict] = []

    for aid in artifact_ids:
        raw_txns = _parse_text_transactions(aid)
        for t in raw_txns:
            all_txns.append(enrich(t))

    # Sort chronologically
    all_txns.sort(key=lambda t: t["date"])

    cache = {
        "built_at":     datetime.now(timezone.utc).isoformat(),
        "artifact_ids": artifact_ids,
        "transactions": all_txns,
        "summary":      _compute_summary(all_txns),
    }
    _CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return cache


def rebuild_if_stale() -> dict:
    """
    Rebuild only if any artifact is newer than the cache file.
    Returns current cache (rebuilt or loaded).
    """
    if not _CACHE_PATH.exists():
        return rebuild()

    cache_mtime = _CACHE_PATH.stat().st_mtime
    index = _load_index()
    for e in index:
        if e.get("domain") == "finanzas" and not e.get("superseded_by"):
            tp = _TEXTS_DIR / f"{e['id']}.txt"
            if tp.exists() and tp.stat().st_mtime > cache_mtime:
                return rebuild()

    return load()


def summary_text(mode: str = "brief") -> str:
    """
    Return a compact text block for LLM prompts.
    mode="brief" → 3-4 lines (voice)
    mode="full"  → full monthly + category + top merchants breakdown
    """
    cache = rebuild_if_stale()
    s = cache.get("summary", {})
    txns = cache.get("transactions", [])

    if not txns:
        return ""

    def fmt(v: float) -> str:
        return f"{abs(v):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    lines: list[str] = []
    lines.append(
        f"Datos financieros: {s['count']} movimientos | "
        f"Ingresos {fmt(s['total_income'])} | "
        f"Gastos {fmt(s['total_expenses'])} | "
        f"Neto {fmt(s['net'])} ({'positivo' if s['net'] >= 0 else 'negativo'})"
    )

    top_cats = list(s.get("by_category", {}).items())[:5]
    if top_cats:
        lines.append("Categorías principales: " +
                     " | ".join(f"{c}: {fmt(v)}" for c, v in top_cats))

    if mode == "full":
        lines.append("\nEvolución mensual (neto):")
        for month, net in s.get("by_month", {}).items():
            sign = "+" if net >= 0 else ""
            lines.append(f"  {month}: {sign}{fmt(net)}")

        top_merchants = list(s.get("by_merchant", {}).items())[:10]
        if top_merchants:
            lines.append("\nMayores gastos por merchant:")
            for m, v in top_merchants:
                lines.append(f"  {m}: {fmt(v)}")

        recent = sorted(txns, key=lambda t: t["date"], reverse=True)[:15]
        if recent:
            lines.append("\nÚltimos movimientos:")
            for t in recent:
                sign = "+" if t["amount"] >= 0 else ""
                merchant = t.get("merchant", t.get("concept", ""))[:35]
                tags = " ".join(f"[{tg}]" for tg in t.get("tags", [])[:2])
                lines.append(
                    f"  {t['date']}  {merchant:<35}  "
                    f"{sign}{fmt(t['amount'])}  {tags}"
                )

    return "\n".join(lines)
