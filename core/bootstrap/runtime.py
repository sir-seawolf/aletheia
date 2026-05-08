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


def _execute_action_api(action: str, question: str) -> dict:
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
        return _execute_action_api(action, question)

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
    from core.orchestrator import process_request
    from core.contracts.contract_lock import validate_final_report
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(process_request, domain, question, session_id=session_id),
    )
    return validate_final_report(result)

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
    }


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


# ── System status (for StatusBar) ─────────────────────────────────────────

@app.get("/api/status")
async def system_status():
    """Quick status snapshot for the navbar StatusBar."""
    import os
    from core.config.preferences import load as load_prefs
    from core.docs.artifact_store import stats as art_stats, financial_summary

    prefs    = load_prefs()
    provider = prefs.get("llm", {}).get("provider", "ollama")

    # Ollama alive check
    ollama_ok = False
    try:
        import requests as _r
        ollama_ok = _r.get("http://localhost:11434", timeout=1).status_code == 200
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
        from memory.storage import MEMORY_DB_PATH, init_db
        import sqlite3 as _sq
        init_db()
        with _sq.connect(MEMORY_DB_PATH) as _c:
            mem_count = _c.execute("SELECT COUNT(*) FROM memory_nodes").fetchone()[0]
    except Exception:
        pass

    return {
        "provider":   provider,
        "ollama_ok":  ollama_ok,
        "docs":       total_docs,
        "memory":     mem_count,
        "fin_total":  round(fin_total, 2),
    }


# ── Chat ───────────────────────────────────────────────────────────────────

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

    from core.chat.session import get_or_create
    session = get_or_create(session_id, domain)
    session.add("user", message)

    # 1. Check for action requests first
    action = _detect_action(message)
    if action:
        action_result = _execute_action_api(action, message)
        reply = action_result.get("llm_insight", "Acción ejecutada.")
        session.add("assistant", reply, action=action)
        return {
            "reply":        reply,
            "session_id":   session_id,
            "action":       action,
            "action_data":  action_result,
            "history_len":  len(session.history),
        }

    # 2. RAG context — semantic search over indexed documents
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

    # 3. Build context-aware prompt
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
    return {
        "reply":       reply,
        "session_id":  session_id,
        "action":      None,
        "action_data": None,
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

