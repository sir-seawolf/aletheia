"""
TraceLearner — adaptive learning engine for Aletheia cognitive routing.

Reads cognitive_traces + trace_divergences via SQL aggregation,
computes ranked ModeInsights and ProviderInsights, and exposes
recommendation APIs consumed by ObserverMode and RoutingIntelligence.

ALL computation is deterministic (SQL + arithmetic) — no LLM involved.
Recommendations are only made when usage_count >= MIN_SAMPLES (default: 5).
Below that threshold the system falls back to keyword/rule-based routing.

Public API:
    trace_learner.recommend_mode(domain, state)   → Optional[ModeID]
    trace_learner.recommend_blend(domain, state)  → Optional[str]   (preset name)
    trace_learner.recommend_provider(task, state) → Optional[str]   (provider name)
    trace_learner.compute_insights()              → (modes, providers)
    trace_learner.insights_for(domain)            → List[ModeInsight]
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from core.cognitive_state import CognitiveState
from core.cognition.insights import (
    InsightCache, ModeInsight, ProviderInsight, MIN_SAMPLES,
)

_DB_PATH = "memory/data/aletheia.db"

# Blend preset names (from core.modes.blend.BLEND_PRESETS)
_BLEND_PRESET_NAMES = {
    "strategic_analytical", "reflective_kronos", "creative_world",
    "analytical_reflective", "strategic_creative", "kronos_strategic",
}

# ── SQL queries ───────────────────────────────────────────────────────────────

_MODE_PERF_SQL = """
SELECT
    COALESCE(domain, 'general')    AS domain,
    mode_activated,
    AVG(confidence)                AS avg_confidence,
    AVG(latency_ms)                AS avg_latency_ms,
    AVG(fatigue_delta)             AS avg_fatigue_delta,
    AVG(tokens_used)               AS avg_tokens,
    COUNT(*)                       AS usage_count
FROM cognitive_traces
WHERE mode_activated IS NOT NULL
  AND source NOT IN ('shadow_3.0', 'replay')
GROUP BY domain, mode_activated
ORDER BY avg_confidence DESC
"""

_SHADOW_WIN_SQL = """
SELECT
    mode_activated,
    CAST(SUM(CASE WHEN overall_winner = 'shadow_3.0' THEN 1 ELSE 0 END) AS REAL)
        / COUNT(*) AS win_rate,
    COUNT(*) AS comparison_count
FROM trace_divergences
WHERE mode_activated IS NOT NULL
GROUP BY mode_activated
"""

_PROVIDER_PERF_SQL = """
SELECT
    provider_used,
    model_tier,
    AVG(confidence)    AS avg_confidence,
    AVG(latency_ms)    AS avg_latency_ms,
    AVG(tokens_used)   AS avg_tokens,
    COUNT(*)           AS usage_count
FROM cognitive_traces
WHERE provider_used NOT IN ('unknown', 'deterministic', 'mock')
  AND source NOT IN ('shadow_3.0', 'replay')
GROUP BY provider_used, model_tier
ORDER BY avg_confidence DESC
"""


class TraceLearner:

    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._db    = db_path
        self._cache = InsightCache()

    # ── Public recommendations ───────────────────────────────────────────────

    def recommend_mode(
        self,
        domain: str,
        state: CognitiveState,
    ) -> Optional[str]:
        """
        Return the mode_or_blend string with the highest rank_score for this domain.
        Returns None if no qualified insight exists (below MIN_SAMPLES or all degraded).
        Ignores blend presets — use recommend_blend() for those.
        """
        insights = self._fresh_mode_insights()
        domain_insights = [
            i for i in insights
            if i.domain in (domain, "general")
            and i.qualifies()
            and i.mode_or_blend not in _BLEND_PRESET_NAMES
            and _mode_compatible_with_state(i.mode_or_blend, state)
        ]
        if not domain_insights:
            return None
        best = max(domain_insights, key=lambda i: i.rank_score)
        return best.mode_or_blend

    def recommend_blend(
        self,
        domain: str,
        state: CognitiveState,
    ) -> Optional[str]:
        """
        Return the blend preset name with the highest rank_score for this domain.
        Only recommended when state.energy > 0.5 (blend is energy-expensive).
        """
        if state.energy <= 0.5:
            return None

        insights = self._fresh_mode_insights()
        blend_insights = [
            i for i in insights
            if i.domain in (domain, "general")
            and i.qualifies()
            and i.mode_or_blend in _BLEND_PRESET_NAMES
        ]
        if not blend_insights:
            return None
        best = max(blend_insights, key=lambda i: i.rank_score)
        return best.mode_or_blend

    def recommend_provider(
        self,
        task: str,
        state: CognitiveState,
    ) -> Optional[str]:
        """
        Return the provider with the best efficiency_score for this task type.
        Respects CognitiveState tier constraints — never recommends premium if fatigued.
        Returns None if no qualified provider history exists.
        """
        providers = self._fresh_provider_insights()
        allowed_tier = state.preferred_model_tier

        # Build tier allowlist: "local" allows only local; "free" allows local+free; "premium" all
        tier_allowed = {
            "local":   {"local"},
            "free":    {"local", "free"},
            "premium": {"local", "free", "premium"},
        }.get(allowed_tier, {"local"})

        candidates = [
            p for p in providers
            if p.qualifies() and p.model_tier in tier_allowed
        ]
        if not candidates:
            return None
        best = max(candidates, key=lambda p: p.efficiency_score)
        return best.provider

    # ── Insight accessors ────────────────────────────────────────────────────

    def insights_for(self, domain: str) -> List[ModeInsight]:
        """All insights for a specific domain, sorted by rank_score desc."""
        return sorted(
            [i for i in self._fresh_mode_insights() if i.domain == domain],
            key=lambda i: -i.rank_score,
        )

    def all_insights(self) -> Dict[str, Any]:
        modes     = self._fresh_mode_insights()
        providers = self._fresh_provider_insights()
        return {
            "modes":     [i.to_dict() for i in modes],
            "providers": [p.to_dict() for p in providers],
            "cache_age_seconds": round(
                (self._cache.last_updated() or 0) and
                __import__("time").time() - (self._cache.last_updated() or 0), 1
            ),
        }

    # ── Recomputation ────────────────────────────────────────────────────────

    def compute_insights(self, force: bool = False) -> Tuple[List[ModeInsight], List[ProviderInsight]]:
        """
        Aggregate trace data from SQLite. Rebuilds cache.
        Call with force=True to bypass TTL (e.g. from /api/learning/recompute).
        """
        if not force and not self._cache.is_stale():
            return self._cache.get_modes(), self._cache.get_providers()

        try:
            modes     = self._aggregate_modes()
            providers = self._aggregate_providers()
        except Exception:
            return self._cache.get_modes(), self._cache.get_providers()

        # Apply degradation flags
        try:
            from core.cognition.degradation import strategy_degradation
            for insight in modes:
                insight.degraded = strategy_degradation.is_degraded(
                    insight.domain, insight.mode_or_blend
                )
                # Record this result for penalty tracking
                strategy_degradation.record_result(
                    insight.domain, insight.mode_or_blend, insight.rank_score
                )
        except Exception:
            pass

        self._cache.set(modes, providers)
        return modes, providers

    def invalidate(self) -> None:
        """Force cache invalidation on next access."""
        self._cache.invalidate()

    # ── Private aggregation ──────────────────────────────────────────────────

    def _fresh_mode_insights(self) -> List[ModeInsight]:
        if self._cache.is_stale():
            self.compute_insights()
        return self._cache.get_modes()

    def _fresh_provider_insights(self) -> List[ProviderInsight]:
        if self._cache.is_stale():
            self.compute_insights()
        return self._cache.get_providers()

    def _aggregate_modes(self) -> List[ModeInsight]:
        win_rates = self._fetch_shadow_win_rates()
        rows = self._query(_MODE_PERF_SQL)
        insights: List[ModeInsight] = []
        for r in rows:
            mode      = r["mode_activated"]
            win_rate  = win_rates.get(mode, 0.5)
            insights.append(ModeInsight.compute(
                domain            = r["domain"],
                mode_or_blend     = mode,
                avg_confidence    = float(r["avg_confidence"]    or 0),
                avg_latency_ms    = float(r["avg_latency_ms"]    or 0),
                avg_fatigue_delta = float(r["avg_fatigue_delta"] or 0),
                avg_tokens        = float(r["avg_tokens"]        or 0),
                usage_count       = int(r["usage_count"]         or 0),
                shadow_win_rate   = win_rate,
            ))
        return insights

    def _aggregate_providers(self) -> List[ProviderInsight]:
        rows = self._query(_PROVIDER_PERF_SQL)
        return [
            ProviderInsight.compute(
                provider       = r["provider_used"],
                model_tier     = r["model_tier"] or "unknown",
                avg_confidence = float(r["avg_confidence"] or 0),
                avg_latency_ms = float(r["avg_latency_ms"] or 0),
                avg_tokens     = float(r["avg_tokens"]     or 0),
                usage_count    = int(r["usage_count"]      or 0),
            )
            for r in rows
        ]

    def _fetch_shadow_win_rates(self) -> Dict[str, float]:
        try:
            rows = self._query(_SHADOW_WIN_SQL)
            return {r["mode_activated"]: float(r["win_rate"] or 0.5) for r in rows}
        except Exception:
            return {}

    def _query(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        try:
            conn = sqlite3.connect(self._db, timeout=5)
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            conn.close()
            return rows
        except Exception:
            return []


# ── Utility ───────────────────────────────────────────────────────────────────

def _mode_compatible_with_state(mode_str: str, state: CognitiveState) -> bool:
    """Exclude high-energy modes when state is fatigued."""
    heavy = {"WORLD_MODEL", "EXECUTIVE"}
    if state.fatigue > 0.6 and mode_str in heavy:
        return False
    return True


# Singleton
trace_learner = TraceLearner()
