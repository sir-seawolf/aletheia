"""
Financial document extractor.

Uses the LLM to parse structured invoice/expense data from plain text.
Falls back to regex heuristics if the LLM is unavailable or returns garbage.
"""

import re
import json
from typing import Any

# Keywords that signal financial content in email bodies or documents
FINANCIAL_KEYWORDS = [
    "factura", "invoice", "recibo", "receipt",
    "importe", "amount", "total", "subtotal",
    "iva", "vat", "tax", "impuesto",
    "pago", "payment", "cobro", "cargo",
    "gasto", "expense", "coste", "cost",
    "€", "$", "eur", "usd",
]

# Patterns for body keyword extraction  (captures ±200 chars around each hit)
_KW_RE = re.compile(
    r"(" + "|".join(re.escape(k) for k in FINANCIAL_KEYWORDS) + r")",
    re.IGNORECASE,
)

_AMOUNT_RE  = re.compile(r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*(?:€|\$|EUR|USD)", re.IGNORECASE)
_DATE_RE    = re.compile(r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b")
_INV_RE     = re.compile(r"(?:factura|invoice|fac|inv)[\.:\s#-]*([A-Z0-9\-\/]{4,20})", re.IGNORECASE)


def has_financial_content(text: str) -> bool:
    """Quick check: does this text contain financial keywords?"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in FINANCIAL_KEYWORDS)


def extract_body_excerpt(body: str, context_chars: int = 200) -> str:
    """
    Return a condensed excerpt of the email body containing only the
    text near financial keywords (±context_chars).
    """
    if not body:
        return ""
    matches = list(_KW_RE.finditer(body))
    if not matches:
        return ""

    # Collect non-overlapping windows
    windows: list[tuple[int, int]] = []
    for m in matches:
        start = max(0, m.start() - context_chars)
        end   = min(len(body), m.end() + context_chars)
        if windows and start <= windows[-1][1]:
            windows[-1] = (windows[-1][0], end)
        else:
            windows.append((start, end))

    excerpts = ["..." + body[s:e].strip() + "..." for s, e in windows[:5]]
    return "\n\n".join(excerpts)


def extract_structured(text: str, source_hint: str = "") -> dict[str, Any]:
    """
    Parse financial fields from *text* using LLM + regex fallback.

    Returns:
      {
        "vendor": str, "date": str, "amount": float, "vat": float,
        "concept": str, "invoice_number": str, "currency": str,
        "confidence": float   # 0-1, based on how many fields were found
      }
    """
    result = _regex_extract(text)

    # Try to enrich with LLM
    try:
        from core.llm import router
        prompt = (
            "Extrae los datos de esta factura o documento financiero en JSON.\n"
            "Devuelve SOLO el JSON con estas claves (valores null si no aparecen):\n"
            '{"vendor": "", "date": "YYYY-MM-DD", "amount": 0.0, "vat": 0.0, '
            '"concept": "", "invoice_number": "", "currency": "EUR"}\n\n'
            f"Texto:\n{text[:3000]}"
        )
        raw = router.generate("financial_extract", prompt, context={"domain": "finanzas"}, temp=0.1)
        llm_data = _parse_json_from_llm(raw)
        if llm_data:
            # Merge: LLM wins unless it returned null for a field regex found
            for k, v in llm_data.items():
                if v is not None and v != "" and v != 0.0:
                    result[k] = v
    except Exception:
        pass  # regex fallback is sufficient

    # Confidence: count non-null fields out of the 6 key fields
    key_fields = ["vendor", "date", "amount", "invoice_number", "concept", "currency"]
    filled = sum(1 for f in key_fields if result.get(f))
    result["confidence"] = round(filled / len(key_fields), 2)

    return result


def _regex_extract(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "vendor": None, "date": None, "amount": None, "vat": None,
        "concept": None, "invoice_number": None, "currency": "EUR",
    }

    # Amount — take the largest number found (likely the total)
    amounts = [_parse_amount(m.group(1)) for m in _AMOUNT_RE.finditer(text)]
    if amounts:
        result["amount"] = max(amounts)

    # Date — first match
    dm = _DATE_RE.search(text)
    if dm:
        result["date"] = _normalise_date(dm.group(1))

    # Invoice number
    im = _INV_RE.search(text)
    if im:
        result["invoice_number"] = im.group(1).strip()

    # Currency
    if "USD" in text.upper() or "$" in text:
        result["currency"] = "USD"

    return result


def _parse_amount(s: str) -> float:
    s = s.replace(" ", "")
    if "," in s and "." in s:
        if s.rindex(",") > s.rindex("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        # Could be thousands sep or decimal
        parts = s.split(",")
        if len(parts[-1]) == 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _normalise_date(s: str) -> str:
    for sep in ("/", "-", "."):
        if sep in s:
            parts = s.split(sep)
            if len(parts) == 3:
                if len(parts[0]) == 4:          # YYYY-MM-DD
                    return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                elif len(parts[2]) == 4:         # DD-MM-YYYY
                    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                elif len(parts[2]) == 2:         # DD-MM-YY
                    year = "20" + parts[2]
                    return f"{year}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
    return s


def _parse_json_from_llm(raw: str) -> dict | None:
    try:
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return None
