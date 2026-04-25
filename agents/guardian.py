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
    scenarios = simulation.get("scenarios", [])
    assumptions = simulation.get("assumptions", [])
    risks = simulation.get("risks", [])

    # Regla 1: En riesgo alto, debe haber comparación de escenarios
    if risk_config.get("level") == "high" and len(scenarios) < 2:
        issues.append("Falta comparación de escenarios en riesgo alto")

    # Regla 2: Debe haber supuestos explícitos
    if not assumptions:
        issues.append("No hay supuestos explícitos")

    # Regla 3: En riesgo alto, debe haber riesgos identificados
    if risk_config.get("level") == "high" and not risks:
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

