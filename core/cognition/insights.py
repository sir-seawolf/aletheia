"""
Cognitive insights — structured performance knowledge derived from trace history.

ModeInsight    : per (domain, mode/blend) historical performance metrics + rank score.
ProviderInsight: per (provider, task) historical performance + efficiency score.
InsightCache   : thread-safe in-memory cache with TTL; prevents DB hammering.

All values are computed deterministically from SQLite — no LLM involved.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Minimum samples before a recommendation is trusted
MIN_SAMPLES: int = 5

# Rank score weights (must sum to 1.0)
_RANK_WEIGHTS = {
    "quality":    0.40,   # avg_confidence
    "frugality":  0.30,   # 1 − avg_fatigue_delta
    "efficiency": 0.20,   # 1 − (avg_tokens / 2000)
    "shadow_val": 0.10,   # shadow win_rate
}

# Cache TTL in seconds — recompute after this interval
CACHE_TTL: float = 300.0


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class ModeInsight:
    domain:             str
    mode_or_blend:      str        # ModeID.value or blend preset name
    avg_confidence:     float
    avg_latency_ms:     float
    avg_fatigue_delta:  float
    avg_tokens:         float
    usage_count:        int
    shadow_win_rate:    float      # 0.5 = no shadow data (neutral)
    rank_score:         float      # composite score in [0, 1]
    degraded:           bool = False

    @classmethod
    def compute(
        cls,
        domain: str,
        mode_or_blend: str,
        avg_confidence: float,
        avg_latency_ms: float,
        avg_fatigue_delta: float,
        avg_tokens: float,
        usage_count: int,
        shadow_win_rate: float = 0.5,
        degraded: bool = False,
    ) -> ModeInsight:
        rank = _rank_score(avg_confidence, avg_fatigue_delta, avg_tokens, shadow_win_rate)
        return cls(
            domain=domain,
            mode_or_blend=mode_or_blend,
            avg_confidence=round(avg_confidence, 4),
            avg_latency_ms=round(avg_latency_ms, 1),
            avg_fatigue_delta=round(avg_fatigue_delta, 4),
            avg_tokens=round(avg_tokens, 1),
            usage_count=usage_count,
            shadow_win_rate=round(shadow_win_rate, 4),
            rank_score=round(rank, 4),
            degraded=degraded,
        )

    def qualifies(self) -> bool:
        """True if this insight has enough data and is not degraded."""
        return self.usage_count >= MIN_SAMPLES and not self.degraded

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain":            self.domain,
            "mode_or_blend":     self.mode_or_blend,
            "avg_confidence":    self.avg_confidence,
            "avg_latency_ms":    self.avg_latency_ms,
            "avg_fatigue_delta": self.avg_fatigue_delta,
            "avg_tokens":        self.avg_tokens,
            "usage_count":       self.usage_count,
            "shadow_win_rate":   self.shadow_win_rate,
            "rank_score":        self.rank_score,
            "degraded":          self.degraded,
            "qualifies":         self.qualifies(),
        }


@dataclass
class ProviderInsight:
    provider:          str
    model_tier:        str
    avg_confidence:    float
    avg_latency_ms:    float
    avg_tokens:        float
    usage_count:       int
    efficiency_score:  float   # confidence / (latency_ms / 1000 + 0.1) — quality per second

    @classmethod
    def compute(
        cls,
        provider: str,
        model_tier: str,
        avg_confidence: float,
        avg_latency_ms: float,
        avg_tokens: float,
        usage_count: int,
    ) -> ProviderInsight:
        eff = avg_confidence / (avg_latency_ms / 1000.0 + 0.1)
        return cls(
            provider=provider,
            model_tier=model_tier,
            avg_confidence=round(avg_confidence, 4),
            avg_latency_ms=round(avg_latency_ms, 1),
            avg_tokens=round(avg_tokens, 1),
            usage_count=usage_count,
            efficiency_score=round(eff, 4),
        )

    def qualifies(self) -> bool:
        return self.usage_count >= MIN_SAMPLES

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider":         self.provider,
            "model_tier":       self.model_tier,
            "avg_confidence":   self.avg_confidence,
            "avg_latency_ms":   self.avg_latency_ms,
            "avg_tokens":       self.avg_tokens,
            "usage_count":      self.usage_count,
            "efficiency_score": self.efficiency_score,
            "qualifies":        self.qualifies(),
        }


# ── Cache ────────────────────────────────────────────────────────────────────

class InsightCache:
    """
    Thread-safe in-memory cache for computed insights.
    Expires after CACHE_TTL seconds; recomputed on next access.
    """

    def __init__(self, ttl: float = CACHE_TTL) -> None:
        self._ttl    = ttl
        self._lock   = threading.Lock()
        self._modes:     List[ModeInsight]    = []
        self._providers: List[ProviderInsight] = []
        self._ts: float = 0.0

    def is_stale(self) -> bool:
        return (time.time() - self._ts) > self._ttl

    def set(
        self,
        modes: List[ModeInsight],
        providers: List[ProviderInsight],
    ) -> None:
        with self._lock:
            self._modes     = modes
            self._providers = providers
            self._ts        = time.time()

    def get_modes(self) -> List[ModeInsight]:
        with self._lock:
            return list(self._modes)

    def get_providers(self) -> List[ProviderInsight]:
        with self._lock:
            return list(self._providers)

    def invalidate(self) -> None:
        with self._lock:
            self._ts = 0.0

    def last_updated(self) -> Optional[float]:
        with self._lock:
            return self._ts if self._ts > 0 else None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _rank_score(
    avg_confidence: float,
    avg_fatigue:    float,
    avg_tokens:     float,
    win_rate:       float,
) -> float:
    quality    = avg_confidence * _RANK_WEIGHTS["quality"]
    frugality  = (1.0 - min(avg_fatigue, 1.0))           * _RANK_WEIGHTS["frugality"]
    efficiency = (1.0 - min(avg_tokens / 2000.0, 1.0))   * _RANK_WEIGHTS["efficiency"]
    shadow_val = win_rate                                  * _RANK_WEIGHTS["shadow_val"]
    return max(0.0, min(1.0, quality + frugality + efficiency + shadow_val))
