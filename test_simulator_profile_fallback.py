"""
Tests para validar que el fallback del simulador es adaptativo al perfil cognitivo.

Objetivo: Profile A y Profile B deben producir salidas DIFERENTES
incluso cuando Ollama NO está disponible (fallback estructurado).
"""

from types import SimpleNamespace
from core.context import Context
from agents.simulator import _build_scenario_description

# Perfiles de prueba
PROFILE_A = SimpleNamespace(
    verbosity_preference="baja",
    structure_preference="sistémica",
    abstraction_capacity="baja",
)

PROFILE_B = SimpleNamespace(
    verbosity_preference="alta",
    structure_preference="narrativa",
    abstraction_capacity="alta",
)

RISK_CONFIG = {"level": "high", "allow_creativity": False}

QUESTION = "¿Puedo dejar mi trabajo en 9 meses?"
FACTS = [
    "Ahorros actuales: 12000€",
    "Gastos mensuales: 1200€",
]


def make_context(profile):
    return Context(
        domain="finanzas",
        risk=RISK_CONFIG,
        memory=FACTS,
        question=QUESTION,
        user_profile=profile,
    )


def test_fallback_profile_a_short():
    """Profile A (baja + sistémica) → salida corta y estructurada."""
    ctx = make_context(PROFILE_A)
    desc = _build_scenario_description(ctx, FACTS, "conservative")

    # Debe ser una línea corta, sin secciones narrativas
    assert "Escenario conservative para:" in desc
    assert "Situación:" not in desc
    assert "Interpretación:" not in desc
    assert "Implicaciones:" not in desc
    assert "Resumen conciso." in desc
    print(f"[PASS] Profile A short output ({len(desc)} chars): {desc[:80]}...")


def test_fallback_profile_b_rich():
    """Profile B (alta + narrativa) → salida más rica con secciones."""
    ctx = make_context(PROFILE_B)
    desc = _build_scenario_description(ctx, FACTS, "optimistic")

    # Debe tener estructura narrativa
    assert "Situación:" in desc
    assert "Interpretación:" in desc
    assert "Implicaciones:" in desc
    # Densidad alta
    assert "análisis extendido de variables clave" in desc
    assert "recomendaciones de contingencia" in desc
    print(f"[PASS] Profile B rich output ({len(desc)} chars): {desc[:80]}...")


def test_profiles_are_different():
    """A y B deben producir descripciones distintas en fallback."""
    ctx_a = make_context(PROFILE_A)
    ctx_b = make_context(PROFILE_B)

    desc_a = _build_scenario_description(ctx_a, FACTS, "conservative")
    desc_b = _build_scenario_description(ctx_b, FACTS, "conservative")

    assert desc_a != desc_b, (
        f"Profile A y B deberían diferir en fallback.\nA: {desc_a}\nB: {desc_b}"
    )

    # B debe ser más largo
    assert len(desc_b) > len(desc_a), (
        f"Profile B debería ser más largo que A. A={len(desc_a)}, B={len(desc_b)}"
    )
    print(f"[PASS] A != B | A len={len(desc_a)} | B len={len(desc_b)}")


def test_no_profile_defaults():
    """Sin perfil debe comportarse como estructura sistémica + media."""
    ctx = make_context(profile=None)
    desc = _build_scenario_description(ctx, FACTS, "exploratory")

    assert "Escenario exploratory para:" in desc
    assert "Situación:" not in desc
    assert "Resumen conciso." not in desc
    assert "análisis extendido" not in desc
    print(f"[PASS] No profile defaults ({len(desc)} chars): {desc[:80]}...")


if __name__ == "__main__":
    test_fallback_profile_a_short()
    test_fallback_profile_b_rich()
    test_profiles_are_different()
    test_no_profile_defaults()
    print("\n✅ Todos los tests de fallback adaptativo pasaron.")

