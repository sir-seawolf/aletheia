"""El corazón del sistema. Genera escenarios, explica supuestos, compara opciones."""

import json
from typing import Dict, Any
from core.context import Context
from ai.ollama_client import generate
from ai.prompts import simulation_prompt


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

    # Intentar generación con IA; fallback a lógica estructurada
    ai_result = _try_generate_with_ai(context, exploration)
    if ai_result:
        return ai_result

    # Fallback: lógica estructurada original
    scenarios = _generate_scenarios(context, facts, risk_config)
    assumptions = _build_assumptions(facts, gaps)
    risks = _identify_risks(context, scenarios)

    return {
        "scenarios": scenarios,
        "risks": risks,
        "assumptions": assumptions,
    }


def _try_generate_with_ai(context: Context, exploration: Dict[str, Any]) -> Dict[str, Any] | None:
    """Intenta generar escenarios usando Ollama. Devuelve None si falla."""
    try:
        prompt = simulation_prompt(context.to_dict(), exploration)
        temperature = 0.3 if not context.risk.get("allow_creativity", True) else 0.7
        response = generate(prompt, temperature=temperature)

        if response.startswith("[ERROR]"):
            return None

        # Limpiar posible markdown
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        data = json.loads(cleaned)

        # Normalizar escenarios
        for s in data.get("scenarios", []):
            s.setdefault("confidence", 0.5)
            s.setdefault("time_horizon", "no especificado")

        return {
            "scenarios": data.get("scenarios", []),
            "risks": data.get("risks", []),
            "assumptions": data.get("assumptions", []),
        }
    except Exception:
        return None


def _generate_scenarios(
    context: Context, facts: list, risk_config: Dict[str, Any]
) -> list:
    """Genera escenarios según el nivel de riesgo (fallback estructurado)."""
    scenarios = []

    if risk_config.get("require_scenarios", False):
        scenarios.append({
            "type": "conservative",
            "description": _build_scenario_description(context, facts, "conservative"),
            "confidence": 0.6,
            "time_horizon": "9 meses",
        })
        scenarios.append({
            "type": "optimistic",
            "description": _build_scenario_description(context, facts, "optimistic"),
            "confidence": 0.5,
            "time_horizon": "9 meses",
        })
    else:
        scenarios.append({
            "type": "exploratory",
            "description": _build_scenario_description(context, facts, "exploratory"),
            "confidence": 0.5,
            "time_horizon": "no especificado",
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
        risks.append(f"Decisión de alto impacto en dominio {context.domain}: recomendable validar con asesoramiento humano")

    if len(scenarios) < 2:
        risks.append("Análisis unilateral: falta comparación de escenarios")

    return risks

