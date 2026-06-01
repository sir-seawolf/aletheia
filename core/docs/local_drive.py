"""
Local cloud-storage navigator.

Detects Google Drive and OneDrive sync folders on the local filesystem,
plus any custom folders listed in PALACE/config/doc_sources.json.

All operations are read-only.
"""

import json
import os
from pathlib import Path
from typing import Any

from core.docs.ingester import extract_text, describe

# ── Auto-detected roots ────────────────────────────────────────────────────

_HOME = Path.home()

_CANDIDATES: list[Path] = [
    # Google Drive (Drive for Desktop)
    _HOME / "Google Drive",
    _HOME / "GoogleDrive",
    Path("G:/My Drive"),
    Path("G:/Mi unidad"),
    # OneDrive (personal)
    _HOME / "OneDrive",
    _HOME / "OneDrive - Personal",
    # OneDrive (business — varies by tenant name)
    *list(_HOME.glob("OneDrive - *")),
    # iCloud Drive (Windows)
    _HOME / "iCloudDrive",
]

_SUPPORTED_EXTS = {
    ".txt", ".md", ".rst", ".log",
    ".csv", ".json",
    ".pdf", ".docx", ".doc",
}

_CONFIG_PATH = Path(__file__).parent.parent.parent / "PALACE" / "config" / "doc_sources.json"


# ── Config helpers ─────────────────────────────────────────────────────────

def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"extra_folders": []}


def save_config(config: dict) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── Public API ─────────────────────────────────────────────────────────────

def detected_roots() -> list[dict]:
    """Return all drive roots that actually exist on this machine."""
    roots = [p for p in _CANDIDATES if p.exists() and p.is_dir()]

    config = _load_config()
    for extra in config.get("extra_folders", []):
        ep = Path(extra)
        if ep.exists() and ep.is_dir() and ep not in roots:
            roots.append(ep)

    return [{"name": p.name, "path": str(p)} for p in roots]


def add_folder(folder_path: str) -> dict:
    """Persist a custom folder to doc_sources.json and return updated roots."""
    p = Path(folder_path)
    if not p.exists():
        raise FileNotFoundError(f"Carpeta no encontrada: {folder_path}")
    config = _load_config()
    extras: list[str] = config.setdefault("extra_folders", [])
    if str(p) not in extras:
        extras.append(str(p))
        save_config(config)
    return {"added": str(p), "roots": detected_roots()}


def browse(path: str = "", max_items: int = 200) -> dict:
    """
    List files and subdirectories at *path*.
    If *path* is empty, return the detected roots.
    """
    if not path:
        return {"path": "", "roots": detected_roots(), "items": []}

    p = Path(path)
    if not p.exists():
        return {"error": f"No existe: {path}"}
    if not p.is_dir():
        return {"error": f"No es un directorio: {path}"}

    items: list[dict] = []
    try:
        entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except PermissionError:
        return {"error": f"Sin permiso para leer: {path}"}

    for entry in entries[:max_items]:
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            items.append({"type": "dir", "name": entry.name, "path": str(entry)})
        elif entry.suffix.lower() in _SUPPORTED_EXTS:
            try:
                stat = entry.stat()
                items.append({
                    "type": "file",
                    "name": entry.name,
                    "path": str(entry),
                    "suffix": entry.suffix.lower(),
                    "size_kb": round(stat.st_size / 1024, 1),
                })
            except Exception:
                pass

    parent = str(p.parent) if p.parent != p else ""
    return {"path": str(p), "parent": parent, "items": items}


def search(query: str, root: str = "", max_results: int = 30) -> list[dict]:
    """
    Search files whose name or text content matches *query*.
    Searches inside *root* (or all detected roots if empty).
    Content search only for files ≤ 500 KB.
    """
    q = query.lower().strip()
    if not q:
        return []

    search_roots: list[Path]
    if root:
        rp = Path(root)
        if rp.exists():
            search_roots = [rp]
        else:
            return [{"error": f"Carpeta no encontrada: {root}"}]
    else:
        search_roots = [Path(r["path"]) for r in detected_roots()]

    results: list[dict] = []

    for sr in search_roots:
        if len(results) >= max_results:
            break
        for filepath in sr.rglob("*"):
            if len(results) >= max_results:
                break
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() not in _SUPPORTED_EXTS:
                continue
            if filepath.name.startswith("."):
                continue

            matched_name = q in filepath.name.lower()
            matched_content = False
            excerpt = ""

            if not matched_name and filepath.stat().st_size <= 500_000:
                try:
                    text = extract_text(filepath)
                    idx = text.lower().find(q)
                    if idx >= 0:
                        matched_content = True
                        start = max(0, idx - 60)
                        excerpt = "..." + text[start: idx + 120].replace("\n", " ") + "..."
                except Exception:
                    pass

            if matched_name or matched_content:
                entry = describe(filepath)
                entry["match"] = "nombre" if matched_name else "contenido"
                if excerpt:
                    entry["excerpt"] = excerpt
                results.append(entry)

    return results


def read_file(path: str) -> dict[str, Any]:
    """Extract and return text content of a file."""
    try:
        text = extract_text(path)
        meta = describe(path)
        return {"ok": True, "text": text, **meta}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
