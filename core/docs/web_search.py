"""
Web search via DuckDuckGo (no API key required).

Returns structured results that can be injected into the LLM context
or stored as artifacts.
"""

from typing import Any


def search(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    """
    Search the web for *query* and return up to *max_results* items.

    Each item: {"title": str, "url": str, "snippet": str}
    """
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title":   r.get("title", ""),
                    "url":     r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return results
    except Exception as exc:
        return [{"error": str(exc)}]


def search_and_summarise(query: str, max_results: int = 6) -> str:
    """
    Search and return a plain-text digest ready for LLM injection.
    """
    results = search(query, max_results)
    if not results or "error" in results[0]:
        err = results[0].get("error", "sin resultados") if results else "sin resultados"
        return f"[Búsqueda web falló: {err}]"

    lines = [f"Resultados web para: «{query}»\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   {r['url']}")
        if r["snippet"]:
            lines.append(f"   {r['snippet'][:200]}")
        lines.append("")
    return "\n".join(lines)


def news(query: str, max_results: int = 6) -> list[dict[str, Any]]:
    """Search recent news headlines."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            return [
                {"title": r["title"], "url": r["url"], "date": r.get("date", ""), "snippet": r.get("body", "")}
                for r in ddgs.news(query, max_results=max_results)
            ]
    except Exception as exc:
        return [{"error": str(exc)}]
