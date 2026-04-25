"""El corazón del sistema. Genera escenarios, explica supuestos, compara opciones."""

import json
from typing import Dict, Any
from core.context import Context
from core.event_bus import build_event, emit_event
from ai.ollama_client import generate
from ai.prompts import simulation_prompt


def run(context: Context, exploration: Dict[str, Any], session_id: str = "local") -> Dict[str, Any]:
    """
    Genera escenarios basados en el contexto y la exploración.

    Args:
        context: Contexto completo de la solicitud
        exploration: Resultado del agente explorer

    Returns:
        Estructura con scenarios, risks y assumptions
    """
    emit_event(
        build_event(
            session_id=session_id,
            agent="simulator",
            stage="thinking",
            event_type="generating_scenarios",
            payload={"domain": context.domain},
            confidence=0.0,
        )
    )

    risk_config = context.risk
    facts = exploration.get("facts", [])
    gaps = exploration.get("gaps", [])

    # Adaptar temperatura según perfil cognitivo
    base_temperature = 0.3 if not risk_config.get("allow_creativity", True) else 0.7
    if context.user_profile and context.user_profile.abstraction_capacity == "alta":
        base_temperature = min(base_temperature + 0.1, 1.0)

    # Intentar generación con IA; fallback a lógica estructurada
    ai_result = _try_generate_with_ai(context, exploration, temperature=base_temperature)
    if ai_result:
        emit_event(
            build_event(
                session_id=session_id,
                agent="simulator",
                stage="done",
                event_type="scenarios_generated",
                payload={"scenarios": ai_result.get("scenarios", [])},
                confidence=0.7,
            )
        )
        return ai_result

    # Fallback: lógica estructurada original
    scenarios = _generate_scenarios(context, facts, risk_config)
    assumptions = _build_assumptions(facts, gaps)
    risks = _identify_risks(context, scenarios)

    result = {
        "scenarios": scenarios,
        "risks": risks,
        "assumptions": assumptions,
    }

    emit_event(
        build_event(
            session_id=session_id,
            agent="simulator",
            stage="done",
            event_type="scenarios_generated",
            payload={"scenarios": scenarios},
            confidence=0.6,
        )
    )

    return result


def _try_generate_with_ai(context: Context, exploration: Dict[str, Any], temperature: float | None = None) -> Dict[str, Any] | None:
    """Intenta generar escenarios usando Ollama. Devuelve None si falla."""
    try:
        prompt = simulation_prompt(context.to_dict(), exploration)
        if temperature is None:
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
    """Construye descripción de escenario usando Ollama con fallback adaptativo al perfil."""
    # 1. Intento con IA primero
    try:
        from ai.prompts import scenario_description_prompt
        from ai.ollama_client import generate

        prompt = scenario_description_prompt(
            question=context.question,
            facts=facts,
            scenario_type=scenario_type,
            profile=context.user_profile,
        )
        temperature = 0.3 if not context.risk.get("allow_creativity", True) else 0.7
        response = generate(prompt, temperature=temperature)

        if response and not response.startswith("[ERROR]"):
            return response.strip()
    except Exception:
        pass

    # 2. Fallback adaptativo al perfil cognitivo (sin IA)
    profile = context.user_profile
    structure = getattr(profile, "structure_preference", "sistémica") if profile else "sistémica"
    verbosity = getattr(profile, "verbosity_preference", "media") if profile else "media"

    if structure == "narrativa":
        description = (
            f"Escenario {scenario_type}:\n\n"
            f"Situación:\n{context.question}\n\n"
            f"Interpretación:\n"
            f"Basado en los datos disponibles, este escenario considera "
        )
        if facts:
            description += f"{len(facts)} hechos relevantes. "
        else:
            description += "la situación actual sin datos adicionales. "
        description += (
            f"\n\nImplicaciones:\n"
            f"Las consecuencias de este escenario dependen de cómo evolucionen las condiciones."
        )
    else:
        # Estructura sistémica (por defecto)
        description = f"Escenario {scenario_type} para: {context.question}"
        if facts:
            description += f" | Basado en {len(facts)} hechos"

    # Ajuste de densidad
    if verbosity == "alta":
        description += (
            " Se desarrollan más detalles y posibles implicaciones. "
            "Incluye análisis extendido de variables clave, escenarios secundarios "
            "y recomendaciones de contingencia."
        )
    elif verbosity == "baja":
        description += " Resumen conciso."

    return description.strip()


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

