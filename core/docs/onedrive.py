"""
OneDrive / Microsoft Graph online client (optional).

Requires:
  pip install msal requests

Credentials setup (one-time):
  1. Go to https://portal.azure.com/ → App registrations → New registration
  2. Add "Files.Read" permission under Microsoft Graph
  3. Create a client secret
  4. Save config at PALACE/config/onedrive_config.json:
     {
       "client_id": "...",
       "client_secret": "...",
       "tenant_id": "consumers"   (or your tenant ID for work accounts)
     }

If config is absent, all functions return {"available": False}.
"""

from pathlib import Path
from typing import Any
import json

_CONFIG_PATH = Path(__file__).parent.parent.parent / "PALACE" / "config" / "onedrive_config.json"
_TOKEN_CACHE  = Path(__file__).parent.parent.parent / "PALACE" / "config" / "onedrive_token.json"
_SCOPE = ["Files.Read", "User.Read"]
_GRAPH = "https://graph.microsoft.com/v1.0"


def is_available() -> bool:
    return _CONFIG_PATH.exists()


def _load_cfg() -> dict:
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def _get_token() -> str:
    try:
        import msal
    except ImportError:
        raise RuntimeError("msal not installed. Run: pip install msal")

    cfg = _load_cfg()
    cache = msal.SerializableTokenCache()
    if _TOKEN_CACHE.exists():
        cache.deserialize(_TOKEN_CACHE.read_text(encoding="utf-8"))

    app = msal.PublicClientApplication(
        cfg["client_id"],
        authority=f"https://login.microsoftonline.com/{cfg.get('tenant_id', 'consumers')}",
        token_cache=cache,
    )

    accounts = app.get_accounts()
    result = app.acquire_token_silent(_SCOPE, account=accounts[0]) if accounts else None

    if not result:
        # Interactive login (opens browser)
        result = app.acquire_token_interactive(scopes=_SCOPE)

    if "access_token" not in result:
        raise RuntimeError(f"OneDrive auth failed: {result.get('error_description')}")

    _TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_CACHE.write_text(cache.serialize(), encoding="utf-8")
    return result["access_token"]


def list_files(query: str = "", max_results: int = 30) -> dict[str, Any]:
    if not is_available():
        return {"available": False, "message": "Credenciales de OneDrive no configuradas."}
    try:
        import requests
        token = _get_token()
        headers = {"Authorization": f"Bearer {token}"}

        if query:
            url = f"{_GRAPH}/me/drive/root/search(q='{query}')?$top={max_results}"
        else:
            url = f"{_GRAPH}/me/drive/root/children?$top={max_results}"

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {"available": True, "files": data.get("value", [])}
    except Exception as exc:
        return {"available": True, "error": str(exc)}


def download_file(item_id: str) -> dict[str, Any]:
    """Download a OneDrive file and return its text content."""
    if not is_available():
        return {"available": False}
    try:
        import requests, io, tempfile, os
        from core.docs.ingester import extract_text

        token = _get_token()
        headers = {"Authorization": f"Bearer {token}"}

        meta_url = f"{_GRAPH}/me/drive/items/{item_id}"
        meta = requests.get(meta_url, headers=headers, timeout=15).json()
        name = meta.get("name", item_id)

        dl_url = meta.get("@microsoft.graph.downloadUrl") or f"{meta_url}/content"
        content = requests.get(dl_url, headers=headers, timeout=60).content

        suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(content)
            tmp_path = tf.name

        try:
            text = extract_text(tmp_path)
        finally:
            os.unlink(tmp_path)

        return {"available": True, "name": name, "text": text}
    except Exception as exc:
        return {"available": True, "error": str(exc)}
