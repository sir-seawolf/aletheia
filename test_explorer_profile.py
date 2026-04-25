"""Test rápido: Explorer con perfiles cognitivos A y B."""

from types import SimpleNamespace
from agents.explorer import _extract_relevant_facts, _detect_gaps, _calculate_confidence

# Memoria de prueba con 12 items que coinciden con dominio/pregunta
MEMORY = [f"memory item {i} test domain" for i in range(12)]

PROFILE_A = SimpleNamespace(
    verbosity_preference="alta",
    cognitive_style="lineal",
)

PROFILE_B = SimpleNamespace(
    verbosity_preference="baja",
    cognitive_style="arborescente",
    abstraction_tolerance="alta",
)

RISK_LOW = {"min_evidence": 0, "level": "low"}


def test_extract_facts():
    """Profile A (alta) → más facts. Profile B (baja) → menos facts."""
    facts_a = _extract_relevant_facts(MEMORY, "test", "question test", PROFILE_A)
    facts_b = _extract_relevant_facts(MEMORY, "test", "question test", PROFILE_B)

    assert len(facts_a) == 10, f"Esperado 10 facts para A, obtenido {len(facts_a)}"
    assert len(facts_b) == 5, f"Esperado 5 facts para B, obtenido {len(facts_b)}"
    print(f"[PASS] facts: A={len(facts_a)}, B={len(facts_b)}")


def test_detect_gaps():
    """Profile A → gaps básicos (solo cantidad). Profile B → gap estructural por tolerancia alta + pocos facts."""
    many_facts = [f"fact {i} test" for i in range(5)]
    few_facts = [f"fact {i} test" for i in range(2)]

    gaps_b_many = _detect_gaps(many_facts, RISK_LOW, PROFILE_B)

    # Con muchos facts, B no debe generar gap estructural
    assert not any("profundidad estructural" in g for g in gaps_b_many)

    # Con pocos facts (<3), B sí debe generar gap estructural
    gaps_b_few = _detect_gaps(few_facts, RISK_LOW, PROFILE_B)
    assert any("profundidad estructural" in g for g in gaps_b_few), (
        f"Esperado gap estructural para B con pocos facts, obtenido {gaps_b_few}"
    )

    # A nunca genera gap estructural
    gaps_a_few = _detect_gaps(few_facts, RISK_LOW, PROFILE_A)
    assert not any("profundidad estructural" in g for g in gaps_a_few)

    print("[PASS] gaps: A=básicos, B=estructurales cuando <3 facts")


def test_calculate_confidence():
    """Profile B (arborescente) → confianza ligeramente más flexible (+0.05)."""
    facts = ["fact1", "fact2"]
    gaps = ["un gap"]

    conf_a = _calculate_confidence(facts, gaps, PROFILE_A)
    conf_b = _calculate_confidence(facts, gaps, PROFILE_B)

    expected_diff = 0.05
    actual_diff = round(conf_b - conf_a, 2)

    assert actual_diff == expected_diff, (
        f"Esperada diferencia de {expected_diff} en confianza, obtenida {actual_diff} (A={conf_a}, B={conf_b})"
    )
    print(f"[PASS] confidence: A={conf_a}, B={conf_b} (diff +{actual_diff})")


def test_structure_preference():
    """Ambos perfiles respetan orden natural por ahora (MVP)."""
    facts_a = _extract_relevant_facts(MEMORY, "test", "question test", PROFILE_A)
    facts_b = _extract_relevant_facts(MEMORY, "test", "question test", PROFILE_B)

    # En MVP ambos mantienen orden natural; solo cambia la cantidad
    assert facts_a == MEMORY[:10]
    assert facts_b == MEMORY[:5]
    print("[PASS] estructura: orden natural preservado para ambos perfiles")


if __name__ == "__main__":
    test_extract_facts()
    test_detect_gaps()
    test_calculate_confidence()
    test_structure_preference()
    print("\n✅ Todos los tests de perfil cognitivo pasaron.")

