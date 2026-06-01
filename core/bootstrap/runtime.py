"""
Runtime FastAPI app for Aletheia Kernel v1.0.
Lightweight - kernel init via CLI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional


@asynccontextmanager
async def lifespan(_app: FastAPI):
    mode = os.getenv("ALETHEIA_MODE", "DEV")
    print(f"Aletheia API ready in {mode} mode")
    print("Endpoints: /health /api/simulate /docs")
    # Pre-warm Whisper so first browser voice request is fast
    try:
        import asyncio as _aio
        await _aio.get_event_loop().run_in_executor(None, _prewarm_whisper)
    except Exception:
        pass
    yield


def _prewarm_whisper():
    try:
        from core.voice.listener import preload
        preload()
    except Exception:
        pass


app = FastAPI(title="Aletheia Kernel v1.0", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"system": "Aletheia Kernel v1.0", "status": "ready", "endpoints": ["/health", "/api/simulate", "/docs"]}

@app.get("/health")
async def health():
    """Basic API health."""
    return {"status": "healthy", "kernel": "v1.0"}

@app.get("/system/health")
async def system_health():
    """Full system health (memory/LLM pre-checked by CLI)."""
    return {"status": "healthy", "components": {"api": "ok", "contract": "enforced"}}

import re as _re

# ── Action request patterns ────────────────────────────────────────────────
_GMAIL_SCAN_RE = _re.compile(
    r"(importar?|escanear?|revisar?|traer?|descargar?|sincronizar?)\s+.*(correo|gmail|email|mail|facturas?|gastos?)"
    r"|facturas?.*(del?\s+a[ñn]o|del?\s+ejercicio|del?\s+mes|de\s+este|hasta\s+ahora)"
    r"|(correo|gmail|email).*(importar?|escanear?|revisar?|facturas?)"
    r"|puedes?\s+.*(importar?|escanear?|traer?).*(correo|gmail|email|facturas?)",
    _re.IGNORECASE,
)

_DRIVE_SEARCH_RE = _re.compile(
    r"(buscar?|encontrar?|localizar?)\s+.*(drive|onedrive|documentos?|carpetas?|archivos?)"
    r"|(drive|onedrive)\s+.*(buscar?|que\s+hay|mostrar?)",
    _re.IGNORECASE,
)

_FINANCIAL_SUMMARY_RE = _re.compile(
    r"(resumen|total|cuanto|cuánto|qu[eé]\s+he?\s+gastado?|gastos?\s+de[l\s])"
    r".*(a[ñn]o|mes|trimestre|ejercicio|facturas?|\d{4})",
    _re.IGNORECASE,
)

_WEB_SEARCH_RE = _re.compile(
    r"(busca?r?\s+en\s+(internet|web|google|online)|"
    r"qu[eé]\s+dice\s+(internet|la\s+web)|"
    r"busca?\s+informaci[oó]n\s+(sobre|de|acerca)|"
    r"noticias?\s+(sobre|de|acerca)|"
    r"precio\s+(actual|hoy|ahora)|"
    r"cu[aá]nto\s+(vale|cuesta|cotiza))",
    _re.IGNORECASE,
)

_URL_INGEST_RE = _re.compile(
    r"(https?://\S+|lee\s+(esta|la)\s+(p[aá]gina|url|web)|"
    r"analiza\s+(esta|la)\s+(p[aá]gina|url|web)|"
    r"ingesta\s+(esta|la)\s+(p[aá]gina|url|web))",
    _re.IGNORECASE,
)

_FISCAL_RE = _re.compile(
    r"(cu[aá]nto\s+(pago|debo|tengo\s+que\s+pagar)\s+(de\s+)?(irpf|renta|impuesto|hacienda|iva)"
    r"|declaraci[oó]n\s+de\s+la\s+renta"
    r"|modelo\s+(130|303|111|115)"
    r"|pago\s+fraccionado"
    r"|iva\s+(del?\s+trimestre|trimestral|a\s+ingresar|a\s+pagar)"
    r"|calcula?\s+(el\s+)?(irpf|iva|impuesto)"
    r"|tipo\s+efectivo\s+(de\s+)?(irpf|impuesto)"
    r"|retenci[oó]n\s+(de\s+)?(irpf|factura)"
    r"|resumen\s+fiscal"
    r"|cu[aá]nto\s+(me\s+queda|queda)\s+(pagar\s+a\s+hacienda|de\s+irpf|de\s+iva))",
    _re.IGNORECASE,
)

_CALENDAR_READ_RE = _re.compile(
    r"(qu[eé]\s+tengo\s+(hoy|ma[ñn]ana|esta\s+semana|el\s+lunes|el\s+martes|el\s+mi[eé]rcoles|el\s+jueves|el\s+viernes)"
    r"|agenda\s+(de\s+hoy|de\s+ma[ñn]ana|de\s+esta\s+semana|del\s+d[ií]a)"
    r"|(mis?\s+)?(eventos?|citas?|reuniones?|calendario)\s+(de\s+hoy|de\s+ma[ñn]ana|esta\s+semana|pr[oó]xim\w+)"
    r"|pr[oó]xim\w+\s+(eventos?|citas?|reuniones?)"
    r"|qu[eé]\s+hay\s+en\s+(el\s+)?calendario"
    r"|mu[eé]strame\s+(el\s+)?calendario"
    r"|tengo\s+algo\s+(hoy|ma[ñn]ana|esta\s+semana))",
    _re.IGNORECASE,
)

_CALENDAR_CREATE_RE = _re.compile(
    r"(crea?r?\s+(una?\s+)?(cita|evento|reuni[oó]n|recordatorio|tarea)\s+(en\s+el\s+calendario|para\s+el|el\s+d[ií]a)"
    r"|a[ñn]ade?\s+(al\s+calendario|una?\s+(cita|evento|reuni[oó]n))"
    r"|ag[eé]nda?\s+(una?\s+)?(reuni[oó]n|cita|evento)"
    r"|programa?\s+(una?\s+)?(reuni[oó]n|cita|evento|llamada)"
    r"|pon\s+(en\s+el\s+calendario|una?\s+(cita|reuni[oó]n)))",
    _re.IGNORECASE,
)


def _detect_action(question: str) -> str | None:
    """Return action key if question is a doc/data action request, else None."""
    if _GMAIL_SCAN_RE.search(question):
        return "gmail_scan"
    if _URL_INGEST_RE.search(question):
        return "url_ingest"
    if _WEB_SEARCH_RE.search(question):
        return "web_search"
    if _DRIVE_SEARCH_RE.search(question):
        return "drive_search"
    if _FINANCIAL_SUMMARY_RE.search(question):
        return "financial_summary"
    if _FISCAL_RE.search(question):
        return "fiscal"
    if _CALENDAR_CREATE_RE.search(question):
        return "calendar_create"
    if _CALENDAR_READ_RE.search(question):
        return "calendar_read"
    return None


def _execute_action_api(action: str, question: str, domain: str = "general") -> dict:
    """Run a doc action and return a simulate-compatible response dict."""
    import re
    from datetime import date

    insight = ""
    extra: dict = {}

    if action == "gmail_scan":
        from core.docs.gmail import scan_financial, is_available
        if not is_available():
            insight = (
                "Para importar facturas del correo necesito que configures las credenciales de Gmail. "
                "Ve a Configuración → Gmail y sube tu credentials.json de Google Cloud Console."
            )
        else:
            year_m = re.search(r"\b(20\d{2})\b", question)
            year = int(year_m.group(1)) if year_m else date.today().year
            result = scan_financial(date(year, 1, 1), date(year, 12, 31))
            if "error" in result:
                insight = result["error"]
            else:
                n, new, upd, dup = result["processed"], result["new"], result["updated"], result["duplicate"]
                inv = result["invoices"]
                total = sum(i.get("amount", 0) for i in inv)
                insight = (
                    f"He escaneado {n} correos del ejercicio {year}. "
                    f"Encontré {len(inv)} facturas/gastos por un total de {total:.2f} €. "
                    f"Artefactos nuevos: {new}, actualizados: {upd}, ya existentes: {dup}. "
                    "Puedes ver el detalle completo en Documentos → Artefactos."
                )
                extra["gmail_scan"] = result

    elif action == "drive_search":
        from core.docs.local_drive import search, detected_roots
        roots = detected_roots()
        if not roots:
            insight = "No tengo drives locales configurados. Añade una carpeta en Configuración → Carpetas locales."
        else:
            # Extract search term from question
            q_clean = re.sub(r"(busca?|encuentra?|localiza?|en\s+drive|en\s+onedrive|documentos?)", "", question, flags=re.IGNORECASE).strip()
            results = search(q_clean or question, max_results=8)
            if not results:
                insight = f"No encontré archivos relacionados con '{q_clean}' en los drives locales ({', '.join(r['name'] for r in roots)})."
            else:
                names = ", ".join(r["name"] for r in results[:5])
                insight = f"Encontré {len(results)} archivo(s) en drives locales: {names}. Ábrelos desde Documentos → Explorar."
            extra["drive_results"] = results

    elif action == "web_search":
        from core.docs.web_search import search as _ws, search_and_summarise
        q_clean = re.sub(
            r"(busca?r?\s+en\s+(internet|web|google|online)|"
            r"qu[eé]\s+dice\s+(internet|la\s+web)|"
            r"busca?\s+informaci[oó]n\s+(sobre|de)|"
            r"noticias?\s+(sobre|de))",
            "", question, flags=re.IGNORECASE
        ).strip() or question
        results = _ws(q_clean, max_results=6)
        summary = search_and_summarise(q_clean, max_results=6)
        insight = (
            f"He buscado en la web: «{q_clean}»\n\n{summary[:1200]}\n\n"
            "Puedo analizar alguno de estos resultados en profundidad si me dices cuál."
        )
        extra["web_results"] = results

    elif action == "url_ingest":
        url_m = re.search(r"https?://\S+", question)
        if not url_m:
            insight = "No detecté una URL en tu mensaje. Incluye la dirección completa (https://...)."
        else:
            url = url_m.group(0).rstrip(".,;)")
            from core.docs.url_ingester import ingest_url
            res = ingest_url(url, domain=domain)
            if res.get("ok"):
                insight = (
                    f"He leído la página «{res['title']}» ({res['chars']} caracteres). "
                    f"Guardada como artefacto. "
                    f"Extracto: {res.get('excerpt', '')[:300]}..."
                )
                extra["url_result"] = res
            else:
                insight = f"No pude leer la página: {res.get('error', 'error desconocido')}"

    elif action == "financial_summary":
        from core.docs.artifact_store import financial_summary
        year_m = re.search(r"\b(20\d{2})\b", question)
        year = int(year_m.group(1)) if year_m else date.today().year
        s = financial_summary(year=year)
        if s["count"] == 0:
            insight = (
                f"No tengo facturas almacenadas para {year}. "
                "Usa 'importa del correo' o sube documentos en la sección Documentos."
            )
        else:
            top = sorted(s["by_vendor"].items(), key=lambda x: x[1], reverse=True)[:3]
            vendors = ", ".join(f"{v} ({a:.0f}€)" for v, a in top)
            insight = (
                f"Resumen financiero {year}: {s['count']} documentos, "
                f"total {s['total']:.2f} € (IVA: {s['total_vat']:.2f} €). "
                f"Principales: {vendors}."
            )
        extra["financial_summary"] = s

    elif action == "fiscal":
        from core.docs import fiscal
        q_lower = question.lower()

        # IVA puntual: "¿cuánto es el IVA de 1500€?"
        amount_m = re.search(r"(\d[\d.,]*)\s*(?:€|euros?)?", question)

        if any(w in q_lower for w in ("modelo 303", "iva trimestral", "iva del trimestre", "iva a ingresar", "modelo303")):
            # Pide datos numéricos — devuelve explicación de qué introducir
            year_m = re.search(r"\b(20\d{2})\b", question)
            yr = int(year_m.group(1)) if year_m else date.today().year
            trim_m = re.search(r"\b([1-4])[ºoer°]?\s*trimestre\b|[tT](\d)\b", question)
            trim = int((trim_m.group(1) or trim_m.group(2)) if trim_m else ((date.today().month - 1) // 3 + 1))
            insight = (
                f"Para el Modelo 303 T{trim}/{yr} necesito:\n"
                "  • Base imponible gravada al 21% (ingresos sin IVA)\n"
                "  • Base imponible gravada al 10% (si aplica)\n"
                "  • IVA soportado total (IVA de tus facturas de compra)\n\n"
                "Dime los importes y lo calculo al momento.\n"
                "Ejemplo: «Base 21%: 8000€, IVA soportado: 420€»"
            )
            # Try auto-calc if we have artifact data
            try:
                res = fiscal.resumen_fiscal(yr)
                if res["iva_repercutido"] > 0:
                    r = fiscal.calcular_iva(
                        base_imponible_21=res["ingresos_brutos"],
                        iva_soportado=res["iva_soportado"],
                        trimestre=trim,
                        year=yr,
                    )
                    insight = fiscal.format_iva(r) + f"\n\n⚠️ {res['advertencia']}"
                    extra["iva"] = r.to_dict()
            except Exception:
                pass

        elif any(w in q_lower for w in ("modelo 130", "pago fraccionado", "modelo130")):
            year_m = re.search(r"\b(20\d{2})\b", question)
            yr = int(year_m.group(1)) if year_m else date.today().year
            trim_m = re.search(r"\b([1-4])[ºoer°]?\s*trimestre\b|[tT](\d)\b", question)
            trim = int((trim_m.group(1) or trim_m.group(2)) if trim_m else ((date.today().month - 1) // 3 + 1))
            try:
                res = fiscal.resumen_fiscal(yr)
                r = fiscal.calcular_modelo_130(
                    ingresos_acumulados=res["ingresos_brutos"],
                    gastos_acumulados=res["gastos_deducibles"],
                    trimestre=trim,
                    year=yr,
                )
                insight = fiscal.format_modelo130(r) + f"\n\n⚠️ {res['advertencia']}"
                extra["modelo130"] = r.to_dict()
            except Exception:
                insight = (
                    f"Modelo 130 T{trim}/{yr}: necesito ingresos y gastos acumulados del año. "
                    "Importa tus facturas primero o dime los importes directamente."
                )

        elif any(w in q_lower for w in ("iva de", "iva del", "cuánto es el iva", "cuanto es el iva", "precio con iva", "sin iva")):
            if amount_m:
                raw = amount_m.group(1).replace(".", "").replace(",", ".")
                try:
                    base = float(raw)
                    tipo = "reducido" if any(w in q_lower for w in ("10%", "reducido")) else \
                           "superreducido" if any(w in q_lower for w in ("4%", "superreducido")) else "general"
                    if "sin iva" in q_lower or "base" in q_lower:
                        r = fiscal.desglosar_iva(base, tipo)
                        insight = (
                            f"Desglose IVA ({r['porcentaje']}%):\n"
                            f"  Total con IVA: {r['total']:,.2f} €\n"
                            f"  Base imponible: {r['base']:,.2f} €\n"
                            f"  IVA: {r['iva']:,.2f} €"
                        )
                    else:
                        r = fiscal.precio_con_iva(base, tipo)
                        insight = (
                            f"IVA {tipo} ({r['porcentaje']}%) sobre {r['base']:,.2f} €:\n"
                            f"  IVA: {r['iva']:,.2f} €\n"
                            f"  Total: {r['total']:,.2f} €"
                        )
                    extra["iva_calculo"] = r
                except ValueError:
                    insight = "No pude leer el importe. Escríbelo así: «IVA de 1500€»"
            else:
                insight = "¿Sobre qué importe quieres calcular el IVA? Dime la cantidad."

        else:
            # IRPF / renta general
            year_m = re.search(r"\b(20\d{2})\b", question)
            yr = int(year_m.group(1)) if year_m else date.today().year
            amount_bruto = None
            if amount_m:
                raw = amount_m.group(1).replace(".", "").replace(",", ".")
                try:
                    amount_bruto = float(raw)
                except ValueError:
                    pass

            autonomo = any(w in q_lower for w in ("autónomo", "autonomo", "freelance", "cuenta propia"))

            if amount_bruto:
                r = fiscal.calcular_irpf(amount_bruto, autonomo=autonomo)
                insight = fiscal.format_irpf(r)
                extra["irpf"] = r.to_dict()
            else:
                # Try from artifact data
                try:
                    res = fiscal.resumen_fiscal(yr)
                    if res["ingresos_brutos"] > 0:
                        r_obj = fiscal.IRPFResult(**{k: v for k, v in res["irpf"].items() if k != "tipo_efectivo_pct"})
                        insight = fiscal.format_irpf(r_obj) + f"\n\n⚠️ {res['advertencia']}"
                        extra["fiscal_resumen"] = res
                    else:
                        insight = (
                            "No tengo ingresos registrados para estimar el IRPF. "
                            "Importa tus facturas o dime tu renta bruta anual: «IRPF de 35000€»"
                        )
                except Exception:
                    insight = (
                        "Dime tu renta bruta anual y te calculo el IRPF. "
                        "Ejemplo: «¿cuánto IRPF pago con 40.000€ brutos?»"
                    )

    elif action == "calendar_read":
        from core.docs.gcalendar import list_events, today_events, format_summary, is_available as _cal_avail
        if not _cal_avail():
            insight = (
                "Para ver tu calendario necesito las credenciales de Google Calendar. "
                "Ve a Configuración → Calendario y sube tu credentials.json de Google Cloud Console."
            )
        else:
            q_lower = question.lower()
            if any(w in q_lower for w in ("hoy", "día", "dia", "today")):
                result = today_events()
                label = "hoy"
            elif any(w in q_lower for w in ("mañana", "manana", "tomorrow")):
                from core.docs.gcalendar import list_events as _le
                import datetime as _dt
                tomorrow_str = (date.today() + _dt.timedelta(days=1)).isoformat()
                result = _le(days_back=0, days_ahead=2, max_results=10)
                result["events"] = [e for e in result.get("events", []) if e["start"].startswith(tomorrow_str)]
                result["count"] = len(result["events"])
                label = "mañana"
            else:
                result = list_events(days_back=0, days_ahead=7)
                label = "los próximos 7 días"
            if "error" in result:
                insight = f"Error al leer el calendario: {result['error']}"
            elif not result.get("events"):
                insight = f"No tienes eventos para {label}."
            else:
                summary = format_summary(result["events"])
                insight = f"Tu agenda para {label} ({result['count']} evento(s)):\n{summary}"
            extra["calendar"] = result

    elif action == "calendar_create":
        from core.docs.gcalendar import is_available as _cal_avail
        if not _cal_avail():
            insight = (
                "Para crear eventos necesito las credenciales de Google Calendar. "
                "Ve a Configuración → Calendario."
            )
        else:
            # Parse title and date from the question using LLM
            from core.llm import router as llm_router
            parse_prompt = (
                f"Extrae del siguiente texto el título del evento, la fecha y hora de inicio "
                f"y la fecha y hora de fin en formato ISO 8601 con zona horaria +02:00 (Europa/Madrid). "
                f"Si no hay hora, usa 09:00 para inicio y 10:00 para fin. "
                f"Si no hay fecha, usa mañana. "
                f"Responde ÚNICAMENTE con JSON: "
                f'{{\"title\": \"...\", \"start\": \"YYYY-MM-DDTHH:MM:SS+02:00\", \"end\": \"YYYY-MM-DDTHH:MM:SS+02:00\", \"description\": \"...\"}}. '
                f"Texto: '{question}'"
            )
            try:
                parsed_str = llm_router.generate(task="chat", prompt=parse_prompt, context={"domain": "calendar"}, temp=0.1)
                import json as _json
                json_m = re.search(r"\{.*\}", parsed_str, re.DOTALL)
                if json_m:
                    ev_data = _json.loads(json_m.group(0))
                    from core.docs.gcalendar import create_event
                    result = create_event(
                        title=ev_data.get("title", "Nuevo evento"),
                        start_iso=ev_data["start"],
                        end_iso=ev_data["end"],
                        description=ev_data.get("description", ""),
                    )
                    if result.get("created"):
                        ev = result["event"]
                        insight = (
                            f"Evento creado: «{ev['title']}» el {ev['start'][:10]} "
                            f"de {ev['start'][11:16]} a {ev['end'][11:16]}."
                        )
                        extra["calendar_created"] = result
                    else:
                        insight = f"No pude crear el evento: {result.get('error', 'error desconocido')}"
                else:
                    insight = "No pude interpretar los datos del evento. Especifica título y fecha con más detalle."
            except Exception as exc:
                insight = f"Error al crear el evento: {exc}"

    return {
        "domain": "finanzas",
        "question": question,
        "llm_insight": insight,
        "scenarios": [],
        "risks": {},
        "confidence": 0.92,
        "guardian_block": False,
        "guardian_recommendation": "Proceder",
        "action_executed": action,
        **extra,
    }


_CONVERSATIONAL_RE_API = _re.compile(
    r"^[¿¡]?\s*(hola|buenos?\s+\w+|qu[eé]\s+tal|c[oó]mo\s+est[aá]s|c[oó]mo\s+te\s+encuentras"
    r"|qu[eé]\s+haces|cu[eé]ntame|qu[eé]\s+eres|qui[eé]n\s+eres|qu[eé]\s+puedes"
    r"|qu[eé]\s+tipo\s+de|c[oó]mo\s+funciona|qu[eé]\s+capacidades|qu[eé]\s+posibilidades"
    r"|qu[eé]\s+sabes|explica\s+c[oó]mo|vamos\s+a\s+ver|a\s+ver\s+qu[eé]"
    r"|mu[eé]strame|qu[eé]\s+piensan|y\s+t[uú]|gracias|adi[oó]s)",
    __import__("re").IGNORECASE,
)


def _is_conversational_api(text: str) -> bool:
    return len(text.split()) <= 20 and bool(_CONVERSATIONAL_RE_API.search(text))


@app.post("/api/simulate")
async def simulate_endpoint(request: Dict):
    """
    Full cognitive simulation with layered routing:
      1. Action requests  (gmail scan, drive search, financial summary) → execute directly
      2. Conversational   (greetings, capability questions)             → LLM chat
      3. Decision queries                                               → full pipeline
    """
    domain   = request.get("domain", "unknown")
    question = request.get("question", "")

    # Layer 1 — action requests
    action = _detect_action(question)
    if action:
        return _execute_action_api(action, question, domain)

    # Layer 2 — conversational
    if _is_conversational_api(question):
        from core.llm import router as llm_router
        prompt = (
            f"Eres Aletheia, una IA cognitiva y acompañante. "
            f"Responde de forma natural, breve y útil a: '{question}'"
        )
        try:
            response = llm_router.generate(
                task="chat",
                prompt=prompt,
                context={"domain": domain},
                temp=0.7,
            )
        except Exception:
            response = "Estoy aquí para ayudarte. ¿En qué quieres que me centre?"
        return {
            "domain": domain,
            "question": question,
            "llm_insight": response or "",
            "scenarios": [],
            "risks": {},
            "confidence": 0.90,
            "guardian_block": False,
            "guardian_recommendation": "Proceder",
            "conversational": True,
        }

    # Layer 3 — full decision pipeline (non-blocking: keeps event loop free for WS)
    import asyncio, functools
    session_id = request.get("session_id") or "local"

    # Open a cognitive trace for this simulation request
    from core.tracing.context import begin_trace, set_trace
    from core.tracing.store import trace_store as _ts
    from core.tracing.trace import TraceBuilder
    _sim_tb = TraceBuilder(session_id=session_id, domain=domain, question=question, source="v1_pipeline")
    set_trace(_sim_tb)

    def _commit_sim_trace(output: dict) -> None:
        try:
            confidence = float(output.get("confidence", 0.7))
            trace = _sim_tb.finish(output=str(output.get("llm_insight", ""))[:120], confidence=confidence)
            _ts.save(trace)
            set_trace(None)
            from core.tracing.shadow import schedule_shadow
            schedule_shadow(session_id, domain, question, trace.output_preview)
        except Exception:
            pass

    from core.orchestrator import process_request
    from core.contracts.contract_lock import validate_final_report
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(process_request, domain, question, session_id=session_id),
    )
    validated = validate_final_report(result)
    _commit_sim_trace(validated)
    return validated

@app.get("/system/metrics")
async def system_metrics():
    """System performance metrics."""
    from core.metrics.system_metrics import get_system_metrics
    return get_system_metrics()

@app.get("/api/profile")
async def get_profile():
    """Return the persisted user profile."""
    from core.identity import user_profile as p
    return p.load()

@app.patch("/api/profile")
async def update_profile(updates: Dict):
    """Merge manual updates into the user profile."""
    from core.identity import user_profile as p
    profile = p.load()
    merged = p.merge(profile, updates)
    p.save(merged)
    return merged

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    await websocket.send_text(f"Connected to Aletheia Kernel v1.0 - session {session_id}")
    await websocket.close()


# ── Docs: upload & ingest ──────────────────────────────────────────────────

@app.post("/api/docs/upload")
async def upload_doc(
    file: UploadFile = File(...),
    domain: str = Form("general"),
    question: Optional[str] = Form(None),
):
    """
    Upload a document (PDF/DOCX/TXT/…), extract its text, and run it through
    the cognitive pipeline.  Returns the standard simulation result plus the
    extracted text excerpt.
    """
    from core.docs.ingester import extract_text
    from core.orchestrator import process_request
    from core.contracts.contract_lock import validate_final_report

    suffix = Path(file.filename or "upload").suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = extract_text(tmp_path)
    finally:
        os.unlink(tmp_path)

    prompt = question or f"Analiza el siguiente documento:\n\n{text[:3000]}"
    full_prompt = f"{prompt}\n\n[Contenido del documento '{file.filename}']:\n{text[:8000]}"

    result = process_request(domain, full_prompt)
    validated = validate_final_report(result)
    validated["doc_excerpt"] = text[:800]
    validated["doc_name"] = file.filename
    return validated


@app.post("/api/docs/ingest_text")
async def ingest_text(body: Dict):
    """
    Ingest raw text (e.g. pasted content) without a file upload.
    Body: { "text": "...", "domain": "...", "question": "..." }
    """
    from core.orchestrator import process_request
    from core.contracts.contract_lock import validate_final_report

    text    = body.get("text", "").strip()
    domain  = body.get("domain", "general")
    question = body.get("question", "") or f"Analiza el siguiente texto:\n\n{text[:3000]}"

    if not text:
        return {"error": "Campo 'text' vacío."}

    full_prompt = f"{question}\n\n[Texto adjunto]:\n{text[:8000]}"
    result = validate_final_report(process_request(domain, full_prompt))
    result["doc_excerpt"] = text[:800]
    return result


# ── Docs: local drive browser ──────────────────────────────────────────────

@app.get("/api/docs/roots")
async def docs_roots():
    """Return detected local Drive / OneDrive / custom folders."""
    from core.docs.local_drive import detected_roots
    from core.docs.gdrive import is_available as gdrive_ok
    from core.docs.onedrive import is_available as onedrive_ok
    return {
        "local": detected_roots(),
        "gdrive_online": gdrive_ok(),
        "onedrive_online": onedrive_ok(),
    }


@app.get("/api/docs/browse")
async def docs_browse(path: str = Query(default="")):
    """List files and subdirectories at *path* (empty = show roots)."""
    from core.docs.local_drive import browse
    return browse(path)


@app.get("/api/docs/search")
async def docs_search(
    q: str = Query(...),
    root: str = Query(default=""),
):
    """Full-text search across local drive folders."""
    from core.docs.local_drive import search
    return {"query": q, "results": search(q, root=root)}


@app.post("/api/docs/add_folder")
async def docs_add_folder(body: Dict):
    """Persist a custom folder path to doc_sources.json."""
    path = body.get("path", "").strip()
    if not path:
        return {"error": "Campo 'path' requerido."}
    from core.docs.local_drive import add_folder
    try:
        return add_folder(path)
    except FileNotFoundError as exc:
        return {"error": str(exc)}


@app.post("/api/docs/read")
async def docs_read(body: Dict):
    """Extract and return text content of a local file."""
    path = body.get("path", "").strip()
    if not path:
        return {"error": "Campo 'path' requerido."}
    from core.docs.local_drive import read_file
    return read_file(path)


# ── Docs: Google Drive online ──────────────────────────────────────────────

@app.get("/api/docs/gdrive/list")
async def gdrive_list(q: str = Query(default="")):
    from core.docs.gdrive import list_files
    return list_files(query=q)


@app.post("/api/docs/gdrive/download")
async def gdrive_download(body: Dict):
    file_id = body.get("file_id", "").strip()
    if not file_id:
        return {"error": "Campo 'file_id' requerido."}
    from core.docs.gdrive import download_file
    return download_file(file_id)


# ── Docs: OneDrive online ──────────────────────────────────────────────────

@app.get("/api/docs/onedrive/list")
async def onedrive_list(q: str = Query(default="")):
    from core.docs.onedrive import list_files
    return list_files(query=q)


@app.post("/api/docs/onedrive/download")
async def onedrive_download(body: Dict):
    item_id = body.get("item_id", "").strip()
    if not item_id:
        return {"error": "Campo 'item_id' requerido."}
    from core.docs.onedrive import download_file
    return download_file(item_id)


# ── Voice: browser STT (Whisper) ───────────────────────────────────────────

@app.post("/api/voice/transcribe")
async def voice_transcribe(audio: UploadFile = File(...)):
    """
    Receive a WAV/WebM audio blob from the browser, transcribe with Whisper,
    and return the text.  Used by the browser voice-input mode.
    """
    suffix = Path(audio.filename or "rec").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        from core.voice.listener import transcribe_file
        text = transcribe_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    return {"text": text or ""}


# ── Artifacts ──────────────────────────────────────────────────────────────

@app.get("/api/artifacts")
async def list_artifacts(
    domain: str = Query(default=""),
    artifact_type: str = Query(default=""),
    date_from: str = Query(default=""),
    date_to: str = Query(default=""),
    limit: int = Query(default=100),
):
    from core.docs.artifact_store import query
    return query(
        domain=domain or None,
        artifact_type=artifact_type or None,
        date_from=date_from or None,
        date_to=date_to or None,
        limit=limit,
    )


@app.get("/api/artifacts/stats")
async def artifact_stats():
    from core.docs.artifact_store import stats
    return stats()


@app.get("/api/artifacts/financial_summary")
async def financial_summary(year: int = Query(default=0)):
    from core.docs.artifact_store import financial_summary as fs
    return fs(year=year or None)


@app.get("/api/artifacts/{artifact_id}/text")
async def artifact_text(artifact_id: str):
    from core.docs.artifact_store import get_text
    text = get_text(artifact_id)
    if text is None:
        return {"error": "Artefacto no encontrado."}
    return {"artifact_id": artifact_id, "text": text}


# ── Gmail ───────────────────────────────────────────────────────────────────

@app.get("/api/gmail/status")
async def gmail_status():
    from core.docs.gmail import is_available, _CREDS_PATH, _TOKEN_PATH
    available = is_available()
    has_token = _TOKEN_PATH.exists()
    libs_ok = True
    try:
        import googleapiclient  # noqa: F401
        import google_auth_oauthlib  # noqa: F401
    except ImportError:
        libs_ok = False
    return {
        "available":    available,
        "has_token":    has_token,
        "libs_ok":      libs_ok,
        "creds_path":   str(_CREDS_PATH),
        "setup_needed": not available or not libs_ok,
        "hint": (
            "Sube gmail_credentials.json en Configuración → Gmail"
            if not available else
            "pip install google-api-python-client google-auth-oauthlib"
            if not libs_ok else
            "Listo — primer escaneo abrirá el navegador para autorizar"
            if not has_token else
            "Credenciales y token OK"
        ),
    }


@app.get("/api/gmail/recent")
async def gmail_recent(max_results: int = Query(default=20)):
    from core.docs.gmail import list_recent
    return list_recent(max_results=max_results)


@app.post("/api/gmail/scan")
async def gmail_scan(body: Dict):
    """
    Scan Gmail for financial emails.
    Body: { "year": 2024 }  or  { "date_from": "2024-01-01", "date_to": "2024-12-31" }
    """
    from datetime import date as date_cls

    # Pre-flight checks
    try:
        import googleapiclient  # noqa: F401
        import google_auth_oauthlib  # noqa: F401
    except ImportError:
        return {
            "error": "Librerías de Google no instaladas.",
            "fix":   "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib",
            "available": False,
        }

    from core.docs.gmail import is_available, scan_financial
    if not is_available():
        return {
            "error": "Credenciales de Gmail no configuradas.",
            "fix":   "Ve a Configuración → Gmail y sube tu credentials.json.",
            "available": False,
        }

    year = body.get("year")
    if year:
        date_from = date_cls(int(year), 1, 1)
        date_to   = date_cls(int(year), 12, 31)
    else:
        try:
            date_from = date_cls.fromisoformat(body.get("date_from", ""))
            date_to   = date_cls.fromisoformat(body.get("date_to", ""))
        except ValueError:
            return {"error": "Indica 'year' o 'date_from'/'date_to' en YYYY-MM-DD."}

    update_existing = bool(body.get("update_existing", False))
    try:
        return scan_financial(date_from, date_to, update_existing=update_existing)
    except Exception as exc:
        return {"error": str(exc), "available": True}


@app.post("/api/settings/credentials/gmail")
async def save_gmail_credentials(creds_file: UploadFile = File(...)):
    """Upload gmail_credentials.json to PALACE/config/."""
    dest = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gmail_credentials.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await creds_file.read())
    token = dest.parent / "gmail_token.json"
    if token.exists():
        token.unlink()
    return {"ok": True}


@app.delete("/api/settings/credentials/gmail")
async def delete_gmail_credentials():
    base = Path(__file__).parent.parent.parent / "PALACE" / "config"
    removed = []
    for fname in ["gmail_credentials.json", "gmail_token.json"]:
        p = base / fname
        if p.exists():
            p.unlink()
            removed.append(fname)
    return {"ok": True, "removed": removed}


# ── KRONOS endpoints ───────────────────────────────────────────────────────

@app.get("/api/kronos/context")
async def kronos_context(mode: str = "brief"):
    """Return the financial context block KRONOS would inject into its prompt."""
    from core.kronos.financial_cache import summary_text
    ctx = summary_text(mode=mode)
    return {"ok": True, "context": ctx, "empty": not ctx}


@app.post("/api/kronos/rebuild")
async def kronos_rebuild():
    """Force a full rebuild of the financial cache from all artifacts."""
    import asyncio, functools
    try:
        from core.kronos.financial_cache import rebuild
        cache = await asyncio.get_event_loop().run_in_executor(None, rebuild)
        s = cache["summary"]
        return {
            "ok": True,
            "count": s["count"],
            "net": s["net"],
            "categories": list(s["by_category"].keys()),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/kronos/summary")
async def kronos_summary():
    """Return the cached financial summary (no LLM call)."""
    from core.kronos.financial_cache import rebuild_if_stale
    cache = rebuild_if_stale()
    return {"ok": True, "summary": cache.get("summary", {}), "built_at": cache.get("built_at")}


@app.post("/api/kronos/analyze")
async def kronos_analyze(body: Dict):
    """Full KRONOS analysis report. Body: { question: str }"""
    question = (body.get("question") or "").strip()
    if not question:
        return {"ok": False, "error": "question requerido"}
    try:
        import asyncio, functools
        from core.kronos.analyzer import full_analysis
        report = await asyncio.get_event_loop().run_in_executor(
            None, functools.partial(full_analysis, question)
        )
        return {"ok": True, "report": report}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/api/settings/llm/agents")
async def set_agent_llm(body: Dict):
    """
    Configure per-agent LLM provider.
    Body: { "agent_id": "kronos", "provider": "claude" }
    """
    agent_id = (body.get("agent_id") or "").strip()
    provider = (body.get("provider") or "").strip()
    if not agent_id or not provider:
        return {"ok": False, "error": "agent_id y provider requeridos"}
    from core.config.preferences import load, save
    prefs = load()
    prefs.setdefault("llm", {}).setdefault("agents", {})[agent_id] = provider
    save(prefs)
    return {"ok": True, "agent_id": agent_id, "provider": provider}


@app.get("/api/settings/llm/agents")
async def get_agent_llm():
    """Return current per-agent LLM overrides."""
    from core.config.preferences import load
    agents = load().get("llm", {}).get("agents", {})
    return {"ok": True, "agents": agents}


# ── Settings ───────────────────────────────────────────────────────────────

@app.get("/api/settings")
async def get_settings():
    """Return current settings status (no secrets in plain text)."""
    from core.config.preferences import status
    return status()


@app.patch("/api/settings/preferences")
async def update_preferences(body: Dict):
    """
    Update a preferences section.
    Body: { "section": "llm" | "voice" | "ui", "updates": { ... } }
    API keys in the 'llm' section are stored locally and never echoed back.
    """
    from core.config.preferences import update
    section = body.get("section", "")
    updates = body.get("updates", {})
    if not section:
        return {"error": "Campo 'section' requerido."}
    prefs = update(section, updates)
    # Return status without exposing the raw api_key value
    llm = prefs.get("llm", {})
    return {
        "ok": True,
        "llm": {
            "provider": llm.get("provider"),
            "model": llm.get("model"),
            "has_api_key": bool(llm.get("api_key")),
        },
        "voice": prefs.get("voice", {}),
        "ui": prefs.get("ui", {}),
        "system": prefs.get("system", {"use_v3_modes": False}),
    }


@app.get("/api/llm/ollama/models")
async def llm_ollama_models():
    """List models currently installed in the local Ollama instance."""
    import asyncio as _aio, functools as _ft
    try:
        import requests as _r
        resp = await _aio.get_event_loop().run_in_executor(
            None, _ft.partial(_r.get, "http://localhost:11434/api/tags", timeout=2)
        )
        if resp.status_code == 200:
            data = resp.json()
            names = [m["name"] for m in data.get("models", [])]
            return {"ok": True, "models": names}
    except Exception:
        pass
    return {"ok": False, "models": []}


@app.post("/api/llm/test")
async def llm_test(body: Dict = None):
    """
    Test connectivity for a provider.
    Body (optional): { "provider": "groq", "api_key": "sk-..." }
    Falls back to the currently configured provider if body is omitted.
    """
    import asyncio as _aio, functools as _ft
    from core.config.preferences import load as load_prefs
    body     = body or {}
    prefs    = load_prefs()
    provider = body.get("provider") or prefs.get("llm", {}).get("provider", "ollama")
    api_key  = body.get("api_key")  or prefs.get("llm", {}).get("api_key", "")

    if provider == "ollama":
        try:
            import requests as _r
            resp = await _aio.get_event_loop().run_in_executor(
                None, _ft.partial(_r.get, "http://localhost:11434/api/tags", timeout=2)
            )
            if resp.status_code == 200:
                names = [m["name"] for m in resp.json().get("models", [])]
                return {"ok": True, "provider": "ollama", "models": names, "error": None}
            return {"ok": False, "provider": "ollama", "models": [], "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"ok": False, "provider": "ollama", "models": [], "error": str(e)}

    if provider == "openrouter":
        if not api_key:
            return {"ok": False, "provider": "openrouter", "models": [], "error": "API key no configurada"}
        try:
            from core.llm.providers.openrouter_provider import OpenRouterProvider
            free_models = OpenRouterProvider().list_free_models()
            return {"ok": True, "provider": "openrouter", "models": free_models,
                    "note": "Clave presente — acceso a modelos gratuitos confirmado", "error": None}
        except Exception as e:
            return {"ok": False, "provider": "openrouter", "models": [], "error": str(e)}

    if not api_key:
        return {"ok": False, "provider": provider, "models": [], "error": "API key no configurada"}
    return {"ok": True, "provider": provider, "models": [], "note": "Clave presente — se validará en el primer chat", "error": None}


@app.post("/api/llm/refresh_catalog")
async def llm_refresh_catalog():
    """Refresh provider availability/metrics snapshot for ranking policies."""
    from core.llm.provider_ranker import refresh_catalog
    return refresh_catalog()


@app.get("/api/llm/ranking")
async def llm_ranking(policy: str = Query(default="fastest")):
    """Return provider ranking by policy: fastest | most_reliable."""
    from core.llm.provider_ranker import rank
    return rank(policy=policy)


@app.get("/api/llm/discover")
async def llm_discover():
    """
    Auto-detect which LLM providers are currently available (configured + reachable).
    Returns a ranked list with status and recommended use per provider.
    """
    import asyncio as _aio, functools as _ft, os
    from core.config.preferences import load as load_prefs
    prefs    = load_prefs()
    stored   = prefs.get("llm", {}).get("provider", "ollama")
    api_key  = prefs.get("llm", {}).get("api_key", "")

    results = []

    # ── Ollama (local) ──────────────────────────────────────────────────────
    ollama_ok = False
    ollama_models: list = []
    try:
        import requests as _r
        r = await _aio.get_event_loop().run_in_executor(
            None, _ft.partial(_r.get, "http://localhost:11434/api/tags", timeout=2)
        )
        if r.status_code == 200:
            ollama_ok = True
            ollama_models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    results.append({
        "provider": "ollama", "label": "Ollama (local)", "ok": ollama_ok,
        "models": ollama_models, "free": True, "needs_key": False,
        "use_for": "privacidad, tareas locales, voz",
        "active": stored == "ollama",
    })

    # ── Cloud providers (check if key configured) ───────────────────────────
    _cloud = [
        ("groq",       "Groq",                     "GROQ_API_KEY",       True,  "chat rápido, tareas frecuentes"),
        ("openrouter", "OpenRouter (20+ modelos)",  "OPENROUTER_API_KEY", True,  "variedad, modelos gratuitos potentes"),
        ("deepseek",   "DeepSeek",                  "DEEPSEEK_API_KEY",   True,  "análisis, razonamiento"),
        ("mistral",    "Mistral AI",                "MISTRAL_API_KEY",    True,  "escritura, síntesis"),
        ("claude",     "Claude (Anthropic)",         "ANTHROPIC_API_KEY",  False, "tareas complejas, premium"),
        ("openai",     "OpenAI / GPT",              "OPENAI_API_KEY",     False, "tareas complejas, premium"),
    ]
    for pname, label, env_var, is_free, use_for in _cloud:
        key_present = bool((stored == pname and api_key) or os.getenv(env_var, ""))
        extra_models: list = []
        if pname == "openrouter" and key_present:
            from core.llm.providers.openrouter_provider import OpenRouterProvider
            extra_models = OpenRouterProvider().list_free_models()
        results.append({
            "provider": pname, "label": label, "ok": key_present,
            "models": extra_models, "free": is_free, "needs_key": True,
            "use_for": use_for, "active": stored == pname,
        })

    configured = sum(1 for r in results if r["ok"])
    return {"providers": results, "configured": configured, "total": len(results)}


@app.post("/api/settings/credentials/gdrive")
async def save_gdrive_credentials(creds_file: UploadFile = File(...)):
    """Upload gdrive_credentials.json to PALACE/config/."""
    from pathlib import Path
    dest = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gdrive_credentials.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await creds_file.read())
    return {"ok": True, "path": str(dest)}


@app.post("/api/settings/credentials/onedrive")
async def save_onedrive_config(body: Dict):
    """
    Save OneDrive app registration config.
    Body: { "client_id": "...", "client_secret": "...", "tenant_id": "consumers" }
    """
    import json
    from pathlib import Path
    required = {"client_id", "client_secret"}
    if not required.issubset(body.keys()):
        return {"error": f"Campos requeridos: {required}"}
    dest = Path(__file__).parent.parent.parent / "PALACE" / "config" / "onedrive_config.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return {"ok": True}


@app.delete("/api/settings/credentials/{service}")
async def delete_credentials(service: str):
    """Remove stored credentials for 'gdrive' or 'onedrive'."""
    from pathlib import Path
    files = {
        "gdrive":    ["gdrive_credentials.json", "gdrive_token.json"],
        "onedrive":  ["onedrive_config.json", "onedrive_token.json"],
    }
    if service not in files:
        return {"error": f"Servicio desconocido: {service}"}
    base = Path(__file__).parent.parent.parent / "PALACE" / "config"
    removed = []
    for fname in files[service]:
        p = base / fname
        if p.exists():
            p.unlink()
            removed.append(fname)
    return {"ok": True, "removed": removed}


# ── Telegram settings ────────────────────────────────────────────────────

_TG_CONFIG = Path(__file__).parent.parent.parent / "PALACE" / "config" / "telegram.json"

@app.get("/api/settings/telegram/status")
async def telegram_status():
    """Return Telegram bot configuration status."""
    if not _TG_CONFIG.exists():
        return {"configured": False, "has_token": False, "allowed_user_ids": [], "admin_user_id": None}
    try:
        import json as _json
        cfg = _json.loads(_TG_CONFIG.read_text(encoding="utf-8"))
        token = cfg.get("token", "")
        return {
            "configured":      bool(token and token != "YOUR_TOKEN_HERE"),
            "has_token":       bool(token),
            "allowed_user_ids": cfg.get("allowed_user_ids", []),
            "admin_user_id":   cfg.get("admin_user_id"),
        }
    except Exception as exc:
        return {"configured": False, "error": str(exc)}


@app.post("/api/settings/telegram")
async def save_telegram_config(body: Dict):
    """
    Save Telegram bot configuration.
    Body: { "token": "...", "allowed_user_ids": [123, 456], "admin_user_id": 123 }
    """
    import json as _json
    token = (body.get("token") or "").strip()
    if not token:
        return {"ok": False, "error": "El token no puede estar vacío."}
    cfg = {
        "token":            token,
        "allowed_user_ids": [int(x) for x in body.get("allowed_user_ids", []) if str(x).strip().isdigit()],
        "admin_user_id":    int(body["admin_user_id"]) if body.get("admin_user_id") and str(body["admin_user_id"]).strip().isdigit() else None,
    }
    _TG_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    _TG_CONFIG.write_text(_json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "configured": True}


@app.delete("/api/settings/telegram")
async def delete_telegram_config():
    """Remove Telegram bot configuration."""
    if _TG_CONFIG.exists():
        _TG_CONFIG.unlink()
    return {"ok": True}


# ── System status (for StatusBar) ─────────────────────────────────────────

@app.get("/api/status")
async def system_status():
    """Quick status snapshot for the navbar StatusBar."""
    import os
    from core.config.preferences import load as load_prefs
    from core.docs.artifact_store import stats as art_stats, financial_summary

    prefs    = load_prefs()
    provider = prefs.get("llm", {}).get("provider", "ollama")

    # Ollama alive check — run in executor so we never block the event loop
    ollama_ok = False
    try:
        import asyncio as _aio, functools as _ft, requests as _r
        _resp = await _aio.get_event_loop().run_in_executor(
            None, _ft.partial(_r.get, "http://localhost:11434", timeout=1)
        )
        ollama_ok = _resp.status_code == 200
    except Exception:
        pass

    # Artifact counts
    try:
        stats = art_stats()
        total_docs = stats.get("total_artifacts", 0)
    except Exception:
        total_docs = 0

    # Financial total (current year)
    fin_total = 0.0
    try:
        from datetime import date
        year = date.today().year
        fs = financial_summary(year=year)
        fin_total = fs.get("total", 0.0)
    except Exception:
        pass

    # Memory nodes count
    mem_count = 0
    try:
        from memory.storage import MEMORY_DB_PATH
        import sqlite3 as _sq
        with _sq.connect(MEMORY_DB_PATH, timeout=1) as _c:
            mem_count = _c.execute("SELECT COUNT(*) FROM memory_nodes").fetchone()[0]
    except Exception:
        pass

    # ── Cognitive layer metrics ───────────────────────────────────────────────
    fatigue         = None
    traces_today    = 0
    shadow_enabled  = False
    qualified_modes = 0
    degraded_modes  = 0

    try:
        from core.session_state import _global_state
        fatigue = round(_global_state.fatigue, 3)
    except Exception:
        pass

    try:
        import sqlite3 as _sq
        from memory.storage import MEMORY_DB_PATH
        from datetime import date
        today = date.today().isoformat()
        with _sq.connect(MEMORY_DB_PATH, timeout=2) as _conn:
            traces_today = _conn.execute(
                "SELECT COUNT(*) FROM cognitive_traces WHERE timestamp LIKE ?",
                (f"{today}%",),
            ).fetchone()[0]
            degraded_modes = _conn.execute(
                "SELECT COUNT(*) FROM strategy_degradation WHERE penalty_score >= 0.7"
            ).fetchone()[0]
    except Exception:
        pass

    try:
        from core.tracing.shadow import is_shadow_enabled
        shadow_enabled = is_shadow_enabled()
    except Exception:
        pass

    try:
        from core.cognition.trace_learner import trace_learner
        modes, _ = trace_learner.compute_insights()
        qualified_modes = sum(1 for m in modes if m.qualifies())
    except Exception:
        pass

    return {
        "provider":        provider,
        "ollama_ok":       ollama_ok,
        "docs":            total_docs,
        "memory":          mem_count,
        "fin_total":       round(fin_total, 2),
        # Cognitive 3.0 fields
        "fatigue":         fatigue,
        "traces_today":    traces_today,
        "shadow_enabled":  shadow_enabled,
        "qualified_modes": qualified_modes,
        "degraded_modes":  degraded_modes,
    }


# ── Chat ───────────────────────────────────────────────────────────────────

def _extract_reply(result) -> str:
    """Extract the main text response from a ModeResult output dict."""
    output = result.output or {}
    for key in ("analysis", "plan", "ideas", "reflection", "synthesis", "model", "response", "text"):
        val = output.get(key)
        if isinstance(val, str) and val.strip():
            return val
    if output.get("blocked"):
        return f"[GUARDIAN] {output.get('reason', 'Solicitud bloqueada por seguridad.')}"
    if output.get("deferred"):
        return f"[EXECUTIVE] {output.get('reason', 'Acción diferida por fatiga cognitiva.')}"
    # stats dict from MemoryCurator or unknown mode — summarise it
    non_empty = {k: v for k, v in output.items() if v}
    if non_empty:
        return "Proceso completado: " + ", ".join(f"{k}={v}" for k, v in list(non_empty.items())[:4])
    return "Procesado."


@app.post("/api/chat")
async def chat_endpoint(body: Dict):
    """
    Multi-turn chat endpoint.

    Body: {
      "message": "...",
      "session_id": "uuid",
      "domain": "finanzas"   (optional, default "general")
    }

    Returns: {
      "reply": "...",
      "session_id": "...",
      "action": "gmail_scan|drive_search|...|null",
      "action_data": {...}|null,
      "history_len": N
    }
    """
    message    = (body.get("message") or "").strip()
    session_id = body.get("session_id") or "chat-default"
    domain     = body.get("domain") or "general"

    if not message:
        return {"error": "Campo 'message' vacío."}

    # Traceability setup — best-effort, never blocks the response
    try:
        from core.tracing.trace import TraceBuilder
        from core.tracing.context import set_trace
        from core.tracing.store import trace_store as _trace_store
        _tb = TraceBuilder(session_id=session_id, domain=domain, question=message, source="v1_pipeline")
        set_trace(_tb)
    except Exception:
        _tb = None
        _trace_store = None

    def _commit_trace(reply: str, confidence: float = 0.7, agent: str = "aletheia") -> None:
        try:
            if _tb and _trace_store:
                from core.tracing.context import set_trace
                trace = _tb.finish(output=reply, confidence=confidence)
                _trace_store.save(trace)
                set_trace(None)
                from core.tracing.shadow import schedule_shadow
                schedule_shadow(session_id, domain, message, reply)
        except Exception:
            pass

    from core.chat.session import get_or_create
    session = get_or_create(session_id, domain)
    session.add("user", message)

    # 1. Check for action requests first
    action = _detect_action(message)
    if action:
        action_result = _execute_action_api(action, message, domain)
        reply = action_result.get("llm_insight", "Acción ejecutada.")
        session.add("assistant", reply, action=action)
        _commit_trace(reply, confidence=0.85, agent="executive")
        return {
            "reply":        reply,
            "session_id":   session_id,
            "action":       action,
            "action_data":  action_result,
            "history_len":  len(session.history),
        }

    # 2. Aletheia 3.0 cognitive routing — full ModeRegistry pipeline
    _use_v3 = body.get("use_v3_modes")
    if _use_v3 is None:
        try:
            from core.config.preferences import load as _load_prefs
            _use_v3 = _load_prefs().get("system", {}).get("use_v3_modes", False)
        except Exception:
            _use_v3 = False
    if _use_v3:
        try:
            import asyncio, functools
            from core.modes.registry import mode_registry
            from core.session_state import get_state

            if _tb is not None:
                _tb.source = "v3_modes"

            cog_context = {
                "question":   message,
                "domain":     domain,
                "session_id": session_id,
                "history":    session.to_list() if hasattr(session, "to_list") else [],
            }
            state = get_state(session_id)

            mode_result = await asyncio.get_event_loop().run_in_executor(
                None,
                functools.partial(mode_registry.route_and_activate, cog_context, state),
            )

            reply = _extract_reply(mode_result)
            session.add("assistant", reply)
            _commit_trace(reply, confidence=mode_result.confidence, agent=mode_result.mode_id.value)
            try:
                from core.aco.v3.meta_cortex import meta_cortex as _mc
                _mc.learn(mode_result.mode_id.value, mode_result.confidence)
            except Exception:
                pass
            return {
                "reply":        reply,
                "session_id":   session_id,
                "action":       None,
                "action_data":  None,
                "agent":        mode_result.mode_id.value,
                "mode":         mode_result.mode_id.value,
                "confidence":   round(mode_result.confidence, 3),
                "history_len":  len(session.history),
            }
        except Exception as _v3_err:
            # v3 path failed — fall through to v1 pipeline
            try:
                from core.event_bus import emit_event, build_event
                emit_event(build_event(session_id, "v3_router", "routing", "v3_fallback", {"error": str(_v3_err)}))
            except Exception:
                pass

    # 3. KRONOS routing — financial/vital analysis questions
    from core.kronos.detector import is_kronos_query
    if is_kronos_query(message):
        from core.kronos.analyzer import quick_analysis as kronos_quick
        try:
            import asyncio, functools
            reply = await asyncio.get_event_loop().run_in_executor(
                None, functools.partial(kronos_quick, message)
            ) or "Necesito más contexto para analizar esto."
        except Exception:
            reply = "KRONOS no pudo conectar con el modelo ahora mismo."
        session.add("assistant", reply, action="kronos")
        _commit_trace(reply, confidence=0.8, agent="kronos")
        return {
            "reply":       reply,
            "session_id":  session_id,
            "action":      None,
            "action_data": None,
            "agent":       "kronos",
            "history_len": len(session.history),
        }

    # 3. RAG context — semantic search over indexed documents
    rag_context = ""
    try:
        from core.docs.rag import search as _rag_search
        hits = _rag_search(message, n_results=4, domain=domain if domain != "general" else None)
        relevant = [h for h in hits if h["score"] > 0.40]
        if relevant:
            snippets = "\n\n".join(
                f"[{h['metadata'].get('filename') or h['metadata'].get('source', '?')}]\n{h['text']}"
                for h in relevant
            )
            rag_context = f"\n\nContexto relevante de tus documentos:\n{snippets}"
    except Exception:
        pass

    # 4. Build context-aware prompt
    history_ctx = session.context_prompt()
    from core.llm import router as llm_router

    if history_ctx:
        prompt = (
            f"Eres Aletheia, una IA cognitiva y acompañante. "
            f"Dominio actual: {domain}.{rag_context}\n\n"
            f"Conversación hasta ahora:\n{history_ctx}\n\n"
            f"Responde al último mensaje de forma natural, breve y útil. "
            f"Si necesitas hacer un análisis de decisión profundo, indícalo."
        )
    else:
        prompt = (
            f"Eres Aletheia, una IA cognitiva. Dominio: {domain}.{rag_context}\n\n"
            f"Responde de forma natural y útil a: '{message}'"
        )

    try:
        import asyncio, functools
        reply = await asyncio.get_event_loop().run_in_executor(
            None,
            functools.partial(
                llm_router.generate,
                task="chat",
                prompt=prompt,
                context={"domain": domain},
                temp=0.7,
            ),
        ) or "Estoy aquí. ¿En qué te ayudo?"
    except Exception:
        reply = "No pude conectar con el modelo de lenguaje ahora mismo."

    session.add("assistant", reply)
    _commit_trace(reply, confidence=0.7, agent="aletheia")
    return {
        "reply":       reply,
        "session_id":  session_id,
        "action":      None,
        "action_data": None,
        "agent":       "aletheia",
        "history_len": len(session.history),
    }


@app.get("/api/chat/{session_id}/history")
async def chat_history(session_id: str):
    from core.chat.session import get
    session = get(session_id)
    if not session:
        return {"session_id": session_id, "history": []}
    return {"session_id": session_id, "history": session.to_list()}


@app.delete("/api/chat/{session_id}")
async def clear_chat(session_id: str):
    from core.chat.session import clear
    clear(session_id)
    return {"ok": True}


# ── Cognitive Traceability Layer ────────────────────────────────────────────

@app.get("/api/traces")
async def get_traces(
    limit: int = Query(default=50, le=200),
    session_id: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    mode: Optional[str] = Query(default=None),
):
    """
    Recent cognitive traces.

    Query params (all optional):
      limit      — max results (default 50, max 200)
      session_id — filter by session
      source     — "v1_pipeline" | "shadow_3.0" | "voice"
      mode       — e.g. "KRONOS", "ANALYTICAL", "OBSERVER"
    """
    from core.tracing.store import trace_store
    return {
        "traces": trace_store.recent(
            limit=limit,
            session_id=session_id,
            source=source,
            mode=mode,
        )
    }


@app.get("/api/traces/summary")
async def traces_summary(session_id: Optional[str] = Query(default=None)):
    """Aggregate stats: mode counts, avg latency, avg fatigue, top providers."""
    from core.tracing.store import trace_store
    return trace_store.summary(session_id=session_id)


@app.get("/api/traces/divergences")
async def traces_divergences(limit: int = Query(default=20, le=100)):
    """Raw shadow vs v1 output divergences (output_preview diff only)."""
    from core.tracing.store import trace_store
    return {"divergences": trace_store.divergences(limit=limit)}


@app.get("/api/traces/divergences/analyzed")
async def traces_divergences_analyzed(
    limit: int  = Query(default=50, le=200),
    winner: Optional[str] = Query(default=None),   # "shadow_3.0" | "v1_pipeline" | "tie"
    mode:   Optional[str] = Query(default=None),
):
    """
    Multidimensional divergence reports (DivergenceAnalyzer).

    Each report scores 6 dimensions and determines overall_winner:
      reasoning_depth, cost_efficiency, coherence,
      context_alignment, fatigue_impact, memory_retrieval

    Triggers a fresh analysis pass if no reports exist yet.
    """
    from core.tracing.store import trace_store
    return {
        "reports": trace_store.analyzed_divergences(limit=limit, winner=winner, mode=mode)
    }


@app.get("/api/traces/divergences/stats")
async def traces_divergences_stats():
    """Aggregate win rates, avg scores per dimension, top winning modes."""
    from core.tracing.store import trace_store
    return trace_store.divergence_stats()


@app.post("/api/traces/analyze")
async def run_divergence_analysis(limit: int = Query(default=50, le=200)):
    """
    Trigger a fresh divergence analysis pass over the N most recent trace pairs.
    Returns the number of reports generated.
    """
    import asyncio, functools
    from core.tracing.divergence import divergence_analyzer
    reports = await asyncio.get_event_loop().run_in_executor(
        None, functools.partial(divergence_analyzer.analyze, limit=limit)
    )
    return {"analyzed": len(reports), "reports": [r.to_dict() for r in reports[:10]]}


@app.get("/api/traces/{trace_id}")
async def get_trace(trace_id: str):
    """Full detail for a single trace."""
    from core.tracing.store import trace_store
    trace = trace_store.get(trace_id)
    if not trace:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


# ── Cognitive Replay ─────────────────────────────────────────────────────────

@app.post("/api/traces/{trace_id}/replay")
async def replay_trace(trace_id: str, body: Dict):
    """
    Re-run a historical trace with different parameters.

    Body (all optional):
      target_mode      — ModeID or blend preset name ("KRONOS", "strategic_analytical", ...)
      target_provider  — "ollama" | "claude" | "openai" | ...
      state_override   — {"fatigue": 0.8, "energy": 0.5, ...}
      synthesis        — "weighted_prompt" | "sequential"  (for blends)
      compare_with_original — bool (default true)
      label            — human description of the scenario

    Returns: ReplayResult with new trace, improvement verdict, and divergence score.
    """
    import asyncio, functools
    from core.tracing.replay import cognitive_replayer, ReplayConfig

    config = ReplayConfig(
        target_mode           = body.get("target_mode"),
        target_provider       = body.get("target_provider"),
        state_override        = body.get("state_override"),
        synthesis             = body.get("synthesis", "weighted_prompt"),
        compare_with_original = body.get("compare_with_original", True),
        label                 = body.get("label", ""),
    )

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(cognitive_replayer.replay, trace_id, config),
    )
    return result.to_dict()


@app.post("/api/traces/{trace_id}/replay/batch")
async def batch_replay_trace(trace_id: str, body: Dict):
    """
    Run multiple replay scenarios against the same trace and compare them.

    Body:
      configs — list of ReplayConfig dicts (same fields as single replay)

    Returns: ranked list of ReplayResults (best improvement first).
    Useful for answering "which mode/provider would have worked best?"
    """
    import asyncio, functools
    from core.tracing.replay import cognitive_replayer, ReplayConfig
    from fastapi import HTTPException

    raw_configs = body.get("configs", [])
    if not raw_configs:
        raise HTTPException(status_code=400, detail="Field 'configs' is required and must be non-empty.")

    configs = [
        ReplayConfig(
            target_mode           = c.get("target_mode"),
            target_provider       = c.get("target_provider"),
            state_override        = c.get("state_override"),
            synthesis             = c.get("synthesis", "weighted_prompt"),
            compare_with_original = c.get("compare_with_original", True),
            label                 = c.get("label", ""),
        )
        for c in raw_configs
    ]

    results = await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(cognitive_replayer.batch_replay, trace_id, configs),
    )
    return {
        "original_trace_id": trace_id,
        "total_replays":     len(results),
        "results":           [r.to_dict() for r in results],
    }


@app.get("/api/traces/{trace_id}/replays")
async def get_trace_replays(trace_id: str, limit: int = Query(default=20, le=100)):
    """All replay history for a specific original trace."""
    from core.tracing.replay import replay_store
    return {
        "original_trace_id": trace_id,
        "replays": replay_store.history(limit=limit, original_trace_id=trace_id),
    }


@app.get("/api/replay/history")
async def replay_history(
    limit:      int = Query(default=50, le=200),
    improvement: Optional[str] = Query(default=None),  # "better"|"worse"|"tie"
):
    """Recent replay results across all traces, optionally filtered by outcome."""
    from core.tracing.replay import replay_store
    return {
        "replays": replay_store.history(limit=limit, improvement=improvement)
    }


@app.get("/api/replay/stats")
async def replay_stats():
    """Aggregate replay outcomes: how often replays improve on the original."""
    from core.tracing.replay import replay_store
    return replay_store.stats()


# ── Adaptive Learning Loop ─────────────────────────────────────────────────

@app.get("/api/learning/insights")
async def learning_insights(domain: Optional[str] = Query(default=None)):
    """
    Current ranked insights per (domain, mode/blend) and per provider.
    Includes rank_score, degradation flag, and shadow win_rate.
    Forces a cache refresh if data is stale (> 5 min).
    """
    from core.cognition.trace_learner import trace_learner
    from core.aco.v3.meta_cortex import meta_cortex
    if domain:
        modes = trace_learner.insights_for(domain)
        return {
            "domain":        domain,
            "modes":         [i.to_dict() for i in modes],
            "metacortex":    meta_cortex.stats(),
        }
    result = trace_learner.all_insights()
    result["metacortex"] = {
        "stats":              meta_cortex.stats(),
        "top_modes":          meta_cortex.top_modes(5),
        "total_interactions": meta_cortex.total_interactions(),
    }
    return result


@app.get("/api/learning/degradation")
async def learning_degradation():
    """
    All degraded strategies and full penalty table.
    Use this to understand what the system has learned to avoid.
    """
    from core.cognition.degradation import strategy_degradation
    return {
        "degraded": strategy_degradation.all_degraded(),
        "all":      strategy_degradation.all_entries(),
    }


@app.post("/api/learning/recompute")
async def learning_recompute():
    """
    Force a full recomputation of TraceLearner insights (bypasses 5-min TTL).
    Returns summary of modes and providers analyzed.
    """
    import asyncio, functools
    from core.cognition.trace_learner import trace_learner
    modes, providers = await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(trace_learner.compute_insights, force=True),
    )
    return {
        "modes_analyzed":     len(modes),
        "providers_analyzed": len(providers),
        "qualified_modes":    sum(1 for m in modes if m.qualifies()),
        "degraded_modes":     sum(1 for m in modes if m.degraded),
        "top_modes":          [m.to_dict() for m in sorted(modes, key=lambda x: -x.rank_score)[:5]],
        "top_providers":      [p.to_dict() for p in sorted(providers, key=lambda x: -x.efficiency_score)[:3]],
    }


@app.post("/api/learning/degradation/reset")
async def learning_degradation_reset(body: Dict):
    """
    Reset degradation penalties.
    Body: {"domain": "...", "mode_or_blend": "..."}  — both optional (omit to reset all).
    """
    from core.cognition.degradation import strategy_degradation
    n = strategy_degradation.reset(
        domain=body.get("domain"),
        mode_or_blend=body.get("mode_or_blend"),
    )
    from core.cognition.trace_learner import trace_learner
    trace_learner.invalidate()
    return {"reset_count": n}


@app.get("/api/learning/recommend")
async def learning_recommend(
    domain:     str = Query(...),
    session_id: str = Query(default="local"),
):
    """
    Current TraceLearner recommendations for a domain + session.
    Useful for debugging routing decisions before they happen.
    """
    from core.cognition.trace_learner import trace_learner
    from core.session_state import get_state
    state = get_state(session_id)
    return {
        "domain":             domain,
        "session_id":         session_id,
        "recommended_mode":   trace_learner.recommend_mode(domain, state),
        "recommended_blend":  trace_learner.recommend_blend(domain, state),
        "recommended_provider": trace_learner.recommend_provider("chat", state),
        "cognitive_state":    state.snapshot(),
    }


# ── Cognitive modes introspection ───────────────────────────────────────────

@app.get("/api/modes/status")
async def modes_status():
    """Registry status: active modes, blend presets, available by current state."""
    from core.modes.registry import mode_registry
    from core.session_state import active_sessions
    return {
        "registry":        mode_registry.status(),
        "active_sessions": active_sessions(),
    }


@app.get("/api/modes/blends")
async def modes_blends():
    """Available blend presets with weights."""
    from core.modes.blend import BLEND_PRESETS
    return {
        name: {k.value: round(v, 3) for k, v in weights.items()}
        for name, weights in BLEND_PRESETS.items()
    }


@app.post("/api/modes/blend/test")
async def test_blend(body: Dict):
    """
    Test a blend against a question without affecting the main session.
    Body: {"question": "...", "domain": "...", "preset": "strategic_analytical"}
    Returns: ModeResult dict.
    """
    question = (body.get("question") or "").strip()
    domain   = body.get("domain") or "general"
    preset   = body.get("preset") or "strategic_analytical"

    if not question:
        return {"error": "Campo 'question' vacío."}

    import asyncio, functools
    from core.modes.blend import ModeBlend
    from core.modes.registry import mode_registry
    from core.cognitive_state import CognitiveState

    try:
        blend = ModeBlend.from_preset(preset)
    except ValueError as e:
        return {"error": str(e)}

    state   = CognitiveState()
    context = {"domain": domain, "question": question, "session_id": "blend-test"}

    result = await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(mode_registry.blend_and_activate, blend, context, state),
    )
    return {
        "preset":    preset,
        "result":    result.to_dict(),
        "state_after": state.snapshot(),
    }


# ── Web search ─────────────────────────────────────────────────────────────

@app.get("/api/search")
async def web_search(q: str = Query(...), max_results: int = Query(default=8)):
    """DuckDuckGo web search."""
    from core.docs.web_search import search
    return {"query": q, "results": search(q, max_results=max_results)}


@app.get("/api/search/news")
async def web_news(q: str = Query(...), max_results: int = Query(default=6)):
    from core.docs.web_search import news
    return {"query": q, "results": news(q, max_results=max_results)}


# ── URL ingestion ───────────────────────────────────────────────────────────

@app.post("/api/docs/ingest_url")
async def ingest_url(body: Dict):
    """
    Fetch a URL, extract text, store as artifact, optionally run through pipeline.
    Body: {"url": "...", "domain": "...", "question": "..." (optional)}
    """
    url    = (body.get("url") or "").strip()
    domain = body.get("domain") or "general"
    question = body.get("question") or ""

    if not url:
        return {"error": "Campo 'url' requerido."}

    from core.docs.url_ingester import ingest_url as do_ingest
    result = do_ingest(url, domain=domain)

    if not result.get("ok"):
        return result

    # Optionally analyse via pipeline
    if question or True:   # always run a quick analysis
        from core.orchestrator import process_request
        from core.contracts.contract_lock import validate_final_report
        prompt = question or f"Analiza el contenido de esta página web: {result['title']}"
        full_prompt = f"{prompt}\n\n[Página: {url}]\n{result.get('excerpt', '')}"
        pipeline = validate_final_report(process_request(domain, full_prompt))
        result["analysis"] = pipeline.get("llm_insight", "")

    return result


# ── Bank statement parser ───────────────────────────────────────────────────

@app.post("/api/docs/bank_statement")
async def parse_bank_statement(file: UploadFile = File(...), domain: str = Form(default="finanzas")):
    """
    Upload a bank statement (CSV, XLSX, OFX/QFX), parse and store transactions.
    """
    suffix = Path(file.filename or "stmt").suffix or ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        from core.docs.bank_parser import ingest_statement
        return ingest_statement(tmp_path, domain=domain)
    finally:
        os.unlink(tmp_path)


@app.get("/api/docs/bank_summary")
async def bank_summary(year: int = Query(default=0)):
    """Aggregate bank statement transactions from artifact store."""
    from core.docs.artifact_store import query
    stmts = query(artifact_type="bank_statement", domain="finanzas",
                  date_from=f"{year}-01-01" if year else None,
                  date_to=f"{year}-12-31" if year else None)
    from core.docs.artifact_store import get_text
    all_txns: list[dict] = []
    for s in stmts:
        text = get_text(s["id"]) or ""
        # Re-parse inline text to get structured transactions
        lines = [l for l in text.splitlines() if re.match(r"\d{4}-\d{2}-\d{2}", l)]
        for l in lines:
            parts = l.split()
            if len(parts) >= 3:
                try:
                    amount = float(parts[-2].replace(",", "."))
                    cat    = parts[-1].strip("[]")
                    all_txns.append({"date": parts[0], "amount": amount, "category": cat})
                except ValueError:
                    pass
    income   = sum(t["amount"] for t in all_txns if t["amount"] > 0)
    expenses = sum(t["amount"] for t in all_txns if t["amount"] < 0)
    by_cat: dict[str, float] = {}
    for t in all_txns:
        by_cat[t["category"]] = round(by_cat.get(t["category"], 0) + abs(t["amount"]), 2)
    return {
        "year":           year or "todos",
        "count":          len(all_txns),
        "total_income":   round(income, 2),
        "total_expenses": round(expenses, 2),
        "net":            round(income + expenses, 2),
        "by_category":    dict(sorted(by_cat.items(), key=lambda x: x[1], reverse=True)),
    }


# ── Fiscal endpoints ──────────────────────────────────────────────────────

@app.post("/api/fiscal/irpf")
async def fiscal_irpf(body: Dict):
    """
    Body: { "renta_bruta": 40000, "autonomo": false, "cuotas_ss": 0,
            "otros_gastos": 0, "hijos": 0, "edad": 40 }
    """
    from core.docs.fiscal import calcular_irpf, format_irpf
    try:
        r = calcular_irpf(
            renta_bruta=float(body.get("renta_bruta") or 0),
            autonomo=bool(body.get("autonomo", False)),
            cuotas_ss=float(body.get("cuotas_ss") or 0),
            otros_gastos_deducibles=float(body.get("otros_gastos") or 0),
            hijos=int(body.get("hijos") or 0),
            edad=int(body.get("edad") or 40),
        )
        return {**r.to_dict(), "summary": format_irpf(r)}
    except Exception as exc:
        return {"error": str(exc)}


@app.post("/api/fiscal/iva")
async def fiscal_iva(body: Dict):
    """
    Body: { "base_21": 8000, "base_10": 0, "base_4": 0,
            "iva_soportado": 420, "trimestre": 1, "year": 2024 }
    """
    from core.docs.fiscal import calcular_iva, format_iva
    try:
        r = calcular_iva(
            base_imponible_21=float(body.get("base_21") or 0),
            base_imponible_10=float(body.get("base_10") or 0),
            base_imponible_4=float(body.get("base_4") or 0),
            iva_soportado=float(body.get("iva_soportado") or 0),
            trimestre=int(body.get("trimestre") or 1),
            year=int(body.get("year") or 2024),
        )
        return {**r.to_dict(), "summary": format_iva(r)}
    except Exception as exc:
        return {"error": str(exc)}


@app.post("/api/fiscal/modelo130")
async def fiscal_modelo130(body: Dict):
    """
    Body: { "ingresos": 20000, "gastos": 5000,
            "pagos_anteriores": 1500, "trimestre": 2, "year": 2024 }
    """
    from core.docs.fiscal import calcular_modelo_130, format_modelo130
    try:
        r = calcular_modelo_130(
            ingresos_acumulados=float(body.get("ingresos") or 0),
            gastos_acumulados=float(body.get("gastos") or 0),
            pagos_anteriores=float(body.get("pagos_anteriores") or 0),
            trimestre=int(body.get("trimestre") or 1),
            year=int(body.get("year") or 2024),
        )
        return {**r.to_dict(), "summary": format_modelo130(r)}
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/fiscal/resumen")
async def fiscal_resumen(year: int = Query(default=2024)):
    from core.docs.fiscal import resumen_fiscal
    try:
        return resumen_fiscal(year)
    except Exception as exc:
        return {"error": str(exc)}


# ── Calendar endpoints ────────────────────────────────────────────────────

@app.get("/api/calendar/today")
async def calendar_today():
    from core.docs.gcalendar import today_events, format_summary
    result = today_events()
    if result.get("available") and not result.get("error"):
        result["summary"] = format_summary(result.get("events", []))
    return result


@app.get("/api/calendar/events")
async def calendar_events(days_ahead: int = Query(default=7), days_back: int = Query(default=0)):
    from core.docs.gcalendar import list_events, format_summary
    result = list_events(days_back=days_back, days_ahead=days_ahead)
    if result.get("available") and not result.get("error"):
        result["summary"] = format_summary(result.get("events", []))
    return result


@app.post("/api/calendar/events")
async def calendar_create_event(body: Dict):
    """
    Create a calendar event.
    Body: { "title": "...", "start": "ISO datetime", "end": "ISO datetime",
            "description": "", "location": "" }
    """
    from core.docs.gcalendar import create_event
    title       = (body.get("title") or "").strip()
    start_iso   = (body.get("start") or "").strip()
    end_iso     = (body.get("end") or "").strip()
    description = body.get("description") or ""
    location    = body.get("location") or ""
    if not title or not start_iso or not end_iso:
        return {"error": "Campos requeridos: title, start, end"}
    return create_event(title, start_iso, end_iso, description=description, location=location)


@app.delete("/api/calendar/events/{event_id}")
async def calendar_delete_event(event_id: str):
    from core.docs.gcalendar import delete_event
    return delete_event(event_id)


@app.get("/api/calendar/search")
async def calendar_search(q: str = Query(default="")):
    from core.docs.gcalendar import search_events, format_summary
    if not q:
        return {"error": "Parámetro 'q' requerido"}
    result = search_events(q)
    if result.get("available") and not result.get("error"):
        result["summary"] = format_summary(result.get("events", []))
    return result


@app.get("/api/calendar/status")
async def calendar_status():
    """Return whether Calendar credentials and token are present."""
    from core.docs.gcalendar import is_available, _CREDS_PATH, _CREDS_ALT, _TOKEN_PATH, _SCOPES
    has_creds = _CREDS_PATH.exists() or _CREDS_ALT.exists()
    has_token = _TOKEN_PATH.exists()
    token_valid = False
    if has_token:
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), _SCOPES)
            token_valid = creds.valid or bool(creds.refresh_token)
        except Exception:
            pass
    using_drive_creds = not _CREDS_PATH.exists() and _CREDS_ALT.exists()
    return {
        "has_credentials": has_creds,
        "has_token":        has_token,
        "token_valid":      token_valid,
        "authorized":       has_creds and token_valid,
        "using_drive_creds": using_drive_creds,
    }


@app.post("/api/calendar/auth")
async def calendar_auth():
    """
    Trigger the Google Calendar OAuth browser flow.
    Opens the default browser on the server machine (desktop app pattern).
    Saves the resulting token to PALACE/config/gcalendar_token.json.
    """
    from core.docs.gcalendar import is_available, _creds_file, _TOKEN_PATH, _SCOPES
    if not is_available():
        return {"ok": False, "error": "No hay credenciales de Google configuradas. Sube gdrive_credentials.json o gcalendar_credentials.json primero."}
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(_creds_file()), _SCOPES)
        creds = flow.run_local_server(port=0)
        _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        return {"ok": True, "message": "Google Calendar autorizado correctamente."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Notification endpoints ────────────────────────────────────────────────

@app.post("/api/notifications/register")
async def notifications_register(body: Dict):
    """Register a user so they receive proactive notifications."""
    from core.notifications import register
    user_id = (body.get("user_id") or "default").strip()
    register(user_id)
    return {"registered": user_id}


@app.get("/api/notifications/poll")
async def notifications_poll(user_id: str = Query(default="default")):
    """Drain and return all pending notifications for a user."""
    from core.notifications import poll
    return poll(user_id)


@app.post("/api/notifications/push")
async def notifications_push(body: Dict):
    """Push a notification to a user (or all users if user_id is omitted)."""
    from core.notifications import push, push_all
    text    = (body.get("text") or "").strip()
    source  = body.get("source") or "system"
    user_id = body.get("user_id")
    if not text:
        return {"error": "Campo 'text' vacío."}
    if user_id:
        push(text, source, user_id)
    else:
        push_all(text, source)
    return {"queued": True}


# ── Consolidation (cognitive sleep) ──────────────────────────────────────

@app.get("/api/consolidation/status")
async def consolidation_status():
    """Return current state of the consolidation engine + queue stats."""
    from core.memory.consolidation_engine import consolidation_engine
    return consolidation_engine.status()


@app.post("/api/consolidation/run")
async def consolidation_run(body: Dict):
    """
    Trigger consolidation.
    Body: { "mode": "now" | "background" }
    """
    import asyncio, functools
    from core.memory.consolidation_engine import consolidation_engine
    mode = body.get("mode", "background")
    if mode == "now":
        result = await asyncio.get_event_loop().run_in_executor(
            None, consolidation_engine.run_now
        )
        return result
    else:
        started = consolidation_engine.start_background()
        return {"started": started, "message": "Consolidación iniciada en segundo plano." if started else "Ya hay una consolidación en curso."}


@app.post("/api/consolidation/stop")
async def consolidation_stop():
    """Stop a running background consolidation."""
    from core.memory.consolidation_engine import consolidation_engine
    consolidation_engine.stop()
    return {"stopped": True}


@app.post("/api/consolidation/schedule")
async def consolidation_schedule(body: Dict):
    """
    Set or clear the daily consolidation schedule.
    Body: { "hour": 2, "minute": 0, "enabled": true }
    """
    from core.memory.consolidation_engine import consolidation_engine
    hour    = int(body.get("hour", 2))
    minute  = int(body.get("minute", 0))
    enabled = bool(body.get("enabled", True))
    consolidation_engine.set_schedule(hour, minute, enabled)
    return {"scheduled": enabled, "hour": hour, "minute": minute}


# ── Setup / Onboarding status ─────────────────────────────────────────────

@app.get("/api/setup/status")
async def setup_status():
    """
    Aggregate health check for all integrable systems.
    Returns a list of system entries with status: 'ok' | 'partial' | 'missing'.
    """
    systems = []

    # 1. LLM — Ollama
    try:
        import httpx as _hx
        r = await asyncio.get_event_loop().run_in_executor(
            None, lambda: __import__("requests").get("http://localhost:11434/api/tags", timeout=2)
        )
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False
    systems.append({
        "id": "ollama", "name": "Ollama (LLM local)", "icon": "🤖",
        "status": "ok" if ollama_ok else "missing",
        "detail": "Corriendo en localhost:11434" if ollama_ok else "No detectado — ejecuta: ollama serve",
        "critical": True, "nav": "settings", "section": "llm",
    })

    # 2. LLM cloud provider
    try:
        from core.config.preferences import load as _lp
        prefs = _lp()
        provider = prefs.get("llm", {}).get("provider", "ollama")
        has_key  = bool(prefs.get("llm", {}).get("api_key", ""))
        cloud_ok = provider != "ollama" and has_key
    except Exception:
        cloud_ok = False
        provider = "ollama"
    systems.append({
        "id": "llm_cloud", "name": "Proveedor cloud (Claude/OpenAI…)", "icon": "☁️",
        "status": "ok" if cloud_ok else "missing",
        "detail": f"{provider} configurado" if cloud_ok else "Opcional — añade una API key para respuestas más potentes",
        "critical": False, "nav": "settings", "section": "llm",
    })

    # 3. Google Calendar
    try:
        from core.docs.gcalendar import is_available, _TOKEN_PATH, _SCOPES
        cal_creds = is_available()
        cal_token = _TOKEN_PATH.exists()
        cal_valid  = False
        if cal_token:
            try:
                from google.oauth2.credentials import Credentials
                c = Credentials.from_authorized_user_file(str(_TOKEN_PATH), _SCOPES)
                cal_valid = c.valid or bool(c.refresh_token)
            except Exception:
                pass
        cal_status = "ok" if (cal_creds and cal_valid) else ("partial" if cal_creds else "missing")
    except Exception:
        cal_status = "missing"
    systems.append({
        "id": "calendar", "name": "Google Calendar", "icon": "📅",
        "status": cal_status,
        "detail": {
            "ok":      "Conectado y autorizado",
            "partial": "Credenciales OK — falta autorizar (pulsa el botón en Config)",
            "missing": "Sin credenciales — configura Google Drive primero",
        }[cal_status],
        "critical": False, "nav": "settings", "section": "calendar",
    })

    # 4. Gmail
    try:
        from core.docs.gmail import is_available as gmail_avail
        gmail_ok = gmail_avail()
    except Exception:
        gmail_ok = False
    systems.append({
        "id": "gmail", "name": "Gmail (facturas)", "icon": "📧",
        "status": "ok" if gmail_ok else "missing",
        "detail": "Credenciales OAuth configuradas" if gmail_ok else "Sin credenciales",
        "critical": False, "nav": "settings", "section": "gmail",
    })

    # 5. Google Drive
    try:
        from core.docs.gdrive import is_available as gdrive_avail
        gdrive_ok = gdrive_avail()
    except Exception:
        gdrive_ok = False
    systems.append({
        "id": "gdrive", "name": "Google Drive", "icon": "💾",
        "status": "ok" if gdrive_ok else "missing",
        "detail": "Credenciales OAuth configuradas" if gdrive_ok else "Sin credenciales",
        "critical": False, "nav": "settings", "section": "gdrive",
    })

    # 6. Telegram
    tg_ok = _TG_CONFIG.exists()
    tg_token_ok = False
    if tg_ok:
        try:
            import json as _j
            _cfg = _j.loads(_TG_CONFIG.read_text(encoding="utf-8"))
            tg_token_ok = bool(_cfg.get("token")) and _cfg.get("token") != "YOUR_TOKEN_HERE"
        except Exception:
            pass
    systems.append({
        "id": "telegram", "name": "Bot de Telegram", "icon": "✈️",
        "status": "ok" if tg_token_ok else "missing",
        "detail": "Token configurado — arranca con --telegram" if tg_token_ok else "Sin token de BotFather",
        "critical": False, "nav": "settings", "section": "telegram",
    })

    # 7. RAG / Documentos
    try:
        from core.docs.artifact_store import ArtifactStore
        n_docs = len(ArtifactStore().list_all())
    except Exception:
        n_docs = 0
    try:
        import chromadb as _cdb
        _client = _cdb.PersistentClient(path="PALACE/rag")
        _col = _client.get_or_create_collection("aletheia_docs")
        n_chunks = _col.count()
    except Exception:
        n_chunks = 0
    rag_status = "ok" if n_chunks > 0 else ("partial" if n_docs > 0 else "missing")
    systems.append({
        "id": "rag", "name": "RAG / Documentos", "icon": "🔍",
        "status": rag_status,
        "detail": f"{n_docs} documentos · {n_chunks} chunks indexados" if n_chunks > 0
                  else (f"{n_docs} documentos sin indexar — ejecuta POST /api/rag/reindex" if n_docs > 0
                        else "Sin documentos — sube PDFs/DOCX en Config → Carpetas"),
        "critical": False, "nav": "docs", "section": None,
    })

    # 8. Voz offline
    _voice_base = Path(__file__).parent.parent.parent / "PALACE" / "voice_models"
    whisper_ok = (_voice_base / "whisper").exists() and any((_voice_base / "whisper").iterdir()) if (_voice_base / "whisper").exists() else False
    piper_ok   = (_voice_base / "piper").exists()   and any((_voice_base / "piper").iterdir())   if (_voice_base / "piper").exists()   else False
    voice_status = "ok" if (whisper_ok and piper_ok) else ("partial" if (whisper_ok or piper_ok) else "missing")
    systems.append({
        "id": "voice", "name": "Voz offline (STT + TTS)", "icon": "🎙️",
        "status": voice_status,
        "detail": "Whisper + Piper listos" if voice_status == "ok"
                  else ("Whisper OK, falta Piper (TTS)" if whisper_ok else
                        ("Piper OK, falta Whisper (STT)" if piper_ok else
                         "Modelos no descargados — arranca con: python start.py --voice")),
        "critical": False, "nav": "settings", "section": "voice",
    })

    connected  = sum(1 for s in systems if s["status"] == "ok")
    partial    = sum(1 for s in systems if s["status"] == "partial")
    total      = len(systems)

    return {
        "systems":   systems,
        "connected": connected,
        "partial":   partial,
        "missing":   total - connected - partial,
        "total":     total,
        "score":     round(connected / total, 2),
    }


# ── RAG endpoints ─────────────────────────────────────────────────────────

@app.post("/api/rag/search")
async def rag_search_endpoint(body: Dict):
    """
    Semantic search over indexed documents.
    Body: { "query": "...", "n": 5, "domain": "finanzas" }
    """
    query   = (body.get("query") or "").strip()
    n       = int(body.get("n") or 5)
    domain  = body.get("domain") or None
    if not query:
        return {"error": "Campo 'query' vacío."}
    from core.docs.rag import search as _rag_search, count as _rag_count
    results = _rag_search(query, n_results=n, domain=domain)
    return {"query": query, "results": results, "total_indexed": _rag_count()}


@app.post("/api/rag/reindex")
async def rag_reindex_endpoint():
    """Re-index all artifacts. Requires Ollama running with nomic-embed-text."""
    import asyncio
    from core.docs.rag import index_all
    stats = await asyncio.get_event_loop().run_in_executor(None, index_all)
    return stats


# ── Cognitive patterns ────────────────────────────────────────────────────

@app.get("/api/consolidation/patterns")
async def consolidation_patterns(
    limit: int = Query(default=20),
    unread_only: bool = Query(default=False),
):
    from core.cognition.pattern_detector import pattern_detector
    return pattern_detector.get_patterns(limit=limit, unread_only=unread_only)


@app.get("/api/consolidation/patterns/unread_count")
async def patterns_unread_count():
    from core.cognition.pattern_detector import pattern_detector
    return {"count": pattern_detector.unread_count()}


@app.post("/api/consolidation/patterns/{pattern_id}/mark_read")
async def pattern_mark_read(pattern_id: str):
    from core.cognition.pattern_detector import pattern_detector
    ok = pattern_detector.mark_read(pattern_id)
    return {"ok": ok}


@app.post("/api/consolidation/patterns/mark_all_read")
async def patterns_mark_all_read():
    from core.cognition.pattern_detector import pattern_detector
    n = pattern_detector.mark_all_read()
    return {"marked": n}


@app.post("/api/consolidation/patterns/detect")
async def patterns_detect_now(since_hours: int = Query(default=48)):
    """Trigger pattern detection manually (without full consolidation)."""
    import asyncio
    from core.cognition.pattern_detector import pattern_detector
    patterns = await asyncio.get_event_loop().run_in_executor(
        None, lambda: pattern_detector.detect(since_hours=since_hours)
    )
    return {"found": len(patterns), "patterns": [p.to_dict() for p in patterns]}


# ── Projects ───────────────────────────────────────────────────────────────

@app.get("/api/projects")
async def projects_list(
    status: str = Query(default=""),
    project_type: str = Query(default=""),
):
    from core.projects.manager import project_manager
    return project_manager.list(
        status=status or None,
        project_type=project_type or None,
    )


@app.post("/api/projects")
async def projects_create(body: Dict):
    from core.projects.manager import project_manager
    from core.projects.analyzer import compute_score, get_recommendation
    project = project_manager.create(body)
    score = compute_score(project)
    rec = get_recommendation(score, project)
    project = project_manager.update(project["id"], {"score_global": score, "recommendation": rec})
    return project


@app.get("/api/projects/reminders")
async def projects_reminders():
    from core.projects.manager import project_manager
    return project_manager.get_reminders()


@app.get("/api/projects/balance")
async def projects_balance():
    from core.projects.manager import project_manager
    return project_manager.get_portfolio_balance()


@app.get("/api/projects/types")
async def projects_types():
    from core.projects.manager import PROJECT_TYPES
    return [{"id": k, **v} for k, v in PROJECT_TYPES.items()]


@app.get("/api/projects/{project_id}")
async def projects_get(project_id: str):
    from core.projects.manager import project_manager
    p = project_manager.get(project_id)
    if not p:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return p


@app.put("/api/projects/{project_id}")
async def projects_update(project_id: str, body: Dict):
    from core.projects.manager import project_manager
    from core.projects.analyzer import compute_score, get_recommendation
    project = project_manager.update(project_id, body)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    score = compute_score(project)
    rec = get_recommendation(score, project)
    project = project_manager.update(project_id, {"score_global": score, "recommendation": rec})
    return project


@app.delete("/api/projects/{project_id}")
async def projects_discard(project_id: str):
    from core.projects.manager import project_manager
    ok = project_manager.discard(project_id)
    return {"ok": ok}


@app.post("/api/projects/{project_id}/analyze")
async def projects_analyze(project_id: str):
    """Trigger LLM narrative analysis for a project card."""
    from core.projects.manager import project_manager
    from core.projects.analyzer import analyze_with_llm, compute_score, get_recommendation

    project = project_manager.get(project_id)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    score = compute_score(project)
    rec = get_recommendation(score, project)

    from datetime import datetime, timezone
    llm_result = await analyze_with_llm(project)

    updates = {
        "score_global": score,
        "recommendation": llm_result.get("recommendation", rec),
        "analysis_summary": llm_result.get("analysis_summary", ""),
        "analysis_updated_at": datetime.now(timezone.utc).isoformat(),
    }
    updated = project_manager.update(project_id, updates)
    return updated


# ── Event streaming WebSocket ──────────────────────────────────────────────

@app.websocket("/stream/{session_id}")
async def event_stream(websocket: WebSocket, session_id: str):
    """Real-time cognitive event stream for the ThinkingPanel."""
    import asyncio
    from core.event_bus import get_event
    from starlette.websockets import WebSocketDisconnect
    await websocket.accept()
    try:
        while True:
            event = get_event(session_id)
            if event is not None:
                await websocket.send_json(event)
            else:
                await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[WS] /stream/{session_id}: {exc}")


def run(mode: str = "DEV", host: str = "127.0.0.1", port: int = 8000):
    """Run API server."""
    reload = (mode == "DEV")
    uvicorn.run("core.bootstrap.runtime:app", host=host, port=port, reload=reload, log_level="info")

if __name__ == "__main__":
    run()

