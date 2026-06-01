"""
Central preferences store — PALACE/config/preferences.json

Schema:
{
  "llm": {
    "provider": "ollama" | "claude" | "openai",
    "model": "...",          // provider-specific model name
    "api_key": "..."         // stored locally, never sent to git
  },
  "voice": {
    "default_input": "text" | "voice",
    "stt_language": "es",
    "tts_model": "es_ES-davefx-medium"
  },
  "ui": {
    "theme": "dark"
  }
}
"""

import json
import time
from pathlib import Path
from typing import Any

_PREFS_PATH = Path(__file__).parent.parent.parent / "PALACE" / "config" / "preferences.json"

_prefs_cache: dict[str, Any] | None = None
_prefs_cache_ts: float = 0.0
_PREFS_CACHE_TTL = 5.0

_DEFAULTS: dict[str, Any] = {
    "llm": {
        "provider": "ollama",
        "model": "",
        "api_key": "",
        "failover_chain": [],
        # Per-agent provider overrides. Keys: agent id. Value: provider name.
        # Example: {"kronos": "claude", "conversacional": "ollama"}
        "agents": {},
    },
    "voice": {
        "default_input": "text",
        "stt_language": "es",
        "tts_model": "es_ES-davefx-medium",
    },
    "ui": {
        "theme": "dark",
    },
    "system": {
        "use_v3_modes":    False,
        "deferred_mode":   False,   # when True, MemoryBus.store() also enqueues to raw_buffer
        "consolidation_schedule": None,
    },
}


def load() -> dict[str, Any]:
    global _prefs_cache, _prefs_cache_ts
    if _prefs_cache is not None and (time.monotonic() - _prefs_cache_ts) < _PREFS_CACHE_TTL:
        return _prefs_cache
    if not _PREFS_PATH.exists():
        result = _deep_copy(_DEFAULTS)
    else:
        try:
            data = json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
            result = _merge(_DEFAULTS, data)
        except Exception:
            result = _deep_copy(_DEFAULTS)
    _prefs_cache = result
    _prefs_cache_ts = time.monotonic()
    return result


def save(prefs: dict[str, Any]) -> None:
    global _prefs_cache, _prefs_cache_ts
    _PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PREFS_PATH.write_text(
        json.dumps(prefs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _prefs_cache = None
    _prefs_cache_ts = 0.0


def update(section: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Merge *updates* into *section* and persist."""
    prefs = load()
    prefs.setdefault(section, {}).update(updates)
    save(prefs)
    return prefs


def get_llm_provider() -> str:
    return load().get("llm", {}).get("provider", "ollama")


_ENV_MAP = {
    "claude":       "ANTHROPIC_API_KEY",
    "openai":       "OPENAI_API_KEY",
    "deepseek":     "DEEPSEEK_API_KEY",
    "groq":         "GROQ_API_KEY",
    "mistral":      "MISTRAL_API_KEY",
    "openrouter":   "OPENROUTER_API_KEY",
}


def get_api_key(provider: str) -> str:
    """Return stored API key for *provider*."""
    import os
    stored = load().get("llm", {}).get("api_key", "")
    return stored or os.getenv(_ENV_MAP.get(provider, ""), "")


def get_failover_chain() -> list[dict]:
    """Return the ordered list of fallback providers."""
    return load().get("llm", {}).get("failover_chain", [])


def get_provider_for_agent(agent_id: str) -> str:
    """
    Return the configured provider for *agent_id*.
    Falls back to the global provider if no per-agent override is set.
    """
    prefs = load()
    agents = prefs.get("llm", {}).get("agents", {})
    return agents.get(agent_id) or prefs.get("llm", {}).get("provider", "ollama")


# ── helpers ────────────────────────────────────────────────────────────────

def _deep_copy(d: dict) -> dict:
    import copy
    return copy.deepcopy(d)


def _merge(defaults: dict, overrides: dict) -> dict:
    result = _deep_copy(defaults)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _merge(result[k], v)
        else:
            result[k] = v
    return result


def status() -> dict[str, Any]:
    """Return safe status dict (no API keys in plain text)."""
    from core.docs.gdrive import is_available as gdrive_ok
    from core.docs.onedrive import is_available as onedrive_ok
    from core.docs.local_drive import detected_roots

    prefs = load()
    llm = prefs.get("llm", {})
    provider = llm.get("provider", "ollama")
    has_key = bool(llm.get("api_key", ""))

    return {
        "llm": {
            "provider": provider,
            "model": llm.get("model", ""),
            "has_api_key": has_key,
        },
        "voice": prefs.get("voice", {}),
        "ui": prefs.get("ui", {}),
        "system": prefs.get("system", {"use_v3_modes": False, "deferred_mode": False}),
        "credentials": {
            "gdrive": gdrive_ok(),
            "onedrive": onedrive_ok(),
        },
        "local_drives": detected_roots(),
    }
