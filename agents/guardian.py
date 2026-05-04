"""
Guardian Agent - Adaptive validation layer with DecisionReport schema enforcement.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: core.schemas.decision_contract, core.guardian.adaptive_policy
Last stable version: v1.1

Responsibility: Final validation rules, block risky outputs, confidence adjustment.
"""

from typing import Dict, Any

from core.schemas.decision_contract import DecisionReport

def validate(simulation: Dict[str, Any], policy: Dict[str, Any] = None, drift_details: dict = None, metrics: dict = None) -> Dict[str, Any]:
    """
    Adaptive guardian validation with strictness policy.

    Args:
        simulation (dict): Simulator DecisionReport input
        policy (dict, optional): ACO/guardian policy
        drift_details (dict, optional): Drift metrics
        metrics (dict, optional): System metrics

    Returns:
        dict: {'valid': bool, 'block': bool, 'issues': list, 'corrected_output': dict}
    """
    from core.guardian.adaptive_policy import resolve_guardian_sensitivity, build_guardian_config
    
    sensitivity = resolve_guardian_sensitivity(drift_details or {}, metrics or {}, simulation.get("domain", ""))
    config = build_guardian_config(sensitivity)

    strict_mode = policy.get("guardian_strict", True) if policy else True
    issues = []
    scenarios = simulation.get("scenarios", [])
    assumptions = simulation.get("assumptions", [])
    risks = simulation.get("risks", [])
    exploration_confidence = simulation.get("exploration_confidence", 0.5)
    llm_insight = simulation.get("llm_insight", {}) or {}
    if isinstance(llm_insight, str):
        llm_insight = {"insight": llm_insight}

    # Regla 1: Alto riesgo requiere >=2 escenarios
    if len(scenarios) < 2:
        issues.append("Falta comparacion de escenarios en riesgo alto")

    # Regla 2: Supuestos explicitos requeridos
    if not assumptions:
        issues.append("No hay supuestos explicitos")

    # Regla 3: Riesgo alto requiere riesgos identificados
    if not risks:
        issues.append("RIESGO ALTO: Debe identificar riesgos explicitos")

    # Regla 4: Baja evidencia factual
    if exploration_confidence < 0.5:
        issues.append("BASE FACTUAL INSUFICIENTE: Confianza exploracion < 0.5")

    # Regla 5: Insight debil
    insight_text = llm_insight.get("insight", "")
    if len(insight_text) < 30:
        issues.append("INSIGHT POCO DESARROLLADO: Analisis estrategico insuficiente")

    # Regla 6: Contradiccion insight-risk
    if llm_insight.get("recommendation_bias", "") == "aggressive":
        issues.append("CONTRADICCION: Bias aggressive detectado")

    # Strict mode
    if not strict_mode and len(issues) == 1:
        issues = []  # Minor issue allowed

    # Schema validation — filter extra fields before strict Pydantic check
    try:
        known = set(DecisionReport.model_fields.keys()) if hasattr(DecisionReport, 'model_fields') else set(DecisionReport.__fields__.keys())
        filtered = {k: v for k, v in simulation.items() if k in known}
        report = DecisionReport(**filtered)
        corrected_output = report.model_dump()
        # Restore non-schema fields (exploration_confidence, llm_calls, user_profile_str, etc.)
        for k, v in simulation.items():
            if k not in corrected_output:
                corrected_output[k] = v
    except ValueError as e:
        issues.append(f"SCHEMA ERROR: {str(e)}")
        corrected_output = simulation.copy()

    corrected_output["guardian_block"] = len(issues) > 0
    corrected_output["guardian_severity"] = "high" if corrected_output["guardian_block"] else "low" if issues else "none"
    corrected_output["guardian_confidence_adjust"] = 0.8 ** len(issues)
    corrected_output["guardian_recommendation"] = "Requiere validacion humana" if corrected_output["guardian_block"] else "Proceder"

    result = {
        "valid": len(issues) == 0,
        "block": corrected_output["guardian_block"],
        "severity": corrected_output["guardian_severity"],
        "issues": issues,
        "confidence_adjust": corrected_output["guardian_confidence_adjust"],
        "recommendation": corrected_output["guardian_recommendation"],
        "guardian_trace": {
            "rules_triggered": issues,
            "severity": corrected_output["guardian_severity"]
        },
        "corrected_output": corrected_output,
    }

    return result

