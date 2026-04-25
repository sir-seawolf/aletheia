"""Prompts especializados por función para Aletheia."""

import json
from typing import Dict, Any


def exploration_prompt(context: Dict[str, Any]) -> str:
    """
    Prompt para el agente Explorer.
    Extrae hechos relevantes de la memoria.
    """
    return f"""Eres un analista frío y preciso. Tu trabajo es extraer hechos relevantes.

Dominio: {context.get('domain', 'general')}
Pregunta: {context.get('question', '')}
Memoria disponible: {context.get('memory', [])}

Instrucciones:
1. Identifica los hechos más relevantes para la pregunta
2. Señala qué información falta
3. No interpretes, no opines, solo reporta

Responde ÚNICAMENTE en formato JSON válido, sin markdown ni explicaciones adicionales:
{{"facts": ["hecho 1", "hecho 2"], "gaps": ["información faltante"], "confidence": 0.8}}
"""


def simulation_prompt(context: Dict[str, Any], exploration: Dict[str, Any]) -> str:
    """
    Prompt para el agente Simulator.
    Genera escenarios y análisis.
    """
    risk_level = context.get('risk', {}).get('level', 'low')
    require_scenarios = context.get('risk', {}).get('require_scenarios', False)

    scenario_instruction = (
        "Genera al menos 2 escenarios: conservador y optimista."
        if require_scenarios
        else "Genera un análisis exploratorio con un único escenario."
    )

    return f"""Eres un simulador estratégico. Tu trabajo es generar escenarios futuros.

Dominio: {context.get('domain', 'general')}
Pregunta: {context.get('question', '')}
Hechos conocidos: {exploration.get('facts', [])}
Vacíos de información: {exploration.get('gaps', [])}
Nivel de riesgo: {risk_level}

Instrucciones:
1. {scenario_instruction}
2. Para cada escenario, incluye: descripción detallada, confidence (0.0 a 1.0) y time_horizon (ej: "3 meses", "1 año")
3. Lista los supuestos explícitos que haces
4. Identifica riesgos clave
5. No des una sola respuesta, explora posibilidades

Responde ÚNICAMENTE en formato JSON válido, sin markdown ni explicaciones adicionales:
{{"scenarios": [{{"type": "conservative", "description": "...", "confidence": 0.6, "time_horizon": "9 meses"}}], "risks": ["riesgo 1"], "assumptions": ["supuesto 1"]}}
"""


def scenario_description_prompt(question: str, facts: list, scenario_type: str) -> str:
    """
    Prompt para generar la descripción de un escenario específico usando Ollama.
    """
    return f"""Dado este contexto:
- Pregunta: {question}
- Hechos: {facts}

Genera un escenario {scenario_type} realista.
Incluye:
- evolución probable
- riesgos
- condiciones necesarias

Responde con un párrafo conciso y directo, sin markdown ni explicaciones adicionales.
"""


def validation_prompt(simulation: Dict[str, Any], risk_config: Dict[str, Any]) -> str:
    """
    Prompt para el agente Guardian.
    Valida la calidad del output.
    """
    return f"""Eres un auditor de calidad. Tu trabajo es validar si un análisis es sólido.

Nivel de riesgo: {risk_config.get('level', 'low')}
Requiere múltiples escenarios: {risk_config.get('require_scenarios', False)}
Mínimo de evidencia: {risk_config.get('min_evidence', 0)}

Análisis a validar:
{json.dumps(simulation, indent=2, ensure_ascii=False)}

Instrucciones:
1. Verifica si cumple las reglas de calidad
2. Señala problemas específicos
3. Si es válido, confirma. Si no, indica qué falta

Responde ÚNICAMENTE en formato JSON válido, sin markdown ni explicaciones adicionales:
{{"valid": true, "issues": [], "corrected_output": {{...}}}}
"""

