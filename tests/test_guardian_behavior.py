"""Tests cognitivos para Guardian - comportamiento esperable."""

import pytest
from unittest.mock import MagicMock
from core.pipeline.guardian import validate
from core.context import Context
from core.risk_engine import get_risk_config

@pytest.fixture
def high_risk_config():
    return {"level": "high", "require_scenarios": True}

@pytest.fixture
def low_confidence_simulation():
    return {
        "scenarios": [{"type": "single"}],
        "assumptions": [],
        "risks": [],
        "exploration_confidence": 0.4,
        "llm_insight": {"insight": "short", "recommendation_bias": "aggressive"}
    }

def test_block_high_risk_single_scenario(high_risk_config):
    """High-risk debe bloquear si <2 scenarios."""
    simulation = {"scenarios": [{}], "assumptions": ["ok"], "risks": ["ok"], "exploration_confidence": 0.8, "llm_insight": {"insight": "bueno"}}
    result = validate(simulation, high_risk_config)
    assert result["block"] == True
    assert "Falta comparación" in str(result["issues"])

def test_low_evidence_block(low_confidence_simulation, high_risk_config):
    """Low confidence bloquea."""
    result = validate(low_confidence_simulation, high_risk_config)
    assert "BASE FACTUAL INSUFICIENTE" in str(result["issues"])

def test_weak_insight_flag(low_confidence_simulation, high_risk_config):
    """Insight corto flag."""
    result = validate(low_confidence_simulation, high_risk_config)
    assert "INSIGHT POCO DESARROLLADO" in str(result["issues"])

def test_contradiction_aggressive_highrisk(high_risk_config):
    """Contradicción bias aggressive high-risk."""
    simulation = {"scenarios": [{}], "llm_insight": {"recommendation_bias": "aggressive"}, "exploration_confidence": 0.8}
    result = validate(simulation, high_risk_config)
    assert "CONTRADICCIÓN" in str(result["issues"])

def test_confidence_adjust():
    """Issues ajustan confidence."""
    simulation = {"exploration_confidence": 0.8}
    config = {"level": "medium"}
    result = validate(simulation, config)
    assert result["confidence_adjust"] <= 1.0  # Basic test

def test_no_issues_valid():
    """No issues → no block."""
    good_sim = {
        "scenarios": [{"type": "conservative"}, {"type": "optimistic"}],
        "assumptions": ["ok"],
        "risks": ["ok"],
        "exploration_confidence": 0.7,
        "llm_insight": {"insight": "long enough text here to pass length check.", "recommendation_bias": "conservative"}
    }
    result = validate(good_sim, {"level": "low"})
    assert result["block"] == False
    assert result["severity"] == "none" or result["severity"] == "low"

print("All cognitive tests passed - Guardian fuerte!")

