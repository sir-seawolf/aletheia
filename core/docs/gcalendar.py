"""
Google Calendar client (optional).

Requires:
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Credentials setup (one-time):
  1. Google Cloud Console → project → Enable "Google Calendar API"
  2. OAuth2 credentials → Download as credentials.json
  3. Place at PALACE/config/gcalendar_credentials.json
     (or reuse gdrive_credentials.json — same project works)
  4. First call opens a browser for authorization → saves token.

All functions return {"available": False} when credentials are absent.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

_CREDS_PATH  = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gcalendar_credentials.json"
_CREDS_ALT   = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gdrive_credentials.json"
_TOKEN_PATH  = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gcalendar_token.json"
_SCOPES      = ["https://www.googleapis.com/auth/calendar"]


def is_available() -> bool:
    return _CREDS_PATH.exists() or _CREDS_ALT.exists()


def _creds_file() -> Path:
    return _CREDS_PATH if _CREDS_PATH.exists() else _CREDS_ALT


def _get_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "google-api-python-client not installed. "
            "Run: pip install google-api-python-client google-auth-oauthlib"
        )

    creds = None
    if _TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(_TOKEN_PATH), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_creds_file()), _SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _fmt_event(e: dict) -> dict:
    start = e.get("start", {})
    end   = e.get("end", {})
    return {
        "id":          e.get("id", ""),
        "title":       e.get("summary", "(sin título)"),
        "start":       start.get("dateTime") or start.get("date", ""),
        "end":         end.get("dateTime") or end.get("date", ""),
        "location":    e.get("location", ""),
        "description": (e.get("description") or "")[:200],
        "link":        e.get("htmlLink", ""),
        "all_day":     "dateTime" not in start,
    }


# ── public API ─────────────────────────────────────────────────────────────

def list_events(
    days_back: int = 0,
    days_ahead: int = 7,
    max_results: int = 20,
    calendar_id: str = "primary",
) -> dict[str, Any]:
    """Return events in the [now - days_back, now + days_ahead] window."""
    if not is_available():
        return {"available": False, "message": "Credenciales de Google Calendar no configuradas."}
    try:
        service = _get_service()
        now = _now_utc()
        time_min = (now - timedelta(days=days_back)).isoformat()
        time_max = (now + timedelta(days=days_ahead)).isoformat()
        resp = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = [_fmt_event(e) for e in resp.get("items", [])]
        return {"available": True, "events": events, "count": len(events)}
    except Exception as exc:
        return {"available": True, "error": str(exc)}


def today_events(calendar_id: str = "primary") -> dict[str, Any]:
    """Events for today only."""
    if not is_available():
        return {"available": False, "message": "Credenciales de Google Calendar no configuradas."}
    try:
        service = _get_service()
        now   = _now_utc()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = start + timedelta(days=1)
        resp  = service.events().list(
            calendarId=calendar_id,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = [_fmt_event(e) for e in resp.get("items", [])]
        return {"available": True, "events": events, "count": len(events), "date": start.date().isoformat()}
    except Exception as exc:
        return {"available": True, "error": str(exc)}


def search_events(query: str, max_results: int = 10, calendar_id: str = "primary") -> dict[str, Any]:
    """Full-text search across all calendar events."""
    if not is_available():
        return {"available": False, "message": "Credenciales de Google Calendar no configuradas."}
    try:
        service = _get_service()
        resp = service.events().list(
            calendarId=calendar_id,
            q=query,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = [_fmt_event(e) for e in resp.get("items", [])]
        return {"available": True, "events": events, "count": len(events), "query": query}
    except Exception as exc:
        return {"available": True, "error": str(exc)}


def create_event(
    title: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
) -> dict[str, Any]:
    """
    Create a calendar event.
    start_iso / end_iso: ISO 8601 datetime strings (e.g. "2026-05-10T10:00:00+02:00")
    or date-only strings for all-day events (e.g. "2026-05-10").
    """
    if not is_available():
        return {"available": False, "message": "Credenciales de Google Calendar no configuradas."}
    try:
        service = _get_service()
        all_day = len(start_iso) == 10  # "YYYY-MM-DD" format

        if all_day:
            body: dict[str, Any] = {
                "summary":     title,
                "description": description,
                "location":    location,
                "start": {"date": start_iso},
                "end":   {"date": end_iso},
            }
        else:
            body = {
                "summary":     title,
                "description": description,
                "location":    location,
                "start": {"dateTime": start_iso},
                "end":   {"dateTime": end_iso},
            }

        event = service.events().insert(calendarId=calendar_id, body=body).execute()
        return {"available": True, "created": True, "event": _fmt_event(event)}
    except Exception as exc:
        return {"available": True, "created": False, "error": str(exc)}


def delete_event(event_id: str, calendar_id: str = "primary") -> dict[str, Any]:
    """Delete an event by ID."""
    if not is_available():
        return {"available": False}
    try:
        service = _get_service()
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"available": True, "deleted": True}
    except Exception as exc:
        return {"available": True, "deleted": False, "error": str(exc)}


def format_summary(events: list[dict]) -> str:
    """Format event list as a readable string for LLM/voice."""
    if not events:
        return "No hay eventos."
    lines = []
    for e in events:
        start = e.get("start", "")
        if "T" in start:
            try:
                dt = datetime.fromisoformat(start)
                time_str = dt.strftime("%H:%M")
                date_str = dt.strftime("%d/%m")
            except ValueError:
                time_str = start[:5]
                date_str = ""
        else:
            time_str = "todo el día"
            date_str = start
        loc = f" — {e['location']}" if e.get("location") else ""
        lines.append(f"• {date_str} {time_str}: {e['title']}{loc}")
    return "\n".join(lines)
