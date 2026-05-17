"""
Aletheia — Telegram bot.

Routes Telegram messages to the local Aletheia API so you can chat from
your phone without opening the browser.

Setup:
  1. Message @BotFather on Telegram → /newbot → copy the token
  2. Create PALACE/config/telegram.json:
       {
         "token": "1234567890:ABC...",
         "allowed_user_ids": [],   <- empty = accept anyone; add your id to restrict
         "admin_user_id": null     <- your Telegram user_id for status reports
       }
  3. python start.py --telegram   (or: python tools/telegram_bot.py)

The bot needs the Aletheia API running.  It auto-detects the port from
.running-ports; defaults to localhost:8000 if not found.

Requires:
  pip install python-telegram-bot httpx
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import httpx

ROOT        = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "PALACE" / "config" / "telegram.json"
PORTS_FILE  = ROOT / ".running-ports"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [TG] %(message)s")
log = logging.getLogger("aletheia.telegram")


# ── config ─────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        log.error(
            "No se encontró PALACE/config/telegram.json\n"
            "Crea el archivo con tu token de @BotFather:\n"
            '  {"token": "TU_TOKEN", "allowed_user_ids": [], "admin_user_id": null}'
        )
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _api_base() -> str:
    try:
        if PORTS_FILE.exists():
            port = int(PORTS_FILE.read_text().strip().splitlines()[0])
            return f"http://127.0.0.1:{port}"
    except Exception:
        pass
    return "http://127.0.0.1:8000"


# ── API helpers ────────────────────────────────────────────────────────────

async def _chat(client: httpx.AsyncClient, api: str, user_id: int, text: str) -> str:
    try:
        r = await client.post(
            f"{api}/api/chat",
            json={
                "message":    text,
                "session_id": f"tg-{user_id}",
                "domain":     "general",
            },
            timeout=60,
        )
        data = r.json()
        return data.get("reply") or "Sin respuesta."
    except httpx.ConnectError:
        return "No puedo conectar con Aletheia. ¿Está corriendo el servidor?"
    except Exception as exc:
        return f"Error: {exc}"


async def _poll_notifications(client: httpx.AsyncClient, api: str, user_id: int) -> list[str]:
    try:
        r = await client.get(f"{api}/api/notifications/poll?user_id=tg-{user_id}", timeout=5)
        items = r.json()
        return [n["text"] for n in items]
    except Exception:
        return []


async def _register_user(client: httpx.AsyncClient, api: str, user_id: int) -> None:
    try:
        await client.post(f"{api}/api/notifications/register", json={"user_id": f"tg-{user_id}"}, timeout=5)
    except Exception:
        pass


async def _ingest_doc(client: httpx.AsyncClient, api: str, filename: str, content: bytes) -> str:
    try:
        r = await client.post(
            f"{api}/api/docs/upload",
            files={"file": (filename, content)},
            timeout=120,
        )
        data = r.json()
        if data.get("ok") or data.get("status") in ("new", "updated", "duplicate"):
            return f"Documento «{filename}» guardado en PALACE."
        return f"Error al guardar: {data.get('error', 'desconocido')}"
    except Exception as exc:
        return f"No pude guardar el documento: {exc}"


# ── bot handlers ────────────────────────────────────────────────────────────

def _build_app(token: str, allowed: list[int], api: str):
    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        filters, ContextTypes,
    )

    def _allowed(uid: int) -> bool:
        return not allowed or uid in allowed

    async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        async with httpx.AsyncClient() as c:
            await _register_user(c, api, uid)
        await update.message.reply_text(
            "Hola, soy Aletheia.\n\n"
            "Puedes escribirme cualquier cosa o usar los comandos:\n"
            "/agenda — eventos de hoy\n"
            "/gastos — resumen financiero\n"
            "/fiscal — calculadora IRPF/IVA\n"
            "/buscar <texto> — búsqueda semántica\n"
            "/status — estado del sistema\n"
            "/help — esta ayuda"
        )

    async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await cmd_start(update, ctx)

    async def cmd_agenda(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        async with httpx.AsyncClient() as c:
            reply = await _chat(c, api, uid, "¿Qué tengo hoy en el calendario?")
        await update.message.reply_text(reply)

    async def cmd_gastos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        async with httpx.AsyncClient() as c:
            reply = await _chat(c, api, uid, "Resumen de gastos de este año")
        await update.message.reply_text(reply)

    async def cmd_fiscal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        async with httpx.AsyncClient() as c:
            reply = await _chat(c, api, uid, "Resumen fiscal de este año")
        await update.message.reply_text(reply)

    async def cmd_buscar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        query = " ".join(ctx.args) if ctx.args else ""
        if not query:
            await update.message.reply_text("Uso: /buscar <texto a buscar en tus documentos>")
            return
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{api}/api/rag/search", json={"query": query, "n": 4}, timeout=30)
        results = r.json().get("results", [])
        if not results:
            await update.message.reply_text(f"No encontré resultados para «{query}».")
            return
        lines = [f"Resultados para «{query}»:\n"]
        for i, res in enumerate(results, 1):
            meta = res.get("metadata", {})
            src  = meta.get("filename") or meta.get("source", "?")
            score = res.get("score", 0)
            lines.append(f"{i}. [{src}] (rel. {score:.0%})\n{res['text'][:200]}…\n")
        await update.message.reply_text("\n".join(lines)[:4000])

    async def cmd_myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        await update.message.reply_text(
            f"Tu Telegram user_id es: {uid}\n\n"
            f"Añádelo a PALACE/config/telegram.json en allowed_user_ids\n"
            f"para habilitar notificaciones proactivas de HESTIA."
        )

    async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        async with httpx.AsyncClient() as c:
            try:
                r = await c.get(f"{api}/api/status", timeout=5)
                s = r.json()
                text = (
                    f"Estado Aletheia:\n"
                    f"  LLM: {s.get('provider', '?')}\n"
                    f"  Ollama: {'✓' if s.get('ollama') else '✗'}\n"
                    f"  Artefactos: {s.get('artifacts', '?')}\n"
                    f"  API: {api}"
                )
            except Exception as exc:
                text = f"No puedo leer el estado: {exc}"
        await update.message.reply_text(text)

    async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        text = (update.message.text or "").strip()
        if not text:
            return
        await update.message.chat.send_action("typing")
        async with httpx.AsyncClient() as c:
            reply = await _chat(c, api, uid, text)
        await update.message.reply_text(reply[:4000])

    async def on_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not _allowed(uid):
            return
        doc  = update.message.document
        name = doc.file_name or "documento"
        ext  = Path(name).suffix.lower()
        if ext not in (".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx"):
            await update.message.reply_text(
                f"Formato «{ext}» no soportado. "
                "Envía PDF, DOCX, TXT, MD, CSV o XLSX."
            )
            return
        await update.message.reply_text(f"Recibiendo «{name}»…")
        file = await ctx.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        async with httpx.AsyncClient() as c:
            reply = await _ingest_doc(c, api, name, bytes(content))
        await update.message.reply_text(reply)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("myid",   cmd_myid))
    app.add_handler(CommandHandler("agenda", cmd_agenda))
    app.add_handler(CommandHandler("gastos", cmd_gastos))
    app.add_handler(CommandHandler("fiscal", cmd_fiscal))
    app.add_handler(CommandHandler("buscar", cmd_buscar))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    return app


# ── notification poller task ────────────────────────────────────────────────

async def _notification_loop(bot, allowed: list[int], api: str, interval: int = 60):
    """Poll /api/notifications/poll for each known user and forward via Telegram."""
    import re
    while True:
        await asyncio.sleep(interval)
        if not allowed:
            continue
        async with httpx.AsyncClient() as c:
            for uid in allowed:
                msgs = await _poll_notifications(c, api, uid)
                for msg in msgs:
                    try:
                        await bot.send_message(chat_id=uid, text=msg)
                    except Exception as exc:
                        log.warning(f"No pude enviar notificación a {uid}: {exc}")


# ── main ───────────────────────────────────────────────────────────────────

async def _run():
    cfg     = _load_config()
    token   = cfg.get("token", "")
    allowed = [int(x) for x in cfg.get("allowed_user_ids", []) if x]
    api     = _api_base()

    if not token or token == "YOUR_TOKEN_HERE":
        log.error("Token de Telegram no configurado en PALACE/config/telegram.json")
        sys.exit(1)

    log.info(f"Bot arrancando — API: {api}")
    if allowed:
        log.info(f"Usuarios permitidos: {allowed}")
    else:
        log.info("Sin restricción de usuarios (allowed_user_ids vacío)")

    app = _build_app(token, allowed, api)

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        log.info("Bot escuchando. Ctrl+C para detener.")

        # Background notification loop (only if we know which users to notify)
        if allowed:
            asyncio.create_task(_notification_loop(app.bot, allowed, api))

        # Keep running until interrupted
        stop_event = asyncio.Event()
        try:
            await stop_event.wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()


def main():
    try:
        from telegram import __version__ as tg_ver
        log.info(f"python-telegram-bot {tg_ver}")
    except ImportError:
        log.error("python-telegram-bot no instalado. Ejecuta: pip install python-telegram-bot httpx")
        sys.exit(1)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
