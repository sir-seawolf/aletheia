"""El corazón del sistema. Genera escenarios, explica supuestos, compara opciones."""

import json
from typing import Dict, Any, List, Optional
from core.context import Context
from core.event_bus import build_event, emit_event
from ai.ollama_client import generate
from ai.prompts import simulation_prompt
from core.models import DecisionReport
from datetime import datetime, timezone
from .simulator_helpers import _build_decision_report_from_ai, _calculate_overall_confidence, _generate_llm_insight

def run(context: Context, exploration: Dict[str, Any], session_id: str = "local") -> Dict[str, Any]:
    """
    Pipeline: IA or fallback → insight → DecisionReport.
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

    base_temperature = 0.3 if not risk_config.get("allow_creativity", True) else 0.7
    if context.user_profile and context.user_profile.abstraction_capacity == "alta":
        base_temperature = min(base_temperature + 0.1, 1.0)

    # IA first with memory influence (Sprint 2)
    ai_result = _try_generate_with_ai(context, exploration, base_temperature)
    if not ai_result:
        # Fallback
        assumptions = _build_assumptions(facts, gaps)
        scenarios = _generate_scenarios(context, facts, gaps, risk_config)
        risks = _identify_risks(context, scenarios)
        ai_result = {"scenarios": scenarios, "risks": risks, "assumptions": assumptions}

    insight = _generate_llm_insight(context, ai_result["scenarios"], ai_result["risks"], ai_result["assumptions"])

    emit_event(
        build_event(
            session_id=session_id,
            agent="simulator",
            stage="done",
            event_type="scenarios_generated",
            payload={"scenarios_count": len(ai_result["scenarios"])},
            confidence=0.7,
        )
    )

    return _build_decision_report_from_ai(context, exploration, ai_result, session_id, insight)

def _try_generate_with_ai(context: Context, exploration: Dict[str, Any], temperature: float) -> Optional[Dict[str, Any]]:
    """IA scenarios."""
    try:
        prompt = simulation_prompt(context.to_dict(), exploration)
        response = generate(prompt, temperature=temperature)
        if response.startswith("[ERROR]"):
            return None

        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            cleaned = "\n".join(lines[1:-1]).strip() if len(lines) > 2 else cleaned

        data = json.loads(cleaned)
        if "scenarios" not in data:
            return None

        global_assumptions = data.get("assumptions", [])
        normalized_scenarios = [
            _normalize_scenario(s, "exploratory", "0-12 meses", global_assumptions)
            for s in data.get("scenarios", [])
        ]
        return {
            "scenarios": normalized_scenarios,
            "risks": data.get("risks", []),
            "assumptions": global_assumptions,
        }
    except:
        return None

def _build_assumptions(facts: List[str], gaps: List[str]) -> List[str]:
    assumptions = []
    if not facts:
        assumptions.append("No hay datos de memoria disponibles")
    else:
        assumptions.append(f"Se asume que los {len(facts)} hechos son precisos y actuales")
    for gap in gaps:
        assumptions.append(f"Se opera sin: {gap}")
    return assumptions

def _generate_scenarios(context: Context, facts: List[str], gaps: List[str], risk_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scenarios = []
    financial_vars = _infer_financial_variables(facts)
    if risk_config.get("require_scenarios", False):
        scenarios.append(_normalize_scenario({
            "type": "conservative",
            "timeline": "0-12 meses",
            "variables": {"ingresos": financial_vars.get("ingresos", "estable"), "gastos": financial_vars.get("gastos_conservative", "+10%")},
            "outcome": _build_scenario_description(context, facts, "conservative"),
        }, "conservative", "0-12 meses", _build_assumptions(facts, gaps)))
        scenarios.append(_normalize_scenario({
            "type": "optimistic",
            "timeline": "0-12 meses",
            "variables": {"ingresos": financial_vars.get("ingresos", "estable"), "gastos": financial_vars.get("gastos_optimistic", "-15%")},
            "outcome": _build_scenario_description(context, facts, "optimistic"),
        }, "optimistic", "0-12 meses", _build_assumptions(facts, gaps)))
    else:
        scenarios.append(_normalize_scenario({
            "type": "exploratory",
            "timeline": "0-12 meses",
            "variables": {"ingresos": financial_vars.get("ingresos", "variable"), "gastos": financial_vars.get("gastos", "variable")},
            "outcome": _build_scenario_description(context, facts, "exploratory"),
        }, "exploratory", "0-12 meses", _build_assumptions(facts, gaps)))
    return scenarios

def _identify_risks(context: Context, scenarios: List[Dict[str, Any]]) -> List[str]:
    risks = []
    if context.risk.get("level") == "high":
        risks.append(f"Decisión de alto impacto en dominio {context.domain}: recomendable validar con asesoramiento humano")
    if len(scenarios) < 2:
        risks.append("Análisis unilateral: falta comparación de escenarios")
    return risks

def _normalize_scenario(scenario: Dict[str, Any], default_type: str, default_timeline: str, default_assumptions: List[str]) -> Dict[str, Any]:
    scenario_type = scenario.get("type", default_type)
    timeline = scenario.get("timeline") or default_timeline
    assumptions = scenario.get("assumptions", default_assumptions)
    variables = scenario.get("variables", {})
    outcome = scenario.get("outcome") or scenario.get("description", "Sin outcome especificado")
    confidence = float(scenario.get("confidence", 0.5))
    return {
        "type": scenario_type,
        "timeline": timeline,
        "assumptions": assumptions,
        "variables": variables,
        "outcome": outcome,
        "confidence": confidence,
        "description": outcome,
        "time_horizon": timeline,
    }

def _infer_financial_variables(facts: List[str]) -> Dict[str, str]:
    text = " ".join(facts).lower()
    has_ingresos = any(k in text for k in ["ingreso", "salario", "nómina", "nomina"])
    has_gastos = any(k in text for k in ["gasto", "coste", "costo"])
    return {
        "ingresos": "estable" if has_ingresos else "incierto",
        "gastos": "estable" if has_gastos else "incierto",
        "gastos_conservative": "+10%",
        "gastos_optimistic": "-15%",
    }

def _build_scenario_description(context: Context, facts: list, scenario_type: str) -> str:
    """Ollama fallback."""
    try:
        from ai.prompts import scenario_description_prompt
        prompt = scenario_description_prompt(context.question, facts, scenario_type, context.user_profile)
        temperature = 0.3 if not context.risk.get("allow_creativity", True) else 0.7
        response = generate(prompt, temperature=temperature)
        if response and not response.startswith("[ERROR]"):
            return response.strip()
    except:
        pass
    # Fallback text
    profile = context.user_profile or MagicMock()
    structure = getattr(profile, "structure_preference", "sistémica")
    verbosity = getattr(profile, "verbosity_preference", "media")
    description = f"Escenario {scenario_type} para: {context.question}"
    if facts:
        description += f" | Basado en {len(facts)} hechos"
    if verbosity == "alta":
        description += " Análisis extendido recomendado."
    elif verbosity == "baja":
        description += " Resumen."
    return description.strip()

