"""
Guardian — adaptive validation layer for the v1 cognitive pipeline.

Responsibility: final validation rules, block risky outputs, schema enforcement,
confidence adjustment.
"""

from typing import Any, Dict, Optional

from core.schemas.decision_contract import DecisionReport


def validate(
    simulation: Dict[str, Any],
    policy: Optional[Dict[str, Any]] = None,
    drift_details: Optional[dict] = None,
    metrics: Optional[dict] = None,
) -> Dict[str, Any]:
    from core.guardian.adaptive_policy import resolve_guardian_sensitivity, build_guardian_config

    sensitivity = resolve_guardian_sensitivity(
        drift_details or {}, metrics or {}, simulation.get("domain", "")
    )
    build_guardian_config(sensitivity)  # side-effects only (logging/metrics)

    strict_mode          = policy.get("guardian_strict", True) if policy else True
    issues:  list[str]  = []
    scenarios            = simulation.get("scenarios", [])
    assumptions          = simulation.get("assumptions", [])
    risks                = simulation.get("risks", [])
    exploration_conf     = simulation.get("exploration_confidence", 0.5)
    llm_insight          = simulation.get("llm_insight", {}) or {}
    if isinstance(llm_insight, str):
        llm_insight = {"insight": llm_insight}

    if len(scenarios) < 2:
        issues.append("Falta comparacion de escenarios en riesgo alto")
    if not assumptions:
        issues.append("No hay supuestos explicitos")
    if not risks:
        issues.append("RIESGO ALTO: Debe identificar riesgos explicitos")
    if exploration_conf < 0.5:
        issues.append("BASE FACTUAL INSUFICIENTE: Confianza exploracion < 0.5")
    if len(llm_insight.get("insight", "")) < 30:
        issues.append("INSIGHT POCO DESARROLLADO: Analisis estrategico insuficiente")
    if llm_insight.get("recommendation_bias", "") == "aggressive":
        issues.append("CONTRADICCION: Bias aggressive detectado")

    if not strict_mode and len(issues) == 1:
        issues = []

    try:
        known   = set(DecisionReport.model_fields.keys()) if hasattr(DecisionReport, "model_fields") else set(DecisionReport.__fields__.keys())
        filtered = {k: v for k, v in simulation.items() if k in known}
        report   = DecisionReport(**filtered)
        corrected = report.model_dump(mode="json")
        for k, v in simulation.items():
            if k not in corrected:
                corrected[k] = v
    except ValueError as exc:
        issues.append(f"SCHEMA ERROR: {exc}")
        corrected = simulation.copy()

    corrected["guardian_block"]             = len(issues) > 0
    corrected["guardian_severity"]          = "high" if corrected["guardian_block"] else ("low" if issues else "none")
    corrected["guardian_confidence_adjust"] = max(0.10, 0.90 - len(issues) * 0.15)
    corrected["guardian_recommendation"]   = "Requiere validacion humana" if corrected["guardian_block"] else "Proceder"

    return {
        "valid":            len(issues) == 0,
        "block":            corrected["guardian_block"],
        "severity":         corrected["guardian_severity"],
        "issues":           issues,
        "confidence_adjust": corrected["guardian_confidence_adjust"],
        "recommendation":   corrected["guardian_recommendation"],
        "guardian_trace":   {"rules_triggered": issues, "severity": corrected["guardian_severity"]},
        "corrected_output": corrected,
    }
