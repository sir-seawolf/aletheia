"""Control de calidad. Valida outputs, aplica reglas de riesgo, bloquea respuestas pobres."""

from typing import Dict, Any


def validate(simulation: Dict[str, Any], risk_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida el output del simulador contra las reglas de riesgo.

    Args:
        simulation: Resultado del agente simulator
        risk_config: Configuración de riesgo del dominio

    Returns:
        Estructura con valid, issues y corrected_output
    """
    issues = []

    # Regla 1: En riesgo alto, debe haber múltiples escenarios
    if risk_config.get("require_scenarios", False):
        scenarios = simulation.get("scenarios", [])
        if len(scenarios) < 2:
            issues.append("RIESGO ALTO: Se requieren múltiples escenarios")

    # Regla 2: Debe haber supuestos explícitos
    assumptions = simulation.get("assumptions", [])
    if not assumptions:
        issues.append("Faltan supuestos explícitos")

    # Regla 3: En riesgo alto, debe haber riesgos identificados
    if risk_config.get("level") == "high":
        risks = simulation.get("risks", [])
        if not risks:
            issues.append("RIESGO ALTO: Debe identificar riesgos explícitos")

    # Construir output corregido
    corrected_output = simulation.copy()
    if issues:
        corrected_output["validation_issues"] = issues
        corrected_output["validated"] = False
    else:
        corrected_output["validated"] = True

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "corrected_output": corrected_output,
    }

