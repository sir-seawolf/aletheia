import json
from typing import Dict, Any, Optional, List
# Note: Full prompts from ai/prompts.py refactored here. For brevity, include key ones + _enrich.

def _build_profile_instructions(profile: Optional[Dict[str, Any]]) -> str:
    # Simplified version from ai/prompts.py
    if not profile:
        return ""
    return "Adapt to user profile preferences."  # Expand as needed

def _enrich(prompt: str, mem: List[Any] = None, palace: List[Any] = None) -> str:
    mem_str = json.dumps((mem[-5:] if mem else []), indent=2)
    palace_str = json.dumps(palace or [], indent=2)
    return f"""Original prompt: {prompt}

MEMORY (recent 5): {mem_str}

PALACE: {palace_str}

Enrich this prompt with memory and palace context above."""

def exploration_prompt(context: Dict[str, Any]) -> str:
    profile_instructions = _build_profile_instructions(context.get("user_profile"))
    return f"""Eres un analista frío.
Dominio: {context.get('domain', 'general')}
Pregunta: {context.get('question', '')}
Memoria: {context.get('memory', [])}

{profile_instructions}

JSON: {{"facts": [], "gaps": [], "confidence": 0.8}}"""

# Add other prompts as used (simulation_prompt, insight_prompt etc.)
def simulation_prompt(context: Dict[str, Any]) -> str:
    return f"Simulation prompt for {context.get('domain')}: {context.get('question')}"

def insight_prompt(context: Dict[str, Any]) -> str:
    return f"Insight prompt for {context.get('domain')}"

