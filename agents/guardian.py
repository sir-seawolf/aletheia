"""Control de calidad. Valida outputs, aplica reglas de riesgo, bloquea respuestas pobres."""

from typing import Dict, Any
from core.event_bus import build_event, emit_event
from core.schemas.decision_contract import DecisionReport as DecisionReportSchema




) -> Dict[str, Any]:
    """
    Valida el output del simulador contra las reglas de riesgo.

    Args:
        simulation: Resultado del agente simulator
        risk_config: Configuración de riesgo del dominio

    Returns:
        Estructura con valid, issues y corrected_output
    """
    emit_event(
        build_event(
            session_id=session_id,
            agent="guardian",
            stage="thinking",
            event_type="risk_evaluation_started",
            payload={"risk_level": risk_config.get("level", "unknown")},
            confidence=0.0,
        )
    )

    issues = []
    scenarios = simulation.get("scenarios", [])
    assumptions = simulation.get("assumptions", [])
    risks = simulation.get("risks", [])
    exploration_confidence = simulation.get("exploration_confidence", 0.5)
    llm_insight = simulation.get("llm_insight", {})

    # Regla 1: En riesgo alto, debe haber comparación de escenarios
    if risk_config.get("level") == "high" and len(scenarios) < 2:
        issues.append("Falta comparación de escenarios en riesgo alto")

    # Regla 2: Debe haber supuestos explícitos
    if not assumptions:
        issues.append("No hay supuestos explícitos")

    # Regla 3: En riesgo alto, debe haber riesgos identificados
    if risk_config.get("level") == "high" and not risks:
        issues.append("RIESGO ALTO: Debe identificar riesgos explícitos")

    # Nueva Regla 4: Baja evidencia factual
    if exploration_confidence < 0.5:
        issues.append("BASE FACTUAL INSUFICIENTE: Confianza exploración < 0.5")

    # Nueva Regla 5: Insight débil
    insight_text = llm_insight.get("insight", "")
    if len(insight_text) < 50:
        issues.append("INSIGHT POCO DESARROLLADO: Análisis estratégico insuficiente")

    # Nueva Regla 6: Contradicción insight-risk
    if risk_config.get("level") == "high" and llm_insight.get("recommendation_bias", "") == "aggressive":
        issues.append("CONTRADICCIÓN: Riesgo alto pero bias aggressive")

    # Construir output corregido
    corrected_output = simulation.copy()
    if issues:
        corrected_output["validation_issues"] = issues
        corrected_output["validated"] = False
    else:
        corrected_output["validated"] = True

    num_issues = len(issues)
    block = num_issues > 1 or any("ALTO" in issue or "INSUFICIENTE" in issue for issue in issues)
    severity = "high" if block else "none" if num_issues == 0 else "low"
    confidence_adjust = 0.8 ** num_issues
    recommendation = "Requiere validación humana o más datos" if block else ("Proceder con precaución" if num_issues > 0 else "Validado")
    
    corrected_output["guardian_block"] = block
    corrected_output["guardian_severity"] = severity
    corrected_output["guardian_confidence_adjust"] = confidence_adjust
    corrected_output["guardian_recommendation"] = recommendation
    
    result = {
        "valid": num_issues == 0,
        "block": block,
        "severity": severity,
        "issues": issues,
        "confidence_adjust": confidence_adjust,
        "recommendation": recommendation,
        "corrected_output": corrected_output,
    }

    emit_event(
        build_event(
            session_id=session_id,
            agent="guardian",
            stage="done" if result["valid"] else "blocked",
            event_type="risk_evaluated",
            payload={
                "risk_level": risk_config.get("level", "unknown").upper(),
                "reasons": issues if issues else ["validación completada sin incidencias"],
            },
            confidence=0.9 if result["valid"] else 0.4,
        )
    )

    return result
