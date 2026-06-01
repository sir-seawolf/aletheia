"""
STRATEGIC mode — long-term planning, scenario generation, trade-off analysis.

Absorbs agents/simulator logic: LLM scenario generation (JSON with regex/text
fallback), risk/assumption extraction, insight generation.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

_SYSTEM = (
    "Eres el modo ESTRATÉGICO de Aletheia. Tu función es pensar a largo plazo, "
    "priorizar objetivos, analizar escenarios y alinear decisiones con metas vitales. "
    "Considera trade-offs reales, preserva opcionalidad y evita el pensamiento táctico miope."
)

_SCENARIO_PROMPT = """\
Eres un simulador estratégico de decisiones personales. Tu trabajo es generar escenarios futuros realistas.

Dominio: {domain}
Pregunta: {question}
Hechos conocidos: {facts}
Vacíos de información: {gaps}
Contexto previo: {memory_str}

Instrucciones:
1. Genera al menos 2 escenarios: conservador y optimista.
2. Para cada escenario: descripción, probability (0.0-1.0), outcome (positivo/neutral/negativo), time_horizon.
3. Lista supuestos explícitos y riesgos clave.

Responde ÚNICAMENTE en JSON válido, sin markdown:
{{"scenarios": [{{"type": "optimista", "description": "...", "probability": 0.6, "outcome": "positivo", "time_horizon": "9 meses"}}, {{"type": "conservador", "description": "...", "probability": 0.3, "outcome": "neutral", "time_horizon": "9 meses"}}], "risks": ["riesgo 1"], "assumptions": ["supuesto 1"]}}"""

_INSIGHT_PROMPT = """\
Analiza estos escenarios y genera un insight estratégico conciso.

Escenarios: {scenarios}
Riesgos: {risks}

Responde en 2-3 frases con el insight estratégico más relevante. Sin markdown."""


class StrategicMode(CognitiveMode):
    mode_id      = ModeID.STRATEGIC
    fatigue_cost = 0.08
    min_energy   = 0.2

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")
        memory   = context.get("memory", [])
        facts    = context.get("facts", [])    # may come from chained AnalyticalMode
        gaps     = context.get("gaps", [])
        depth    = state.preferred_depth

        memory_str = _summarise_memory(memory, limit=5)

        # Step 1 — scenario generation
        scenarios, risks, assumptions = self._generate_scenarios(
            question, domain, facts, gaps, memory_str
        )

        # Step 2 — strategic insight
        insight = self._generate_insight(scenarios, risks, domain)

        # Step 3 — synthesised plan for conversational output
        prompt = (
            f"{_SYSTEM}\n\n"
            f"Dominio: {domain}\n"
            f"Solicitud: {question}\n"
            f"Contexto: {memory_str}\n"
            f"Escenarios generados: {len(scenarios)}\n"
            f"Profundidad: {depth}.\n"
            "Sintetiza el plan estratégico y los próximos pasos priorizados."
        )

        plan_response = self._llm(
            task="strategic",
            prompt=prompt,
            context={"domain": domain, "mode": "strategic"},
            temp=0.4,
        )

        return ModeResult(
            mode_id         = ModeID.STRATEGIC,
            output          = {
                "plan":        plan_response,
                "scenarios":   scenarios,
                "risks":       risks,
                "assumptions": assumptions,
                "insight":     insight,
            },
            confidence      = 0.7,
            tokens_used     = len(prompt.split()) + len(plan_response.split()),
            reasoning_depth = depth,
        )

    def _generate_scenarios(
        self,
        question: str,
        domain: str,
        facts: List[str],
        gaps: List[str],
        memory_str: str,
    ) -> Tuple[List[Dict], List[str], List[str]]:
        """LLM scenario generation with JSON → regex → generic fallback."""
        prompt = _SCENARIO_PROMPT.format(
            domain=domain,
            question=question,
            facts=facts or ["(sin datos previos)"],
            gaps=gaps or ["(sin vacíos detectados)"],
            memory_str=memory_str,
        )
        try:
            raw = self._llm(
                task="strategic_scenarios",
                prompt=prompt,
                context={"domain": domain},
                temp=0.4,
            )
            if not raw or raw.startswith("[ERROR]") or raw.startswith("[MOCK]"):
                raise ValueError("bad response")

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(
                    l for l in cleaned.splitlines() if not l.startswith("```")
                ).strip()

            # 1. direct JSON
            try:
                data = json.loads(cleaned)
                if isinstance(data, dict) and "scenarios" in data:
                    return (
                        data.get("scenarios", []),
                        data.get("risks", []),
                        data.get("assumptions", []),
                    )
            except (ValueError, TypeError):
                pass

            # 2. regex: first block containing "scenarios"
            m = re.search(r'\{[^{}]*"scenarios".*?\}', cleaned, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group())
                    return (
                        data.get("scenarios", []),
                        data.get("risks", []),
                        data.get("assumptions", []),
                    )
                except (ValueError, TypeError):
                    pass
        except Exception:
            pass

        return (
            _fallback_scenarios(domain),
            ["Incertidumbre en datos disponibles"],
            ["Condiciones del entorno relativamente estables"],
        )

    def _generate_insight(
        self,
        scenarios: List[Dict],
        risks: List[str],
        domain: str,
    ) -> str:
        """LLM strategic insight with JSON field extraction fallback."""
        prompt = _INSIGHT_PROMPT.format(scenarios=scenarios[:2], risks=risks[:3])
        try:
            raw = self._llm(
                task="strategic_insight",
                prompt=prompt,
                context={"domain": domain},
                temp=0.4,
            )
            if not raw or raw.startswith("[ERROR]") or raw.startswith("[MOCK]"):
                return ""

            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(
                    l for l in cleaned.splitlines() if not l.startswith("```")
                ).strip()

            try:
                data = json.loads(cleaned)
                if isinstance(data, dict):
                    return data.get("insight", cleaned)
            except (ValueError, TypeError):
                pass

            m = re.search(r'"insight"\s*:\s*"([^"]+)"', cleaned)
            if m:
                return m.group(1)

            return cleaned
        except Exception:
            return ""


# ── module helpers ───────────────────────────────────────────────────────────

def _fallback_scenarios(domain: str) -> List[Dict]:
    return [
        {
            "id": "s1", "type": "optimista",
            "description": f"Escenario favorable en {domain}: avance sostenido sin obstáculos mayores.",
            "outcome": "positivo", "probability": 0.55,
        },
        {
            "id": "s2", "type": "conservador",
            "description": f"Escenario cauto en {domain}: progreso gradual con ajustes necesarios.",
            "outcome": "neutral", "probability": 0.35,
        },
        {
            "id": "s3", "type": "pesimista",
            "description": f"Escenario adverso en {domain}: obstáculos que exigen replantear la estrategia.",
            "outcome": "negativo", "probability": 0.10,
        },
    ]


def _summarise_memory(memory: list, limit: int = 5) -> str:
    if not memory:
        return "(sin memoria previa)"
    return "; ".join(str(m)[:80] for m in memory[-limit:])
