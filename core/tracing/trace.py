"""
CognitiveTrace — structured snapshot of one cognitive request lifecycle.

Every request that flows through Aletheia produces exactly one CognitiveTrace.
It captures: mode activated, routing decision, memory sources, fatigue delta,
latency, tokens, confidence, and output preview.

Use TraceBuilder to collect fields incrementally during a request,
then call .finish(output) to get the immutable CognitiveTrace.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CognitiveTrace:
    trace_id:               str
    session_id:             str
    timestamp:              str
    source:                 str          # "v1_pipeline" | "shadow_3.0" | "voice"

    # Request
    domain:                 str
    question_preview:       str          # first 80 chars

    # Mode activation (3.0 only; None for v1 pipeline)
    mode_activated:         Optional[str]
    observer_routing_reason: Optional[str]

    # LLM routing
    provider_used:          str
    model_tier:             str          # "local" | "free" | "premium" | "unknown"
    routing_reasoning:      str

    # Memory
    memory_sources:         List[str]    # ["episodic", "palace", "working", ...]
    memory_items_used:      int

    # Fatigue
    fatigue_before:         float
    fatigue_after:          float
    fatigue_delta:          float

    # Performance
    tokens_used:            int
    latency_ms:             float
    confidence:             float

    # Output
    output_preview:         str          # first 120 chars
    error:                  Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id":               self.trace_id,
            "session_id":             self.session_id,
            "timestamp":              self.timestamp,
            "source":                 self.source,
            "domain":                 self.domain,
            "question_preview":       self.question_preview,
            "mode_activated":         self.mode_activated,
            "observer_routing_reason": self.observer_routing_reason,
            "provider_used":          self.provider_used,
            "model_tier":             self.model_tier,
            "routing_reasoning":      self.routing_reasoning,
            "memory_sources":         self.memory_sources,
            "memory_items_used":      self.memory_items_used,
            "fatigue_before":         round(self.fatigue_before, 4),
            "fatigue_after":          round(self.fatigue_after, 4),
            "fatigue_delta":          round(self.fatigue_delta, 4),
            "tokens_used":            self.tokens_used,
            "latency_ms":             round(self.latency_ms, 1),
            "confidence":             round(self.confidence, 3),
            "output_preview":         self.output_preview,
            "error":                  self.error,
        }


class TraceBuilder:
    """
    Mutable accumulator for a single cognitive request.

    Usage:
        tb = TraceBuilder(session_id="abc", domain="finanzas", question="¿cuánto gasto?")
        tb.set_routing("ollama", "local", "fatigue=0.7")
        tb.set_mode("KRONOS", "keyword:gasto")
        tb.set_fatigue(0.1, 0.13)
        tb.add_memory_source("palace")
        trace = tb.finish(output="Gastas X€ al mes.", confidence=0.8)
    """

    def __init__(
        self,
        session_id: str,
        domain: str,
        question: str,
        source: str = "v1_pipeline",
    ) -> None:
        self.trace_id               = str(uuid.uuid4())
        self.session_id             = session_id
        self.timestamp              = _utc_now()
        self.source                 = source
        self.domain                 = domain
        self.question_preview       = question[:80]
        self._start                 = time.perf_counter()

        # Filled by various subsystems
        self.mode_activated:         Optional[str] = None
        self.observer_routing_reason: Optional[str] = None
        self.provider_used:          str            = "unknown"
        self.model_tier:             str            = "unknown"
        self.routing_reasoning:      str            = ""
        self._memory_sources:        List[str]      = []
        self.memory_items_used:      int            = 0
        self.fatigue_before:         float          = 0.0
        self.fatigue_after:          float          = 0.0
        self.tokens_used:            int            = 0
        self.confidence:             float          = 0.0
        self.error:                  Optional[str]  = None

    # ── Setters called by subsystems ────────────────────────────────────────

    def set_routing(self, provider: str, tier: str, reasoning: str) -> None:
        self.provider_used     = provider
        self.model_tier        = tier
        self.routing_reasoning = reasoning

    def set_mode(self, mode_id: str, routing_reason: Optional[str] = None) -> None:
        self.mode_activated          = mode_id
        self.observer_routing_reason = routing_reason

    def set_fatigue(self, before: float, after: float) -> None:
        self.fatigue_before = before
        self.fatigue_after  = after

    def add_memory_source(self, source: str) -> None:
        if source not in self._memory_sources:
            self._memory_sources.append(source)

    def set_memory_count(self, count: int) -> None:
        self.memory_items_used = count

    def add_tokens(self, n: int) -> None:
        self.tokens_used += n

    def set_error(self, msg: str) -> None:
        self.error = msg[:200]

    # ── Build ────────────────────────────────────────────────────────────────

    def finish(self, output: Any = "", confidence: float = 0.0) -> CognitiveTrace:
        latency = (time.perf_counter() - self._start) * 1000
        return CognitiveTrace(
            trace_id               = self.trace_id,
            session_id             = self.session_id,
            timestamp              = self.timestamp,
            source                 = self.source,
            domain                 = self.domain,
            question_preview       = self.question_preview,
            mode_activated         = self.mode_activated,
            observer_routing_reason = self.observer_routing_reason,
            provider_used          = self.provider_used,
            model_tier             = self.model_tier,
            routing_reasoning      = self.routing_reasoning,
            memory_sources         = list(self._memory_sources),
            memory_items_used      = self.memory_items_used,
            fatigue_before         = self.fatigue_before,
            fatigue_after          = self.fatigue_after,
            fatigue_delta          = round(self.fatigue_after - self.fatigue_before, 4),
            tokens_used            = self.tokens_used,
            latency_ms             = round(latency, 1),
            confidence             = confidence or self.confidence,
            output_preview         = str(output)[:120],
            error                  = self.error,
        )
