"""
URL ingester — fetches a web page and extracts clean plain text.

Uses httpx for the HTTP request and BeautifulSoup for HTML parsing.
The extracted text is stored in the artifact_store for later querying.
"""

from typing import Any


_MAX_CHARS = 12_000
_SKIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form", "iframe"}


def fetch_and_extract(url: str) -> dict[str, Any]:
    """
    Fetch *url* and return:
      {"url": str, "title": str, "text": str, "ok": bool, "error": str|None}
    """
    try:
        import httpx
    except ImportError:
        return {"ok": False, "error": "pip install httpx", "url": url}

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {"ok": False, "error": "pip install beautifulsoup4", "url": url}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    try:
        resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}

    content_type = resp.headers.get("content-type", "")

    # Non-HTML: try as plain text
    if "html" not in content_type:
        text = resp.text[:_MAX_CHARS]
        return {"ok": True, "url": url, "title": url.split("/")[-1], "text": text}

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove noise
    for tag in soup.find_all(_SKIP_TAGS):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else url

    # Extract main content — prefer <article>, <main>, <body>
    for selector in ("article", "main", '[role="main"]', "body"):
        container = soup.select_one(selector)
        if container:
            break
    else:
        container = soup

    paragraphs = container.find_all(["p", "h1", "h2", "h3", "h4", "li", "td", "th"])
    lines = []
    for p in paragraphs:
        t = p.get_text(" ", strip=True)
        if len(t) > 20:
            lines.append(t)

    text = "\n\n".join(lines)
    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS] + "\n\n[... contenido truncado ...]"

    return {"ok": True, "url": url, "title": title, "text": text or resp.text[:2000]}


def ingest_url(url: str, domain: str = "general") -> dict[str, Any]:
    """
    Fetch, extract, and store a URL in the artifact store.
    Returns the ingest result merged with the page metadata.
    """
    page = fetch_and_extract(url)
    if not page.get("ok"):
        return page

    from core.docs.artifact_store import ingest
    result = ingest(
        text=page["text"],
        source=f"url:{url}",
        domain=domain,
        artifact_type="webpage",
        filename=page["title"][:80],
        source_date=__import__("datetime").date.today().isoformat(),
    )
    return {
        "ok":          True,
        "url":         url,
        "title":       page["title"],
        "chars":       len(page["text"]),
        "artifact_id": result.artifact_id,
        "status":      result.status,
        "excerpt":     page["text"][:400],
    }
