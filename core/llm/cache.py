import time
import hashlib
from typing import Optional


class LLMCacheV2:
    """
    LLM response cache v2 with TTL and domain invalidation.

    STATUS: IMPLEMENTED (production v1.1)
    Uses SHA256 key(task + domain + prompt). Context dict required for exact match.

    Public methods:
    - get(task: str, prompt: str, context: dict) → str | None
      Requires full (task, prompt, context) tuple for hit.
    - set(task: str, prompt: str, context: dict, value: str)
    - invalidate_domain(domain: str)
    """
    def __init__(self):
        # key -> {value, ts, domain}
        self.store = {}

        # TTL base (ajustable por dominio si quieres luego)
        self.ttl = 60 * 60  # 1 hora

    def _key(self, task: str, prompt: str, context: dict):
        domain = (context or {}).get("domain", "global")
        raw = f"{task}:{domain}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, task: str, prompt: str, context: dict) -> Optional[str]:
        """
        Retrieve cached response.

        Args:
            task (str): Task type e.g. 'exploration'
            prompt (str): Exact prompt string
            context (dict): Context dict (domain key critical)

        Returns:
            str | None: Cached response or None (miss/expired)
        """
        key = self._key(task, prompt, context)
        item = self.store.get(key)

        if not item:
            return None

        # expiración
        if time.time() - item["ts"] > self.ttl:
            del self.store[key]
            return None

        return item["value"]

    def set(self, task: str, prompt: str, context: dict, value: str):
        key = self._key(task, prompt, context)

        self.store[key] = {
            "value": value,
            "ts": time.time(),
            "domain": (context or {}).get("domain", "global")
        }

    def invalidate_domain(self, domain: str):
        """
        Limpieza selectiva cuando Palace o Memory cambian
        """
        keys_to_delete = [
            k for k, v in self.store.items()
            if v.get("domain") == domain
        ]

        for k in keys_to_delete:
            del self.store[k]
