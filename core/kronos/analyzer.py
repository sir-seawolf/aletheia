"""
KRONOS analyzer — cognitive-financial and vital analysis.

quick_analysis(): voice response, single LLM call, real financial context.
full_analysis():  structured report with complete context.

Both use agent_id="kronos" so the router applies any per-agent LLM override
configured in preferences.json → llm.agents.kronos.
"""

from core.kronos.persona import SYSTEM_PROMPT
from core.kronos.financial_cache import summary_text
from core.llm import router as llm_router

_AGENT_ID = "kronos"


def _ctx(mode: str) -> str:
    ctx = summary_text(mode=mode)
    if not ctx:
        return ""
    return f"\n\n--- DATOS FINANCIEROS (PALACE) ---\n{ctx}\n--- FIN DATOS ---\n"


def quick_analysis(question: str) -> str:
    """Voice-optimized KRONOS response — 2-4 sentences, real data."""
    prompt = (
        f"{SYSTEM_PROMPT}"
        f"{_ctx('brief')}\n"
        f"Pregunta: {question}\n\n"
        "Responde en 2-4 frases directas para voz. "
        "Usa los datos reales si son relevantes. "
        "Sin listas, sin markdown, sin títulos."
    )
    return llm_router.generate(
        task="chat",
        prompt=prompt,
        context={"domain": "kronos", "mode": "voice"},
        temp=0.4,
        agent_id=_AGENT_ID,
    )


def full_analysis(question: str) -> str:
    """Full KRONOS report — complete financial context, structured sections."""
    prompt = (
        f"{SYSTEM_PROMPT}"
        f"{_ctx('full')}\n"
        f"Solicitud: {question}\n\n"
        "Genera un análisis completo con estas secciones exactas:\n"
        "# RESUMEN EJECUTIVO\n"
        "# PATRONES DETECTADOS\n"
        "# RIESGOS PRIORITARIOS\n"
        "# OPORTUNIDADES REALES\n"
        "# ACCIONES RECOMENDADAS (30 días)\n"
        "# DATOS FALTANTES IMPORTANTES\n"
        "# PREGUNTA REFLEXIVA FINAL"
    )
    return llm_router.generate(
        task="kronos_analysis",
        prompt=prompt,
        context={"domain": "kronos", "mode": "full"},
        temp=0.4,
        agent_id=_AGENT_ID,
    )
