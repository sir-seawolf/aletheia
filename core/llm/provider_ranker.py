from __future__ import annotations

import os
import time
from typing import Any, Dict, List

_PROVIDER_BASE: Dict[str, Dict[str, Any]] = {
    "ollama":     {"latency_ms": 120, "reliability": 0.92, "free": True,  "needs_key": False},
    "groq":       {"latency_ms": 180, "reliability": 0.90, "free": True,  "needs_key": True},
    "openrouter": {"latency_ms": 220, "reliability": 0.88, "free": True,  "needs_key": True},
    "deepseek":   {"latency_ms": 260, "reliability": 0.87, "free": True,  "needs_key": True},
    "mistral":    {"latency_ms": 280, "reliability": 0.89, "free": True,  "needs_key": True},
    "claude":     {"latency_ms": 340, "reliability": 0.94, "free": False, "needs_key": True},
    "openai":     {"latency_ms": 360, "reliability": 0.93, "free": False, "needs_key": True},
}

_ENV_KEYS = {
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

_cache: Dict[str, Any] = {
    "last_refresh_ts": 0.0,
    "providers": [],
}


def _ollama_alive(timeout_s: float = 1.5) -> bool:
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=timeout_s)
        return r.status_code == 200
    except Exception:
        return False


def _has_key(provider: str, stored_provider: str, stored_key: str) -> bool:
    if provider == "ollama":
        return True
    if stored_provider == provider and bool(stored_key):
        return True
    env_name = _ENV_KEYS.get(provider, "")
    return bool(os.getenv(env_name, "")) if env_name else False


def refresh_catalog() -> Dict[str, Any]:
    try:
        from core.config.preferences import load as load_prefs
        prefs = load_prefs()
    except Exception:
        prefs = {}

    llm = prefs.get("llm", {})
    stored_provider = llm.get("provider", "ollama")
    stored_key = llm.get("api_key", "")

    ollama_ok = _ollama_alive()
    providers: List[Dict[str, Any]] = []

    for pname, base in _PROVIDER_BASE.items():
        available = bool(ollama_ok) if pname == "ollama" else _has_key(pname, stored_provider, stored_key)
        providers.append({
            "provider": pname,
            "available": available,
            "latency_ms": base["latency_ms"],
            "reliability": base["reliability"],
            "free": base["free"],
            "needs_key": base["needs_key"],
        })

    _cache["providers"] = providers
    _cache["last_refresh_ts"] = time.time()
    return {
        "ok": True,
        "providers": providers,
        "refreshed_at": _cache["last_refresh_ts"],
    }


def rank(policy: str = "fastest") -> Dict[str, Any]:
    if not _cache["providers"]:
        refresh_catalog()

    providers = list(_cache["providers"])
    policy = (policy or "fastest").strip().lower()
    if policy not in ("fastest", "most_reliable"):
        policy = "fastest"

    available = [p for p in providers if p["available"]]
    unavailable = [p for p in providers if not p["available"]]

    if policy == "most_reliable":
        available.sort(key=lambda p: (-p["reliability"], p["latency_ms"]))
    else:
        available.sort(key=lambda p: (p["latency_ms"], -p["reliability"]))

    ranked = available + unavailable
    return {
        "policy": policy,
        "ranking": ranked,
        "available_count": len(available),
        "total_count": len(providers),
        "refreshed_at": _cache.get("last_refresh_ts", 0.0),
    }


def best_provider(policy: str = "fastest") -> str:
    data = rank(policy)
    for p in data["ranking"]:
        if p.get("available"):
            return p["provider"]
    return "ollama"
