"""
Gmail connector for Aletheia.

Requires:
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Credentials setup (one-time):
  1. Same Google Cloud project as Drive (or a new one).
  2. Enable "Gmail API".
  3. OAuth2 credentials → download as JSON → save as PALACE/config/gmail_credentials.json
  4. First run opens browser for authorization → saves token to gmail_token.json.

Scopes used (read-only):
  https://www.googleapis.com/auth/gmail.readonly

What we scan:
  - Email body:       keyword excerpts (±200 chars around financial terms)
  - Attachments:      PDF, DOCX, TXT, CSV — downloaded and run through ingester
  - Deduplication:    every piece of content is stored via artifact_store (SHA-256)
"""

from __future__ import annotations

import base64
import tempfile
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

_CREDS_PATH  = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gmail_credentials.json"
_TOKEN_PATH  = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gmail_token.json"
_SCOPES      = ["https://www.googleapis.com/auth/gmail.readonly"]

_ATTACHMENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

_FINANCIAL_SUBJECT_KW = [
    "factura", "invoice", "recibo", "receipt", "payment", "pago",
    "gasto", "expense", "presupuesto", "quote", "order", "pedido",
    "subscription", "suscripción", "cobro", "cargo", "billing",
]


def is_available() -> bool:
    return _CREDS_PATH.exists()


# ── Auth ───────────────────────────────────────────────────────────────────

def _get_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "Falta google-api-python-client. "
            "Instala con: pip install google-api-python-client google-auth-oauthlib"
        )

    creds = None
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDS_PATH), _SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


# ── Core scan ──────────────────────────────────────────────────────────────

def _gmail_date(d: date) -> str:
    return d.strftime("%Y/%m/%d")


def _decode_body(payload: dict) -> str:
    """Recursively decode email body parts into plain text."""
    mime = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")
    parts = payload.get("parts", [])

    texts: list[str] = []

    if body_data and ("text/plain" in mime or "text/html" in mime):
        raw = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        if "text/html" in mime:
            # Strip HTML tags crudely
            import re
            raw = re.sub(r"<[^>]+>", " ", raw)
            raw = re.sub(r"\s+", " ", raw)
        texts.append(raw.strip())

    for part in parts:
        texts.append(_decode_body(part))

    return "\n".join(t for t in texts if t)


def _extract_attachments(service, msg_id: str, payload: dict) -> list[dict]:
    """Download attachments and return list of {filename, data, mime_type}."""
    results = []

    def _walk(parts: list):
        for part in parts:
            filename = part.get("filename", "")
            mime     = part.get("mimeType", "")
            body     = part.get("body", {})
            att_id   = body.get("attachmentId")

            if filename and att_id and mime in _ATTACHMENT_TYPES:
                att = service.users().messages().attachments().get(
                    userId="me", messageId=msg_id, id=att_id
                ).execute()
                data = base64.urlsafe_b64decode(att["data"] + "==")
                results.append({"filename": filename, "data": data, "mime_type": mime})

            _walk(part.get("parts", []))

    _walk(payload.get("parts", []))
    return results


def _header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


# ── Public API ─────────────────────────────────────────────────────────────

def scan_financial(
    date_from: date,
    date_to: date,
    update_existing: bool = False,
    progress_cb=None,
) -> dict[str, Any]:
    """
    Scan Gmail for financial emails between *date_from* and *date_to*.

    For each matching email:
      - Extracts a keyword excerpt from the body
      - Downloads PDF/DOCX attachments
      - Runs financial extraction on all content
      - Stores everything in the artifact_store (with dedup)

    Returns a summary dict.
    """
    if not is_available():
        return {"error": "Credenciales de Gmail no configuradas.", "available": False}

    from core.docs.ingester import extract_text
    from core.docs.artifact_store import ingest
    from core.docs.financial_extractor import (
        has_financial_content,
        extract_body_excerpt,
        extract_structured,
        FINANCIAL_KEYWORDS,
    )

    service = _get_service()

    # Build Gmail search query
    subject_filter = " OR ".join(f'subject:"{kw}"' for kw in _FINANCIAL_SUBJECT_KW[:8])
    query = (
        f"after:{_gmail_date(date_from)} before:{_gmail_date(date_to)} "
        f"({subject_filter})"
    )

    # Page through results
    msg_refs: list[dict] = []
    page_token = None
    while True:
        kwargs: dict[str, Any] = {"userId": "me", "q": query, "maxResults": 100}
        if page_token:
            kwargs["pageToken"] = page_token
        resp = service.users().messages().list(**kwargs).execute()
        msg_refs.extend(resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    summary = {
        "available":   True,
        "query":       query,
        "emails_found": len(msg_refs),
        "processed":   0,
        "new":         0,
        "updated":     0,
        "duplicate":   0,
        "skipped":     0,
        "invoices":    [],
        "errors":      [],
    }

    for ref in msg_refs:
        try:
            msg = service.users().messages().get(
                userId="me", messageId=ref["id"], format="full"
            ).execute()

            subject = _header(msg, "subject")
            sender  = _header(msg, "from")
            date_str = _header(msg, "date")
            msg_id  = msg["id"]
            iso_date = _parse_email_date(date_str)

            payload = msg.get("payload", {})
            body    = _decode_body(payload)

            # ── Body excerpt ──
            if body and has_financial_content(body):
                excerpt = extract_body_excerpt(body)
                if excerpt:
                    fin = extract_structured(excerpt, source_hint=sender)
                    r = ingest(
                        text=excerpt,
                        source=f"gmail:{msg_id}:body",
                        domain="finanzas",
                        artifact_type="email_excerpt",
                        filename=f"email_{msg_id[:8]}.txt",
                        source_date=iso_date,
                        financial=fin if fin.get("amount") else None,
                    )
                    _update_summary(summary, r, fin, subject, iso_date)

            # ── Attachments ──
            attachments = _extract_attachments(service, msg_id, payload)
            for att in attachments:
                suffix = Path(att["filename"]).suffix or ".bin"
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
                    tf.write(att["data"])
                    tmp_path = tf.name
                try:
                    text = extract_text(tmp_path)
                finally:
                    os.unlink(tmp_path)

                fin = extract_structured(text, source_hint=att["filename"])
                r = ingest(
                    text=text,
                    source=f"gmail:{msg_id}:{att['filename']}",
                    domain="finanzas",
                    artifact_type="invoice",
                    filename=att["filename"],
                    source_date=iso_date,
                    financial=fin if fin.get("amount") else None,
                )
                _update_summary(summary, r, fin, att["filename"], iso_date)

            summary["processed"] += 1
            if progress_cb:
                progress_cb(summary["processed"], len(msg_refs))

        except Exception as exc:
            summary["errors"].append(str(exc))

    return summary


def list_recent(max_results: int = 20) -> dict[str, Any]:
    """Return recent financial emails (no download, just metadata)."""
    if not is_available():
        return {"error": "Credenciales de Gmail no configuradas.", "available": False}

    service = _get_service()
    subject_filter = " OR ".join(f'subject:"{kw}"' for kw in _FINANCIAL_SUBJECT_KW[:6])
    resp = service.users().messages().list(
        userId="me", q=subject_filter, maxResults=max_results
    ).execute()

    items = []
    for ref in resp.get("messages", []):
        msg = service.users().messages().get(
            userId="me", messageId=ref["id"], format="metadata",
            metadataHeaders=["subject", "from", "date"]
        ).execute()
        items.append({
            "id":      msg["id"],
            "subject": _header(msg, "subject"),
            "from":    _header(msg, "from"),
            "date":    _header(msg, "date"),
        })

    return {"available": True, "emails": items}


# ── Helpers ────────────────────────────────────────────────────────────────

def _parse_email_date(date_str: str) -> str:
    """Convert email Date header to ISO YYYY-MM-DD."""
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""


def _update_summary(summary: dict, result, fin: dict, name: str, date: str) -> None:
    summary[result.status] = summary.get(result.status, 0) + 1
    if fin and fin.get("amount"):
        summary["invoices"].append({
            "filename": name,
            "date":     date,
            "vendor":   fin.get("vendor", ""),
            "amount":   fin.get("amount", 0),
            "currency": fin.get("currency", "EUR"),
            "status":   result.status,
        })
