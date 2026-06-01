import json
from typing import Dict, Any, Optional, List
# Note: Full prompts from ai/prompts.py refactored here. For brevity, include key ones + _enrich.


def _enrich(prompt: str, mem: List[Any] = None, palace: List[Any] = None) -> str:
    mem_str = json.dumps((mem[-5:] if mem else []), indent=2)
    palace_str = json.dumps(palace or [], indent=2)
    return f"""Original prompt: {prompt}

MEMORY (recent 5): {mem_str}

PALACE: {palace_str}

Enrich this prompt with memory and palace context above."""

def exploration_prompt(context: Dict[str, Any]) -> str:
    profile_str = context.get("user_profile_str", "")
    memory = context.get("memory", [])
    profile_section = f"\nPerfil: {profile_str}" if profile_str else ""
    mem_section = f"\nMemoria relevante: {memory[:3]}" if memory else ""

    return f"""Extrae hechos y vacíos de información de esta entrada.

Dominio: {context.get('domain', 'general')}
Pregunta: {context.get('question', '')}{profile_section}{mem_section}

Responde ÚNICAMENTE con este JSON (sin texto extra, sin markdown):
{{"facts": ["hecho 1", "hecho 2"], "gaps": ["info faltante 1"], "confidence": 0.7}}

Si no hay hechos concretos:
{{"facts": ["Consulta exploratoria sin datos cuantitativos"], "gaps": ["Contexto específico no proporcionado"], "confidence": 0.5}}"""

# Add other prompts as used (simulation_prompt, insight_prompt etc.)
def simulation_prompt(context: Dict[str, Any]) -> str:
    return f"Simulation prompt for {context.get('domain')}: {context.get('question')}"

def insight_prompt(context: Dict[str, Any]) -> str:
    return f"Insight prompt for {context.get('domain')}"

