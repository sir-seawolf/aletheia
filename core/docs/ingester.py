"""
Document ingester — extracts plain text from common file formats.

Supported: .txt, .md, .csv, .json, .pdf, .docx
Graceful fallback: if a heavy library (pdfplumber, python-docx) is not installed,
returns a helpful error message instead of crashing.
"""

from pathlib import Path

_MAX_CHARS = 12_000   # max chars injected into LLM context


def extract_text(path: str | Path) -> str:
    """
    Return plain-text content of the file at *path*.
    Raises FileNotFoundError if the file does not exist.
    Truncates to _MAX_CHARS with a notice if the document is long.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {p}")
    if not p.is_file():
        raise ValueError(f"La ruta no es un archivo: {p}")

    suffix = p.suffix.lower()

    if suffix in (".txt", ".md", ".rst", ".log"):
        text = p.read_text(encoding="utf-8", errors="replace")

    elif suffix == ".csv":
        text = p.read_text(encoding="utf-8", errors="replace")

    elif suffix == ".json":
        import json
        raw = p.read_text(encoding="utf-8", errors="replace")
        try:
            obj = json.loads(raw)
            text = json.dumps(obj, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            text = raw

    elif suffix == ".pdf":
        text = _extract_pdf(p)

    elif suffix in (".docx", ".doc"):
        text = _extract_docx(p)

    else:
        # Try reading as UTF-8 plain text regardless
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise ValueError(f"Formato no soportado ({suffix}): {exc}") from exc

    return _truncate(text, p.name)


def _extract_pdf(path: Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n\n".join(pages)
    except ImportError:
        pass

    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    except ImportError:
        pass

    try:
        import PyPDF2
        with open(str(path), "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    except ImportError:
        return (
            "No se pudo extraer el PDF. "
            "Instala pdfplumber o pypdf:  pip install pdfplumber"
        )


def _extract_docx(path: Path) -> str:
    try:
        import docx
        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        return (
            "No se pudo extraer el DOCX. "
            "Instala python-docx:  pip install python-docx"
        )


def _truncate(text: str, name: str) -> str:
    text = text.strip()
    if len(text) <= _MAX_CHARS:
        return text
    return (
        text[:_MAX_CHARS]
        + f"\n\n[... documento {name} truncado a {_MAX_CHARS} caracteres ...]"
    )


def describe(path: str | Path) -> dict:
    """Return metadata dict without extracting full content."""
    p = Path(path)
    stat = p.stat()
    return {
        "name": p.name,
        "suffix": p.suffix.lower(),
        "size_kb": round(stat.st_size / 1024, 1),
        "path": str(p.resolve()),
    }
