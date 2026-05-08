"""HestiaObserver — passive event accumulator.

STATUS: IMPLEMENTED (Hestia v1)
"""

import json
from typing import Any, Dict

from core.hestia.memory import HestiaMemory


_HIGH_VALUE_DOMAINS = {"finanzas", "carrera", "tecnologia", "finance", "career"}
_CREATIVE_DOMAINS = {"creatividad", "aprendizaje", "creativity", "learning"}


class HestiaObserver:

    def __init__(self):
        self.memory = HestiaMemory()
        self.session_buffer: list[Dict[str, Any]] = []

    def observe(self, event: Dict[str, Any]) -> None:
        try:
            relevance = self._assess_relevance(event)
            if relevance > 0.3:
                obs = {
                    "timestamp": event.get("timestamp"),
                    "session_id": event.get("session_id"),
                    "domain": event.get("payload", {}).get("domain", "unknown"),
                    "summary": self._summarize(event),
                    "strategic_relevance": relevance,
                    "flags": json.dumps(self._flag(event)),
                }
                self.session_buffer.append(obs)
                if len(self.session_buffer) > 500:
                    self.session_buffer = self.session_buffer[-500:]
                self.memory.save_observation(obs)
        except Exception:
            pass

    def _assess_relevance(self, event: Dict[str, Any]) -> float:
        payload = event.get("payload", {})
        domain = payload.get("domain", "").lower()

        if payload.get("guardian_block"):
            return 0.9
        if domain in _HIGH_VALUE_DOMAINS:
            return 0.8
        facts = payload.get("facts_count", payload.get("facts", None))
        if facts == 0 or facts == []:
            return 0.6
        if domain in _CREATIVE_DOMAINS:
            return 0.4
        return 0.3

    def _summarize(self, event: Dict[str, Any]) -> str:
        agent = event.get("agent", "unknown")
        event_type = event.get("event_type", "event")
        domain = event.get("payload", {}).get("domain", "unknown")
        return f"{agent} procesó {domain}: {event_type}"

    def _flag(self, event: Dict[str, Any]) -> list:
        payload = event.get("payload", {})
        domain = payload.get("domain", "").lower()
        flags = []

        if domain in _HIGH_VALUE_DOMAINS:
            flags.append("high_value_domain")
        if payload.get("guardian_block"):
            flags.append("guardian_blocked")
        facts = payload.get("facts_count", payload.get("facts", None))
        if facts == 0 or facts == []:
            flags.append("empty_exploration")
        if domain and domain not in _HIGH_VALUE_DOMAINS and domain not in _CREATIVE_DOMAINS:
            flags.append("low_value_domain")

        domain_count = sum(
            1 for obs in self.session_buffer
            if obs.get("domain", "").lower() == domain
        )
        if domain_count > 3:
            flags.append("repeated_domain")

        return flags


hestia_observer = HestiaObserver()
