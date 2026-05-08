"""
Google Drive online client (optional).

Requires:
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Credentials setup (one-time):
  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable "Google Drive API"
  3. Create OAuth2 credentials → Download as credentials.json
  4. Place credentials.json at PALACE/config/gdrive_credentials.json
  5. First run will open a browser for authorization → saves token.json

If credentials are absent, all functions return {"available": False}.
"""

from pathlib import Path
from typing import Any

_CREDS_PATH = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gdrive_credentials.json"
_TOKEN_PATH = Path(__file__).parent.parent.parent / "PALACE" / "config" / "gdrive_token.json"
_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def is_available() -> bool:
    return _CREDS_PATH.exists()


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
            from google.auth.transport.requests import Request as Req
            creds.refresh(Req())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(_CREDS_PATH), _SCOPES)
            creds = flow.run_local_server(port=0)
        _TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds)


def list_files(query: str = "", max_results: int = 30) -> dict[str, Any]:
    if not is_available():
        return {"available": False, "message": "Credenciales de Google Drive no configuradas."}
    try:
        service = _get_service()
        q = f"name contains '{query}' and trashed=false" if query else "trashed=false"
        resp = service.files().list(
            q=q,
            pageSize=max_results,
            fields="files(id, name, mimeType, size, modifiedTime, webViewLink)",
        ).execute()
        return {"available": True, "files": resp.get("files", [])}
    except Exception as exc:
        return {"available": True, "error": str(exc)}


def download_file(file_id: str) -> dict[str, Any]:
    """Download a Drive file and return its text content."""
    if not is_available():
        return {"available": False}
    try:
        from googleapiclient.http import MediaIoBaseDownload
        import io, tempfile, os
        from core.docs.ingester import extract_text

        service = _get_service()
        meta = service.files().get(fileId=file_id, fields="name,mimeType").execute()
        mime = meta.get("mimeType", "")
        name = meta.get("name", file_id)

        # Google Docs → export as plain text
        if "google-apps" in mime:
            export_mime = "text/plain"
            req = service.files().export_media(fileId=file_id, mimeType=export_mime)
        else:
            req = service.files().get_media(fileId=file_id)

        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ".txt"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(buf.getvalue())
            tmp_path = tf.name

        try:
            text = extract_text(tmp_path)
        finally:
            os.unlink(tmp_path)

        return {"available": True, "name": name, "text": text}
    except Exception as exc:
        return {"available": True, "error": str(exc)}
