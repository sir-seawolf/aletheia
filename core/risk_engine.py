"""Regulador de comportamiento del sistema."""

from typing import Dict, Any
from config import DOMAIN_RISK_MAP, RISK_RULES


def get_risk_config(domain: str) -> Dict[str, Any]:
    """
    Clasifica el riesgo de un dominio y devuelve configuración estructurada.

    Args:
        domain: Dominio de la consulta (ej: "finanzas", "carrera")

    Returns:
        Dict con level, require_scenarios, allow_creativity, min_evidence, require_guardian
    """
    level = DOMAIN_RISK_MAP.get(domain, "low")
    rules = RISK_RULES.get(level, RISK_RULES["low"])

    return {
        "level": level,
        **rules,
    }

