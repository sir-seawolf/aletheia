"""
Legacy prompts module - DEPRECATED.

STATUS: PLACEHOLDER (legacy v1, migrate to core/llm/prompts.py)
Dependencies: memory.models.UserProfile
Last stable version: v1.0 (superseded)

Contains profile-adaptive prompt builders for exploration/simulation.
Each func injects: profile fields (verbosity_preference, structure_preference, abstraction_capacity), 
target models (llama3/phi3), ~200-800 token length.

TODO: IMPLEMENT migration to central LLMRouter prompt system.
"""

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
    Extrae hechos concretos de la pregunta e inyecta contexto del perfil del usuario.
    """
    profile_str = context.get("user_profile_str", "")
    profile_section = f"\n\n{profile_str}" if profile_str else ""

    return f"""Eres un analista de decisiones personales. Analiza la siguiente pregunta y extrae los datos clave.

Dominio: {context.get('domain', 'general')}
Pregunta: {context.get('question', '')}{profile_section}

Tu tarea:
1. Extrae los hechos concretos que están en la pregunta o en los datos del usuario (números, cifras, situaciones específicas).
2. Identifica qué información falta para poder responder con precisión.
3. Estima tu confianza en los datos disponibles (0.0 a 1.0).

Responde SOLO con este JSON (sin markdown, sin texto antes ni después):
{{"facts": ["hecho 1", "hecho 2"], "gaps": ["dato faltante 1"], "confidence": 0.7}}"""


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


    profile_str = context.get("user_profile_str", "")
    profile_section = f"\n{profile_str}" if profile_str else ""

    return f"""Eres un simulador estratégico de decisiones personales. Tu trabajo es generar escenarios futuros realistas. {memory_section if memory_section else ''}

Dominio: {context.get('domain', 'general')}
Pregunta: {context.get('question', '')}
Hechos conocidos: {exploration.get('facts', [])}
Vacíos de información: {exploration.get('gaps', [])}
Nivel de riesgo: {risk_level}{profile_section}

Instrucciones:
1. {scenario_instruction}
2. Para cada escenario, incluye: descripción detallada, confidence (0.0 a 1.0) y time_horizon (ej: "3 meses", "1 año")
3. Lista los supuestos explícitos que haces
4. Identifica riesgos clave
5. No des una sola respuesta, explora posibilidades
{profile_instructions}

Responde ÚNICAMENTE en formato JSON válido, sin markdown ni explicaciones adicionales:
{{"scenarios": [{{"type": "optimista", "description": "descripción del escenario", "probability": 0.60, "outcome": "positivo", "time_horizon": "9 meses"}}, {{"type": "conservador", "description": "descripción del escenario", "probability": 0.30, "outcome": "neutral", "time_horizon": "9 meses"}}], "risks": ["riesgo 1"], "assumptions": ["supuesto 1"]}}
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


def _is_decision_question(question: str) -> bool:
    """Heuristic: does this question require a decision analysis?"""
    import re
    decision_patterns = re.compile(
        r"\b(debería|debo|deberia|conviene|vale la pena|merece la pena|"
        r"comprar|compro|vender|vendo|invertir|invierto|"
        r"cambiar|cambio|dejar|dejo|aceptar|acepto|rechazar|rechazo|"
        r"contratar|contrато|despedir|mudarse|arriesgar|"
        r"alquilar|alquilo|hipoteca|pedir prestado|"
        r"should i|is it worth|buy|sell|invest|change|accept|reject|"
        r"riesgo de|riesgos de|análisis de|analizar)\b",
        re.IGNORECASE,
    )
    return bool(decision_patterns.search(question)) or (len(question) > 60 and "?" in question)


def insight_prompt(context: Dict[str, Any], scenarios: List[Dict], risks: List[str], assumptions: List[str]) -> str:
    """Prompt para generar insight. Adaptativo: analítico para decisiones, conversacional para el resto."""
    question = context.get("question", "")

    if not _is_decision_question(question):
        return f"""Eres Aletheia, una IA cognitiva. Responde a esta pregunta de forma natural, directa y útil en 2-4 frases.
No uses listas ni estructura formal. No menciones "tensión", "variable crítica" ni "análisis".

Pregunta: {question}

Responde con una sola cadena de texto, sin JSON."""

    profile_instructions = _build_profile_instructions(context.get("user_profile"))
    scenario_summary = "\n".join(
        f"- {s.get('type','?')}: {str(s.get('outcome',''))[:80]}"
        for s in scenarios[:3]
    )
    risks_str   = ", ".join(str(r) for r in risks[:3])   if risks   else "ninguno identificado"
    assumptions_str = ", ".join(str(a) for a in assumptions[:2]) if assumptions else "ninguno"

    return f"""Eres un analista estratégico. Destila el insight clave en una lectura corta y penetrante.

Decisión: {question}
Escenarios: {scenario_summary}
Riesgos: {risks_str}
Supuestos: {assumptions_str}
{profile_instructions}

Responde SOLO con este JSON (sin texto adicional, máximo 60 palabras por campo):
{{"insight": "una frase directa sobre el fondo real de la decisión", "key_variable": "el factor que lo determina todo", "recommendation_bias": "conservative|exploratory|aggressive"}}"""

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

