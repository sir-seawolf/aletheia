"""
Bank statement parser — Spanish banks.

Supports:
  CSV  — CaixaBank, BBVA, Santander, ING, Sabadell, Bankinter, Openbank
  XLS/XLSX — most Spanish banks export in this format
  OFX/QFX  — Open Financial Exchange (Quicken-compatible)

Normalises every transaction to:
  {"date": "YYYY-MM-DD", "concept": str, "amount": float, "balance": float|None, "category": str}

Detected categories (heuristic):
  supermercado, restaurante, transporte, suscripcion, salud, ocio,
  nomina, transferencia, recibo, seguro, impuesto, otro
"""

import re
import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Any


# ── Category keywords ──────────────────────────────────────────────────────

_CATEGORIES: list[tuple[str, list[str]]] = [
    ("nomina",        ["nomina", "nómina", "salary", "sueldo", "haberes"]),
    ("supermercado",  ["mercadona", "lidl", "carrefour", "alcampo", "dia ", "eroski", "aldi", "supermercado"]),
    ("restaurante",   ["restaurante", "cafeteria", "bar ", "mcdonalds", "burger", "pizz", "sushi", "kebab"]),
    ("transporte",    ["renfe", "metro", "bus ", "cabify", "uber", "repsol", "cepsa", "bp ", "gasolina", "parking", "peaje"]),
    ("suscripcion",   ["netflix", "spotify", "amazon prime", "youtube", "hbo", "disney", "apple", "google one", "microsoft"]),
    ("salud",         ["farmacia", "medico", "médico", "hospital", "clinica", "clínica", "dentista", "seguro salud"]),
    ("ocio",          ["cine", "teatro", "concierto", "amazon", "zara", "mango", "h&m", "fnac", "corte ingles"]),
    ("recibo",        ["luz", "agua", "gas ", "telefono", "teléfono", "internet", "comunidad", "hipoteca", "alquiler"]),
    ("seguro",        ["seguro", "mapfre", "axa", "allianz", "mutua", "adeslas"]),
    ("impuesto",      ["hacienda", "agencia tributaria", "ayuntamiento", "impuesto", "ivtm", "ibi "]),
    ("transferencia", ["transferencia", "bizum", "paypal", "bizum"]),
]


def _categorise(concept: str) -> str:
    concept_l = concept.lower()
    for category, keywords in _CATEGORIES:
        if any(kw in concept_l for kw in keywords):
            return category
    return "otro"


def _parse_amount(s: str) -> float:
    """Parse Spanish/EU formatted numbers: 1.234,56 or 1,234.56 or 1234.56"""
    s = s.strip().replace(" ", "").replace("€", "").replace("$", "")
    if not s or s in ("-", ""):
        return 0.0
    # Determine decimal separator
    if "," in s and "." in s:
        if s.rindex(",") > s.rindex("."):   # 1.234,56
            s = s.replace(".", "").replace(",", ".")
        else:                                # 1,234.56
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts[-1]) == 2:             # 1234,56
            s = s.replace(",", ".")
        else:                               # 1,234
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_date(s: str) -> str:
    """Try multiple date formats, return ISO YYYY-MM-DD."""
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y",
                "%d.%m.%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s  # return as-is if nothing matches


# ── Bank-specific parsers ──────────────────────────────────────────────────

def _detect_bank(header: str) -> str:
    h = header.lower()
    if "caixabank" in h or "la caixa" in h: return "caixabank"
    if "bbva" in h:                          return "bbva"
    if "santander" in h:                     return "santander"
    if "ing" in h:                           return "ing"
    if "sabadell" in h:                      return "sabadell"
    if "bankinter" in h:                     return "bankinter"
    if "openbank" in h:                      return "openbank"
    return "generic"


def _parse_csv(text: str) -> list[dict]:
    """Generic CSV parser — tries to detect column roles."""
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []

    # Try to find the header row
    header_idx = 0
    for i, line in enumerate(lines[:10]):
        lower = line.lower()
        if any(kw in lower for kw in ["fecha", "date", "concepto", "importe", "amount", "saldo"]):
            header_idx = i
            break

    header = lines[header_idx]
    data_lines = lines[header_idx + 1:]

    # Detect separator
    sep = ";" if header.count(";") > header.count(",") else ","

    reader = csv.DictReader(io.StringIO("\n".join([header] + data_lines)), delimiter=sep)

    # Map column names to roles
    def _find_col(cols, candidates):
        for c in candidates:
            for col in cols:
                if c in col.lower():
                    return col
        return None

    transactions = []
    try:
        rows = list(reader)
    except Exception:
        return []

    if not rows:
        return []

    cols = list(rows[0].keys())
    date_col    = _find_col(cols, ["fecha valor", "fecha", "date", "f.valor"])
    concept_col = _find_col(cols, ["concepto", "concept", "descripcion", "descripción", "description", "comercio"])
    amount_col  = _find_col(cols, ["importe", "amount", "cargo", "abono", "movimiento"])
    balance_col = _find_col(cols, ["saldo", "balance"])

    if not date_col or not amount_col:
        # Fallback: first col = date, last numeric-looking = amount
        date_col    = cols[0]
        amount_col  = cols[-1]
        concept_col = cols[1] if len(cols) > 2 else cols[0]

    for row in rows:
        raw_date    = row.get(date_col, "").strip()
        raw_concept = row.get(concept_col, "").strip() if concept_col else ""
        raw_amount  = row.get(amount_col, "").strip()
        raw_balance = row.get(balance_col, "").strip() if balance_col else ""

        if not raw_date or not raw_amount:
            continue

        amount = _parse_amount(raw_amount)
        if amount == 0.0:
            continue

        transactions.append({
            "date":     _parse_date(raw_date),
            "concept":  raw_concept,
            "amount":   amount,
            "balance":  _parse_amount(raw_balance) if raw_balance else None,
            "category": _categorise(raw_concept),
        })

    return transactions


def _parse_xlsx(path: Path) -> list[dict]:
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("pip install openpyxl")

    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Find header row
    header_idx = 0
    for i, row in enumerate(rows[:10]):
        row_str = " ".join(str(c).lower() for c in row if c)
        if any(kw in row_str for kw in ["fecha", "date", "concepto", "importe"]):
            header_idx = i
            break

    header = [str(c or "").strip() for c in rows[header_idx]]
    data   = rows[header_idx + 1:]

    def _find_idx(candidates):
        for c in candidates:
            for i, h in enumerate(header):
                if c in h.lower():
                    return i
        return None

    date_i    = _find_idx(["fecha valor", "fecha", "date"])
    concept_i = _find_idx(["concepto", "descripcion", "description"])
    amount_i  = _find_idx(["importe", "amount", "cargo", "movimiento"])
    balance_i = _find_idx(["saldo", "balance"])

    if date_i is None or amount_i is None:
        date_i, amount_i = 0, -1

    transactions = []
    for row in data:
        if len(row) <= max(filter(lambda x: x is not None, [date_i, amount_i])):
            continue
        raw_date    = str(row[date_i] or "").strip()
        raw_concept = str(row[concept_i] or "").strip() if concept_i is not None else ""
        raw_amount  = str(row[amount_i] or "").strip()
        raw_balance = str(row[balance_i] or "").strip() if balance_i is not None else ""

        if not raw_date or not raw_amount:
            continue

        amount = _parse_amount(raw_amount)
        if amount == 0.0 and raw_amount not in ("0", "0,00", "0.00"):
            continue

        transactions.append({
            "date":     _parse_date(raw_date) if raw_date else "",
            "concept":  raw_concept,
            "amount":   amount,
            "balance":  _parse_amount(raw_balance) if raw_balance else None,
            "category": _categorise(raw_concept),
        })
    return transactions


def _parse_ofx(text: str) -> list[dict]:
    """Parse OFX/QFX (SGML-like financial exchange format)."""
    transactions = []
    for block in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, re.DOTALL | re.IGNORECASE):
        def _tag(name):
            m = re.search(rf"<{name}>(.*?)\n", block, re.IGNORECASE)
            return m.group(1).strip() if m else ""

        raw_date = _tag("DTPOSTED")[:8]
        if len(raw_date) == 8:
            raw_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

        concept = _tag("MEMO") or _tag("NAME") or _tag("PAYEE")
        amount  = _parse_amount(_tag("TRNAMT"))

        if raw_date and amount != 0.0:
            transactions.append({
                "date":     raw_date,
                "concept":  concept,
                "amount":   amount,
                "balance":  None,
                "category": _categorise(concept),
            })
    return transactions


# ── Public API ─────────────────────────────────────────────────────────────

def parse(path: str | Path) -> dict[str, Any]:
    """
    Parse a bank statement file and return transactions + summary.

    Returns:
      {
        "ok": bool,
        "bank": str,
        "transactions": list[dict],
        "count": int,
        "total_income": float,
        "total_expenses": float,
        "net": float,
        "by_category": dict,
        "date_range": [str, str]
      }
    """
    p = Path(path)
    suffix = p.suffix.lower()

    try:
        if suffix in (".xlsx", ".xls"):
            txns = _parse_xlsx(p)
            bank = "generic"
        elif suffix in (".ofx", ".qfx"):
            text = p.read_text(encoding="latin-1", errors="replace")
            txns = _parse_ofx(text)
            bank = "ofx"
        else:
            text = p.read_text(encoding="utf-8", errors="replace")
            if not text:
                text = p.read_text(encoding="latin-1", errors="replace")
            bank = _detect_bank(text[:500])
            txns = _parse_csv(text)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    if not txns:
        return {"ok": False, "error": "No se detectaron transacciones. Verifica el formato del archivo."}

    income   = sum(t["amount"] for t in txns if t["amount"] > 0)
    expenses = sum(t["amount"] for t in txns if t["amount"] < 0)
    by_cat: dict[str, float] = {}
    for t in txns:
        by_cat[t["category"]] = round(by_cat.get(t["category"], 0) + abs(t["amount"]), 2)

    dates = sorted(t["date"] for t in txns if t["date"])

    return {
        "ok":             True,
        "bank":           bank,
        "transactions":   txns,
        "count":          len(txns),
        "total_income":   round(income, 2),
        "total_expenses": round(expenses, 2),
        "net":            round(income + expenses, 2),
        "by_category":    dict(sorted(by_cat.items(), key=lambda x: x[1], reverse=True)),
        "date_range":     [dates[0], dates[-1]] if dates else ["", ""],
    }


def ingest_statement(path: str | Path, domain: str = "finanzas") -> dict[str, Any]:
    """Parse and store a bank statement in the artifact store."""
    result = parse(path)
    if not result["ok"]:
        return result

    from core.docs.artifact_store import ingest
    from core.docs.financial_extractor import FINANCIAL_KEYWORDS

    summary_text = (
        f"Extracto bancario: {result['bank']}\n"
        f"Período: {result['date_range'][0]} – {result['date_range'][1]}\n"
        f"Transacciones: {result['count']}\n"
        f"Ingresos: {result['total_income']} €  |  Gastos: {result['total_expenses']} €  |  Neto: {result['net']} €\n\n"
        "Transacciones:\n" +
        "\n".join(
            f"{t['date']}  {t['concept'][:50]:50s}  {t['amount']:>10.2f} €  [{t['category']}]"
            for t in result["transactions"][:200]
        )
    )

    ar = ingest(
        text=summary_text,
        source=f"bank:{Path(path).name}",
        domain=domain,
        artifact_type="bank_statement",
        filename=Path(path).name,
        source_date=result["date_range"][1] or __import__("datetime").date.today().isoformat(),
        financial={
            "amount":   abs(result["total_expenses"]),
            "concept":  f"Extracto {result['bank']} {result['date_range']}",
            "currency": "EUR",
        },
    )

    result["artifact_id"] = ar.artifact_id
    result["artifact_status"] = ar.status
    return result
