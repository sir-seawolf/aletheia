"""El corazón del sistema. Genera escenarios, explica supuestos, compara opciones."""

from typing import Dict, Any
from core.context import Context


def run(context: Context, exploration: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera escenarios basados en el contexto y la exploración.

    Args:
        context: Contexto completo de la solicitud
        exploration: Resultado del agente explorer

    Returns:
        Estructura con scenarios, risks y assumptions
    """
    risk_config = context.risk
    facts = exploration.get("facts", [])
    gaps = exploration.get("gaps", [])

    # Determinar qué escenarios generar según riesgo
    scenarios = _generate_scenarios(context, facts, risk_config)
    assumptions = _build_assumptions(facts, gaps)
    risks = _identify_risks(context, scenarios)

    return {
        "scenarios": scenarios,
        "risks": risks,
        "assumptions": assumptions,
    }


def _generate_scenarios(
    context: Context, facts: list, risk_config: Dict[str, Any]
) -> list:
    """Genera escenarios según el nivel de riesgo."""
    scenarios = []

    if risk_config.get("require_scenarios", False):
        scenarios.append({
            "type": "conservative",
            "description": _build_scenario_description(context, facts, "conservative"),
        })
        scenarios.append({
            "type": "optimistic",
            "description": _build_scenario_description(context, facts, "optimistic"),
        })
    else:
        scenarios.append({
            "type": "exploratory",
            "description": _build_scenario_description(context, facts, "exploratory"),
        })

    return scenarios


def _build_scenario_description(context: Context, facts: list, scenario_type: str) -> str:
    """Construye descripción de escenario (MVP: placeholder estructurado)."""
    base = f"Escenario {scenario_type} para: {context.question}"
    if facts:
        base += f" | Basado en {len(facts)} hechos"
    return base


def _build_assumptions(facts: list, gaps: list) -> list:
    """Construye lista de supuestos explícitos."""
    assumptions = []

    if not facts:
        assumptions.append("No hay datos de memoria disponibles")
    else:
        assumptions.append(f"Se asume que los {len(facts)} hechos son precisos y actuales")

    for gap in gaps:
        assumptions.append(f"Se opera sin: {gap}")

    return assumptions


def _identify_risks(context: Context, scenarios: list) -> list:
    """Identifica riesgos basados en el contexto."""
    risks = []

    if context.risk.get("level") == "high":
        risks.append("Decisión de alto impacto: recomendable validar con asesoramiento humano")

    if len(scenarios) < 2:
        risks.append("Análisis unilateral: falta comparación de escenarios")

    return risks

