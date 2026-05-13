"""
KRONOS context builder — thin wrapper over financial_cache.summary_text().
Kept for backward compatibility; new code should use financial_cache directly.
"""

from core.kronos.financial_cache import summary_text, rebuild_if_stale, load


def build_context(mode: str = "brief") -> str:
    """Return financial context block for LLM prompts."""
    return summary_text(mode=mode)


def _aggregate_transactions() -> dict:
    """Return raw aggregated data (used by tests / diagnostics)."""
    cache = rebuild_if_stale()
    s = cache.get("summary", {})
    txns = cache.get("transactions", [])
    return {
        "count":          s.get("count", 0),
        "total_income":   s.get("total_income", 0.0),
        "total_expenses": s.get("total_expenses", 0.0),
        "net":            s.get("net", 0.0),
        "by_month":       s.get("by_month", {}),
        "by_category":    s.get("by_category", {}),
        "transactions":   txns,
    }
