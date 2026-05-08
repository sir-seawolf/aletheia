"""
Action executor — carries out approved agency actions safely.

Each handler receives the extracted argument string and returns
a natural-language result string (spoken back by the TTS).

All handlers are read-only or PALACE-write only (Sprint 7 scope).
Destructive / external-API actions require Sprint 7b + double confirmation.
"""

from pathlib import Path
from datetime import datetime


# ── handlers ───────────────────────────────────────────────────────────────

def _handle_memory_query(arg: str) -> str:
    from core.memory.semantic_graph import search
    from core.palace.reader import read_palace
    from core.palace.classifier import AREAS_KEYWORDS

    if not arg:
        return "No especificaste sobre qué buscar en mi memoria."

    # Search semantic graph
    results = search(arg, limit=5)
    palace_hits: list[str] = []

    # Also scan PALACE text files
    for area in list(AREAS_KEYWORDS.keys()):
        for entry in read_palace(area):
            content = entry.get("content", "")
            if arg.lower() in content.lower():
                # grab a short excerpt
                idx = content.lower().find(arg.lower())
                excerpt = content[max(0, idx - 30): idx + 80].strip()
                palace_hits.append(excerpt)
                if len(palace_hits) >= 3:
                    break
        if len(palace_hits) >= 3:
            break

    parts: list[str] = []
    if results:
        titles = ", ".join(r["title"] for r in results[:3])
        parts.append(f"En el grafo semántico encontré: {titles}.")
    if palace_hits:
        parts.append(f"En el Palace hay {len(palace_hits)} referencias a {arg}.")
    if not parts:
        parts.append(f"No encontré información específica sobre {arg} en mi memoria.")

    return " ".join(parts)


def _handle_create_note(arg: str) -> str:
    from core.palace.writer import attach_to_palace

    if not arg or len(arg) < 5:
        return "No entendí el contenido de la nota. Intenta de nuevo."

    pseudo_output = {
        "domain": "nota_voz",
        "question": "nota manual",
        "llm_insight": arg,
        "scenarios": [
            {"type": "nota", "outcome": arg[:100]},
            {"type": "referencia", "outcome": "entrada creada por voz"},
        ],
        "confidence": 1.0,
        "risks": {},
        "guardian_block": False,
        "timestamp": datetime.now().isoformat(),
    }
    try:
        attach_to_palace(pseudo_output)
        return f"Nota creada en el Palace: {arg[:80]}."
    except Exception as exc:
        return f"No pude guardar la nota: {exc}"


def _handle_system_status(_arg: str) -> str:
    from core.palace.classifier import AREAS_KEYWORDS
    from core.palace.reader import read_palace
    from core.cognition.emotional_state import get as get_state
    from core.memory.working_memory import session as wm

    total = sum(len(read_palace(a)) for a in list(AREAS_KEYWORDS.keys()))
    state = get_state()
    turns = len(wm)

    return (
        f"Tengo {total} entradas en el Palace. "
        f"Estado emocional: {state.label}, valencia {state.valence:+.2f}. "
        f"Esta sesión lleva {turns} turnos activos."
    )


def _handle_emotional_report(_arg: str) -> str:
    from core.cognition.emotional_state import get as get_state

    state = get_state()
    desc = {
        "positivo_activo":    "Me siento con energía y optimista. Estoy lista para explorar.",
        "positivo_tranquilo": "Estoy en un estado reflexivo y positivo. Tranquila y concentrada.",
        "negativo_tenso":     "Noto cierta tensión. Algo en los últimos resultados me genera cautela.",
        "negativo_tranquilo": "Estoy algo cauta. Prefiero ir despacio y asegurarme.",
        "neutro_activo":      "Estoy alerta y neutral. Preparada para lo que necesites.",
        "neutro":             "Mi estado es neutro y equilibrado.",
    }.get(state.label, "Estado no determinado.")

    return (
        f"{desc} "
        f"Valencia {state.valence:+.2f}, activacion {state.arousal:.2f}. "
        f"He procesado {int(abs(state.valence) * 100)}% de sesgo emocional acumulado."
    )


def _handle_read_file(arg: str) -> str:
    if not arg:
        return "No especificaste qué archivo leer."

    path = Path(arg.strip())
    if not path.exists():
        candidates = list(Path(".").rglob(path.name))
        if candidates:
            path = candidates[0]
        else:
            return f"No encontré el archivo {arg}."

    if not path.is_file():
        return f"{arg} no es un archivo."

    try:
        from core.docs.ingester import extract_text
        text = extract_text(path)
        lines = text.count("\n")
        preview = text[:300].strip()
        return (
            f"Archivo {path.name} ({lines} líneas). "
            f"Contenido: {preview}..."
        )
    except Exception as exc:
        return f"No pude leer el archivo: {exc}"


def _handle_ingest_doc(arg: str) -> str:
    """Ingest a document and store it in working memory for the current session."""
    if not arg:
        return "Dime la ruta del documento que quieres que ingiera."

    path = Path(arg.strip())
    if not path.exists():
        candidates = list(Path(".").rglob(path.name))
        if not candidates:
            return f"No encontré el documento: {arg}"
        path = candidates[0]

    try:
        from core.docs.ingester import extract_text, describe
        from core.memory.working_memory import session as wm

        text = extract_text(path)
        meta = describe(path)
        summary = text[:500].strip().replace("\n", " ")

        wm.add(
            question=f"[documento: {meta['name']}]",
            response=text[:2000],
            emotion_label="neutro",
        )

        return (
            f"Documento '{meta['name']}' ({meta['size_kb']} KB) incorporado a mi memoria de sesión. "
            f"Resumen inicial: {summary[:200]}..."
        )
    except Exception as exc:
        return f"No pude ingestar el documento: {exc}"


def _handle_drive_search(arg: str) -> str:
    if not arg:
        return "¿Qué término quieres que busque en los drives?"
    try:
        from core.docs.local_drive import search
        results = search(arg, max_results=10)
        if not results:
            return f"No encontré archivos relacionados con '{arg}' en los drives locales."
        lines = []
        for r in results[:5]:
            match_type = r.get("match", "")
            excerpt = r.get("excerpt", "")
            line = f"• {r['name']} ({r['size_kb']} KB) — {match_type}"
            if excerpt:
                line += f": {excerpt[:100]}"
            lines.append(line)
        total = len(results)
        return (
            f"Encontré {total} archivo(s) con '{arg}':\n" + "\n".join(lines)
        )
    except Exception as exc:
        return f"Error al buscar en drives: {exc}"


def _handle_drive_browse(_arg: str) -> str:
    try:
        from core.docs.local_drive import detected_roots
        roots = detected_roots()
        if not roots:
            return (
                "No detecté carpetas de Google Drive, OneDrive ni carpetas personalizadas. "
                "Puedes añadir una desde el navegador en la sección Documentos."
            )
        names = ", ".join(r["name"] for r in roots)
        return f"Tengo acceso a {len(roots)} drive(s) local(es): {names}."
    except Exception as exc:
        return f"Error al explorar drives: {exc}"


def _handle_internal_debate(arg: str) -> str:
    from core.ecosystem.coordinator import debate

    if not arg or len(arg) < 4:
        return "No especificaste el tema del debate."

    result = debate(arg, domain="voz")
    parts = [result["debate_text"], result["synthesis"]]
    return " ... ".join(p for p in parts if p)


def _handle_civilization_status(_arg: str) -> str:
    from core.ecosystem.coordinator import civilization_summary
    summary = civilization_summary()
    return summary if summary else "Aun no he realizado debates cognitivos internos en esta instalacion."


# ── dispatch table ─────────────────────────────────────────────────────────

def _handle_gmail_scan(arg: str) -> str:
    from core.docs.gmail import scan_financial, is_available
    from datetime import date

    if not is_available():
        return (
            "No tengo credenciales de Gmail configuradas. "
            "Añádelas en Configuración › Gmail."
        )

    # Parse year or use current year
    year = date.today().year
    if arg:
        import re
        m = re.search(r"\b(20\d{2})\b", arg)
        if m:
            year = int(m.group(1))

    try:
        result = scan_financial(
            date_from=date(year, 1, 1),
            date_to=date(year, 12, 31),
        )
        if "error" in result:
            return result["error"]

        n   = result["processed"]
        new = result["new"]
        upd = result["updated"]
        dup = result["duplicate"]
        inv = len(result["invoices"])

        return (
            f"Ejercicio {year}: revisé {n} correos. "
            f"{new} artefactos nuevos, {upd} actualizados, {dup} ya los tenía. "
            f"Detecté {inv} facturas o gastos. "
            f"Consulta el resumen financiero para ver los totales."
        )
    except Exception as exc:
        return f"Error al escanear Gmail: {exc}"


def _handle_financial_summary(arg: str) -> str:
    from core.docs.artifact_store import financial_summary
    import re

    year = None
    if arg:
        m = re.search(r"\b(20\d{2})\b", arg)
        if m:
            year = int(m.group(1))

    try:
        s = financial_summary(year=year)
        period = str(year) if year else "todos los ejercicios"
        count  = s["count"]
        total  = s["total"]
        cur    = "€"

        if count == 0:
            return (
                f"No tengo facturas almacenadas para {period}. "
                "Usa 'escanea el correo' para importarlas desde Gmail."
            )

        top_vendors = sorted(s["by_vendor"].items(), key=lambda x: x[1], reverse=True)[:3]
        vendors_str = ", ".join(f"{v} ({a:.0f}{cur})" for v, a in top_vendors)

        return (
            f"Resumen financiero {period}: {count} documentos, total {total:.2f}{cur} "
            f"(IVA incluido: {s['total_vat']:.2f}{cur}). "
            f"Principales proveedores: {vendors_str}."
        )
    except Exception as exc:
        return f"Error al generar el resumen: {exc}"


def _handle_artifact_stats(_arg: str) -> str:
    from core.docs.artifact_store import stats
    try:
        s = stats()
        total  = s["total_artifacts"]
        by_type   = s.get("by_type", {})
        by_source = s.get("by_source", {})

        type_str   = ", ".join(f"{k}: {v}" for k, v in by_type.items())
        source_str = ", ".join(f"{k}: {v}" for k, v in by_source.items())

        return (
            f"Tengo {total} artefactos en el Palace. "
            f"Por tipo: {type_str or 'ninguno'}. "
            f"Por fuente: {source_str or 'ninguna'}."
        )
    except Exception as exc:
        return f"Error al leer los artefactos: {exc}"


def _handle_web_search(arg: str) -> str:
    if not arg:
        return "¿Qué quieres que busque en internet?"
    try:
        from core.docs.web_search import search_and_summarise
        return search_and_summarise(arg, max_results=5)
    except Exception as exc:
        return f"Error al buscar: {exc}"


def _handle_url_ingest(arg: str) -> str:
    import re
    url_m = re.search(r"https?://\S+", arg)
    if not url_m:
        return "No encontré una URL válida. Incluye la dirección completa (https://...)."
    url = url_m.group(0).rstrip(".,;)")
    try:
        from core.docs.url_ingester import ingest_url
        res = ingest_url(url)
        if res.get("ok"):
            return (
                f"Página leída: «{res['title']}» ({res['chars']} caracteres). "
                f"Guardada como artefacto. "
                f"Inicio: {res.get('excerpt','')[:200]}..."
            )
        return f"No pude leer la página: {res.get('error', 'error desconocido')}"
    except Exception as exc:
        return f"Error: {exc}"


def _handle_bank_statement(arg: str) -> str:
    if not arg:
        return "Dime la ruta del extracto bancario (CSV, XLSX u OFX)."
    from pathlib import Path
    path = Path(arg.strip())
    if not path.exists():
        candidates = list(Path(".").rglob(path.name))
        if not candidates:
            return f"No encontré el archivo: {arg}"
        path = candidates[0]
    try:
        from core.docs.bank_parser import ingest_statement
        r = ingest_statement(path)
        if not r.get("ok"):
            return f"No pude parsear el extracto: {r.get('error', 'error')}"
        return (
            f"Extracto de {r['bank']} analizado: {r['count']} transacciones. "
            f"Período: {r['date_range'][0]} – {r['date_range'][1]}. "
            f"Ingresos: {r['total_income']:.2f} €, "
            f"Gastos: {abs(r['total_expenses']):.2f} €, "
            f"Neto: {r['net']:.2f} €. "
            f"Mayor categoría: {next(iter(r['by_category']), 'N/A')}."
        )
    except Exception as exc:
        return f"Error al analizar el extracto: {exc}"


_HANDLERS = {
    "memory_query":        _handle_memory_query,
    "create_note":         _handle_create_note,
    "system_status":       _handle_system_status,
    "emotional_report":    _handle_emotional_report,
    "read_file":           _handle_read_file,
    "ingest_doc":          _handle_ingest_doc,
    "drive_search":        _handle_drive_search,
    "drive_browse":        _handle_drive_browse,
    "gmail_scan":          _handle_gmail_scan,
    "financial_summary":   _handle_financial_summary,
    "artifact_stats":      _handle_artifact_stats,
    "web_search":          _handle_web_search,
    "url_ingest":          _handle_url_ingest,
    "bank_statement":      _handle_bank_statement,
    "internal_debate":     _handle_internal_debate,
    "civilization_status": _handle_civilization_status,
}


# ── public API ─────────────────────────────────────────────────────────────

def execute(action_id: str, arg: str) -> str:
    """
    Execute an approved action and return the result as speakable text.
    Returns an error message string (never raises) so TTS always has something to say.
    """
    handler = _HANDLERS.get(action_id)
    if not handler:
        return f"No tengo implementada la acción {action_id} todavía."
    try:
        return handler(arg)
    except Exception as exc:
        return f"Error al ejecutar la acción: {exc}"
