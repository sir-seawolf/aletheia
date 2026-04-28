import time
import hashlib


class LLMCacheV2:

    def __init__(self):
        # key -> {value, ts, domain}
        self.store = {}

        # TTL base (ajustable por dominio si quieres luego)
        self.ttl = 60 * 60  # 1 hora

    def _key(self, task: str, prompt: str, context: dict):
        domain = (context or {}).get("domain", "global")
        raw = f"{task}:{domain}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, task: str, prompt: str, context: dict):
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
