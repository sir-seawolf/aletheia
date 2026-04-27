"""
Config package - exposes all vars for import config.*
"""
# Direct from config.py
DOMAIN_RISK_MAP = {
    "finanzas": "high",
    "carrera": "high",
    "tecnologia": "medium",
    "objetivos": "medium",
    "salud": "high",
    "relaciones": "medium",
    "aprendizaje": "low",
    "creatividad": "low",
}

RISK_RULES = {
    "high": {
        "require_scenarios": True,
        "allow_creativity": False,
        "min_evidence": 2,
        "require_guardian": True,
    },
    "medium": {
        "require_scenarios": True,
        "allow_creativity": True,
        "min_evidence": 1,
        "require_guardian": True,
    },
    "low": {
        "require_scenarios": False,
        "allow_creativity": True,
        "min_evidence": 0,
        "require_guardian": False,
    },
}

MODEL = "llama3"
TEMPERATURE = 0.7
MEMORY_DB_PATH = "memory/data/aletheia.db"

from .modes import MODES, get_mode

