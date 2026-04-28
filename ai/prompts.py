# DEPRECATED: Use core/llm/prompts.py
# Legacy prompts - migrate to central prompts in LLMRouter ecosystem
"""
Legacy prompts. All new code uses core.llm.prompts.
"""
pass

import json
from typing import Dict, Any, Optional, List
from memory.models import UserProfile


def _build_profile_instructions(profile: Optional[UserProfile]) -> str:
    """Construye las instrucciones de adaptación según el perfil cognitivo."""
    if not profile:
        return ""

    instructions = []

    # Control de densidad
    if profile.verbosity_preference == "baja":
        instructions.append("Máximo 3 líneas por escenario. Sé extremadamente conciso.")
    elif profile.verbosity_preference == "alta":
        instructions.append("Desarrolla cada escenario con el detalle necesario. Sé exhaustivo.")
    else:
        instructions.append("Desarrolla cada escenario con el detalle necesario.")

    # Control de estructura
    if profile.structure_preference == "sistémica":
        instructions.append("Usa listas, bullets y estructura jerárquica clara.")
    elif profile.structure_preference == "narrativa":
        instructions.append("Usa párrafos narrativos fluidos. Evita listas.")

    # Control de abstracción
    if profile.abstraction_capacity == "alta":
        instructions.append("Evita explicaciones básicas. Prioriza conceptos abstractos y modelos.")
    elif profile.abstraction_capacity == "baja":
        instructions.append("Explica paso a paso con ejemplos concretos.")

    return "\n".join(instructions)


def exploration_prompt(context: Dict[str, Any]) -> str:
    """
    Prompt para el agente Explorer.
    Extrae hechos relevantes de la memoria.
    """
    profile = context.get("user_profile")
    profile_instructions = _build_profile_instructions(profile)

    return f"""Eres un analista frío y preciso. Tu trabajo es extraer hechos relevantes.

Dominio: {context.get('domain', 'general')}
Pregunta: {context.get('question', '')}
Memoria disponible: {context.get('memory', [])}

Instrucciones:
1. Identifica los hechos más relevantes para la pregunta
2. Señala qué información falta
3. No interpretes, no opines, solo reporta
{profile_instructions}

Responde ÚNICAMENTE en formato JSON válido, sin markdown ni explicaciones adicionales:
{{"facts": ["hecho 1", "hecho 2"], "gaps": ["información faltante"], "confidence": 0.8}}
"""


def simulation_prompt(context: Dict[str, Any], exploration: Dict[str, Any], memory_bias: Dict[str, Any] = None) -> str:
    """
    Prompt para el agente Simulator (Sprint 2: memory-weighted).
    Genera escenarios influenciados por memoria histórica.
    """
    risk_level = context.get('risk', {}).get('level', 'low')
    require_scenarios = context.get('risk', {}).get('require_scenarios', False)
    profile = context.get("user_profile")
    profile_instructions = _build_profile_instructions(profile)

    scenario_instruction = (
        "Genera al menos 2 escenarios: conservador y optimista."
        if require_scenarios
        else "Genera un análisis exploratorio con un único escenario."
    )

    memory_section = ""
    if memory_bias:
        regulation = memory_bias.get("regulation", {})
        memory_section = f"""
INFLUENCIA DE MEMORIA HISTÓRICA:

{memory_bias["bias_summary"]}

REGULATION MODE: {regulation.get('mode', 'balanced')}
BIAS MULTIPLIER: {regulation.get('bias_multiplier', 1.0)}
{regulation.get('message', '')}

CASOS SIMILARES RECIENTES:
{json.dumps(memory_bias["influential_cases"], indent=2, ensure_ascii=False)}

Incorpora esta memoria regulada como sesgo estructural:
- Aplica MRE weights/decay
- Penaliza patrones que fallaron (high error/low weight)
- Sigue regulation mode
"""


    return f"""Eres un simulador estratégico. Tu trabajo es generar escenarios futuros {memory_section if memory_section else ''}

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
{profile_instructions}

Responde ÚNICAMENTE en formato JSON válido, sin markdown ni explicaciones adicionales:
{{"scenarios": [{{"type": "conservative", "description": "...", "confidence": 0.6, "time_horizon": "9 meses"}}], "risks": ["riesgo 1"], "assumptions": ["supuesto 1"]}}
"""


def scenario_description_prompt(question: str, facts: list, scenario_type: str, profile: Optional[UserProfile] = None) -> str:
    """
    Prompt para generar la descripción de un escenario específico usando Ollama.
    """
    profile_instructions = _build_profile_instructions(profile)

    return f"""Dado este contexto:
- Pregunta: {question}
- Hechos: {facts}

Genera un escenario {scenario_type} realista.
Incluye:
- evolución probable
- riesgos
- condiciones necesarias
{profile_instructions}

Responde con un párrafo conciso y directo, sin markdown ni explicaciones adicionales.
"""


def insight_prompt(context: Dict[str, Any], scenarios: List[Dict], risks: List[str], assumptions: List[str]) -> str:
    """Prompt para generar insight estratégico global."""
    profile_instructions = _build_profile_instructions(context.get("user_profile"))
    
    scenario_summary = "\n".join([f"- {s.get('type', 'unknown')}: {s.get('outcome', '')[:100]}..." for s in scenarios])
    
    return f"""Eres un analista estratégico senior. Tu trabajo es destilar el insight clave del análisis.

Pregunta: {context.get('question', '')}
Escenarios: {scenario_summary}
Riesgos: {', '.join(risks)}
Supuestos: {', '.join(assumptions)}

No resumas. Identifica:
1. Tensión principal de la decisión
2. Variable crítica que lo determina todo
3. Riesgo oculto no mencionado
4. Recomendación estratégica (bias: conservative/exploratory/aggressive)

{profile_instructions}

JSON:
{{"insight": "lectura corta penetrante", "key_variable": "la variable", "decision_tension": "la tensión", "recommendation_bias": "conservative"}}"""

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

