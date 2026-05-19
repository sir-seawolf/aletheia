"""
Unit tests for core/pipeline/ (explorer, simulator, guardian).
LLM calls are mocked — no Ollama needed.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── Guardian ─────────────────────────────────────────────────────────────────

class TestGuardian:
    """Tests copied and updated from tests/test_guardian_behavior.py."""

    def _sim(self, **overrides):
        from datetime import datetime
        base = {
            # Required DecisionReport fields
            "timestamp":      datetime.now().isoformat(),
            "domain":         "test",
            "question":       "test?",
            "facts":          ["hecho1", "hecho2"],
            "gaps":           [],
            "scenarios": [
                {"type": "optimista",   "outcome": "pos", "probability": 0.6},
                {"type": "conservador", "outcome": "neu", "probability": 0.4},
            ],
            "risks":          {"riesgo_mercado": 0.3},
            "assumptions":    ["condiciones estables"],
            "llm_insight":    "El análisis muestra perspectiva positiva con riesgos controlados.",
            "llm_explanation": "Explicación detallada del análisis realizado.",
            "confidence":     0.75,
            "risk_level":     "medium",
            "prediction":     "proceed",
            # Extra fields used by rules
            "exploration_confidence": 0.7,
        }
        base.update(overrides)
        return base

    def test_valid_simulation_passes(self):
        from core.pipeline.guardian import validate
        result = validate(self._sim())
        assert result["valid"] is True
        assert result["block"] is False
        assert result["severity"] in ("none", "low")

    def test_missing_scenarios_blocks(self):
        from core.pipeline.guardian import validate
        result = validate(self._sim(scenarios=[{"type": "solo"}]))
        assert result["block"] is True
        assert any("comparacion" in i.lower() or "escenario" in i.lower() for i in result["issues"])

    def test_no_assumptions_flagged(self):
        from core.pipeline.guardian import validate
        result = validate(self._sim(assumptions=[]))
        issues_str = " ".join(result["issues"])
        assert "supuesto" in issues_str.lower()

    def test_low_exploration_confidence_flagged(self):
        from core.pipeline.guardian import validate
        result = validate(self._sim(exploration_confidence=0.3))
        issues_str = " ".join(result["issues"])
        assert "factual" in issues_str.lower() or "confianza" in issues_str.lower()

    def test_short_insight_flagged(self):
        from core.pipeline.guardian import validate
        result = validate(self._sim(llm_insight={"insight": "Ok.", "recommendation_bias": "conservative"}))
        issues_str = " ".join(result["issues"])
        assert "insight" in issues_str.lower()

    def test_confidence_adjust_decreases_with_issues(self):
        from core.pipeline.guardian import validate
        good = validate(self._sim())
        bad  = validate(self._sim(scenarios=[], assumptions=[], risks=[]))
        assert bad["confidence_adjust"] < good["confidence_adjust"]

    def test_corrected_output_has_guardian_fields(self):
        from core.pipeline.guardian import validate
        result = validate(self._sim())
        out = result["corrected_output"]
        assert "guardian_block" in out
        assert "guardian_recommendation" in out
        assert isinstance(out["guardian_block"], bool)

    def test_non_strict_mode_forgives_single_issue(self):
        from core.pipeline.guardian import validate
        # Provide a valid sim missing only the insight (one issue)
        sim = self._sim(
            llm_insight=".",    # too short → INSIGHT POCO DESARROLLADO
            exploration_confidence=0.8,
        )
        result = validate(sim, policy={"guardian_strict": False})
        # Non-strict forgives a single issue
        assert result["issues"] == []


# ── Explorer ──────────────────────────────────────────────────────────────────

class TestExplorer:

    def test_extract_relevant_facts_keyword_match(self):
        from core.pipeline.explorer import _extract_relevant_facts
        memory = [
            "Gastos mensuales del hogar: 1200€",
            "Ingresos netos: 2500€",
            "Vacaciones de verano",
        ]
        facts = _extract_relevant_facts(memory, "finanzas", "¿Puedo ahorrar más en finanzas?", profile=None)
        assert any("gastos" in f.lower() or "ingresos" in f.lower() for f in facts)

    def test_extract_respects_max_items(self):
        from core.pipeline.explorer import _extract_relevant_facts
        memory = [f"item financiero {i}" for i in range(20)]
        facts = _extract_relevant_facts(memory, "finanzas", "finanzas", profile=None)
        assert len(facts) <= 10

    def test_detect_gaps_low_evidence(self):
        from core.pipeline.explorer import _detect_gaps
        gaps = _detect_gaps([], {"min_evidence": 3}, profile=None)
        assert len(gaps) > 0
        assert any("3" in g for g in gaps)

    def test_detect_gaps_high_risk_temporal(self):
        from core.pipeline.explorer import _detect_gaps
        facts = ["El plan es viable"]
        gaps = _detect_gaps(facts, {"level": "high"}, profile=None)
        assert any("temporal" in g.lower() or "fecha" in g.lower() for g in gaps)

    def test_confidence_increases_with_facts(self):
        from core.pipeline.explorer import _calculate_confidence
        low  = _calculate_confidence([], [], None)
        high = _calculate_confidence(["f1", "f2", "f3", "f4", "f5"], [], None)
        assert high > low

    def test_confidence_decreases_with_gaps(self):
        from core.pipeline.explorer import _calculate_confidence
        no_gaps   = _calculate_confidence(["f1", "f2"], [], None)
        with_gaps = _calculate_confidence(["f1", "f2"], ["gap1", "gap2"], None)
        assert with_gaps < no_gaps

    def test_confidence_bounded(self):
        from core.pipeline.explorer import _calculate_confidence
        c = _calculate_confidence([], ["g"] * 10, None)
        assert 0.0 <= c <= 1.0

    def test_run_with_mock_llm(self):
        from core.pipeline.explorer import run
        mock_response = '{"facts": ["hecho1", "hecho2"], "gaps": [], "confidence": 0.8}'
        with patch("core.pipeline.explorer.router.generate", return_value=mock_response):
            result = run("finanzas", "¿Puedo ahorrar más?", memory=[])
        assert "facts" in result
        assert "confidence" in result
        assert isinstance(result["facts"], list)

    def test_run_fallback_when_llm_fails(self):
        from core.pipeline.explorer import run
        with patch("core.pipeline.explorer.router.generate", return_value="[ERROR]"):
            result = run("tecnologia", "¿Qué laptop comprar?", memory=["laptop precio: 1200€"])
        assert "facts" in result
        assert "confidence" in result


# ── Simulator ────────────────────────────────────────────────────────────────

class TestSimulator:

    def _exploration(self):
        return {
            "domain": "finanzas",
            "question": "¿Puedo dejar mi trabajo?",
            "facts": ["ahorros: 12000€", "gastos: 1200€/mes"],
            "gaps": [],
            "confidence": 0.75,
        }

    def test_run_with_mock_llm(self):
        from core.pipeline.simulator import run
        fake_scenarios = '{"scenarios": [{"type": "optimista", "outcome": "positivo", "probability": 0.6}, {"type": "conservador", "outcome": "neutral", "probability": 0.4}], "risks": ["riesgo empleo"], "assumptions": ["mercado estable"]}'
        fake_insight   = '{"insight": "El escenario es favorable dado el colchón de ahorro disponible."}'
        with patch("core.pipeline.simulator.router.generate", side_effect=[fake_scenarios, fake_insight]):
            result = run(self._exploration())
        assert "scenarios" in result
        assert "risks" in result
        assert "llm_insight" in result
        assert len(result["scenarios"]) >= 2

    def test_run_fallback_when_llm_fails(self):
        from core.pipeline.simulator import run
        with patch("core.pipeline.simulator.router.generate", return_value="garbage"):
            result = run(self._exploration())
        assert len(result["scenarios"]) >= 2
        assert result["scenarios"][0]["type"] in ("optimista", "conservador", "pesimista")

    def test_build_scenario_description(self):
        from core.pipeline.simulator import _build_scenario_description
        desc = _build_scenario_description("optimista", "finanzas")
        assert "finanzas" in desc
        assert len(desc) > 10

    def test_full_chain_explorer_simulator_guardian(self):
        """End-to-end v1 pipeline with mocked LLM calls."""
        from core.pipeline.explorer import run as explore
        from core.pipeline.simulator import run as simulate
        from core.pipeline.guardian import validate

        fake_expl    = '{"facts": ["f1", "f2", "f3"], "gaps": [], "confidence": 0.8}'
        fake_sim     = '{"scenarios": [{"type": "optimista", "outcome": "pos", "probability": 0.6}, {"type": "conservador", "outcome": "neu", "probability": 0.4}], "risks": ["r1"], "assumptions": ["a1"]}'
        fake_insight = '{"insight": "Análisis indica viabilidad con riesgo controlado y perspectivas positivas a medio plazo."}'

        # explorer + simulator share the same router object — patch once with all 3 responses
        from core.llm import router as _router
        with patch.object(_router, "generate", side_effect=[fake_expl, fake_sim, fake_insight]):

            exploration = explore("finanzas", "¿Puedo retirarme en 10 años?", memory=[])
            simulation  = simulate(exploration)
            validated   = validate(simulation)

        assert exploration["confidence"] > 0
        assert len(simulation["scenarios"]) >= 2
        assert "block" in validated
        assert "corrected_output" in validated
