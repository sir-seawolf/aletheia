"""Configuración central de Aletheia."""

# Modelo de IA local
MODEL = "llama3"

# Temperatura por defecto para generación
TEMPERATURE = 0.7

# Flag para integración cloud (futuro)
USE_CLOUD = False

# Configuración de memoria
MEMORY_DB_PATH = "memory/data/aletheia.db"

# Dominios reconocidos con sus niveles de riesgo base
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

# Reglas de riesgo por nivel
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

