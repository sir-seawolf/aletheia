"""Adaptive Guardian Policies - Sensitivity based on drift."""

SENSITIVITY_CONFIGS = {
    "normal": {
        "min_confidence": 0.3,
        "min_scenarios": 2,
        "min_insight_len": 30,
        "require_explicit_risks": False
    },
    "medium": {
        "min_confidence": 0.4,
        "min_scenarios": 2,
        "min_insight_len": 50,
        "require_explicit_risks": True
    },
    "high": {
        "min_confidence": 0.5,
        "min_scenarios": 3,
        "min_insight_len": 80,
        "require_explicit_risks": True
    }
}

def resolve_guardian_sensitivity(drift_details: dict, metrics: dict, domain: str) -> str:
    "Resolve sensitivity from drift and context."
    if drift_details.get("degradation") or drift_details.get("instability"):
        return "high"
    if drift_details.get("false_stability"):
        return "medium"
    if domain in ["finanzas", "salud", "legal"]:
        return "medium"
    return "normal"

def build_guardian_config(sensitivity: str) -> dict:
    "Build config from sensitivity."
    return SENSITIVITY_CONFIGS.get(sensitivity, SENSITIVITY_CONFIGS["normal"])

