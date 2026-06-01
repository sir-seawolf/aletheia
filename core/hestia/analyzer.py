"""HestiaAnalyzer — strategic analysis with HESTIA personality.

STATUS: IMPLEMENTED (Hestia v1)
"""

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.hestia.memory import HestiaMemory


_HESTIA_PERSONALITY = """
Eres HESTIA, la parte estratégica de Miguel.

No eres un asistente. Eres esa persona que le conoce
bien, ha acumulado experiencia real, tiene criterio
propio, y le dice lo que ve — incluyendo lo que él
no quiere ver o no percibe.

CÓMO HABLAS:
- Directo por defecto. Sin rodeos, sin suavizar.
- Si algo no funciona, lo dices claro y explicas por qué.
- Si algo funciona bien, también lo reconoces.
  No eres pesimista sistemático — eres honesto.
- Si detectas que tu análisis no está aterrizando,
  cambias a preguntas: haces que él llegue solo
  a la conclusión en lugar de dársela mascada.
- Nunca condescendiente. Nunca genérico.
  Cada análisis es sobre Miguel, no sobre nadie más.

LO QUE SABES DE MIGUEL:
- Visión holística y capacidad de ver conjuntos complejos.
  Esto es una fortaleza real, no un adorno.
- A veces se pierde en los detalles o en análisis
  muy profundos cuando la acción simple era suficiente.
- Le cuesta detectar patrones de drenaje:
  tiempo, energía o recursos que se van sin retorno.
- Tiene más capacidad de la que usa económicamente.
- Objetivo actual: ingresos de clase media en España
  (~30.000€/año) en el menor tiempo posible.
  Esta dirección no cambia. La forma puede cambiar.

TU FUNCIÓN EN CADA ANÁLISIS:
1. ¿Lo que hizo hoy/este período le acerca o aleja
   del objetivo? Sé específico.
2. ¿Qué patrones ves que se repiten y no suman?
3. ¿Hay capacidades suyas que no está usando?
4. ¿Dónde se va el tiempo y la energía de verdad?
5. ¿Qué haría alguien con su perfil que estuviera
   moviéndose bien hacia ese objetivo?
"""

_ANALYSIS_FORMAT = """
Responde SOLO con JSON válido, sin texto adicional.
Estructura exacta:
{
  "alignment_score": <float 0.0-1.0>,
  "dominant_patterns": [<string>, ...],
  "drains_detected": [<string>, ...],
  "strengths_unused": [<string>, ...],
  "opportunities": [<string>, ...],
  "recommendations": [
    {
      "action": <string>,
      "priority": <int 1-3>,
      "why": <string>,
      "estimated_impact": <string>,
      "time_cost": <string>
    }
  ],
  "verdict": <string una línea directa sin filtro>
}
"""


class HestiaAnalyzer:

    def __init__(self):
        self.memory = HestiaMemory()

    def analyze(self, hours_back: int = 24,
                goal_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        observations = self.memory.get_observations(hours_back)
        goals = self.memory.get_active_goals()
        if goal_ids:
            goals = [g for g in goals if g["id"] in goal_ids]
        used_goal_ids = [g["id"] for g in goals]

        try:
            prompt = self._build_prompt(observations, goals, hours_back)
            raw = self._call_llm(prompt)
            result = self._parse_llm_response(raw, observations, goals)
            result["mode_used"] = "llm"
        except Exception:
            result = self._fallback_analysis(observations, goals)
            result["mode_used"] = "fallback"

        result.update({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "period": f"últimas {hours_back} horas",
            "goals_used": goals,
            "hours_analyzed": hours_back,
            "goal_ids": used_goal_ids,
        })
        return result

    def _build_prompt(self, observations: list,
                      goals: list, hours_back: int) -> str:
        goals_text = "\n".join(
            f"- {g['title']}: {g.get('current_value', 0)}/{g.get('target_value', '?')} "
            f"{g.get('target_unit', '')} (prioridad {g.get('priority', 1)})"
            for g in goals
        )

        all_flags: list[str] = []
        obs_summaries: list[str] = []
        for obs in observations:
            obs_summaries.append(obs.get("summary", ""))
            try:
                all_flags.extend(json.loads(obs.get("flags", "[]")))
            except Exception:
                pass

        flag_counts = Counter(all_flags)
        flags_text = "\n".join(
            f"  {flag}: {count}x" for flag, count in flag_counts.most_common()
        )
        obs_text = "\n".join(f"  - {s}" for s in obs_summaries[:30])

        return (
            f"{_HESTIA_PERSONALITY}\n\n"
            f"═══ OBJETIVOS ACTIVOS ═══\n{goals_text or 'Sin objetivos activos.'}\n\n"
            f"═══ ACTIVIDAD — ÚLTIMAS {hours_back}h ═══\n"
            f"Observaciones ({len(observations)} total):\n{obs_text or '  (sin actividad registrada)'}\n\n"
            f"Flags detectados:\n{flags_text or '  (ninguno)'}\n\n"
            f"═══ FORMATO DE RESPUESTA ═══\n{_ANALYSIS_FORMAT}"
        )

    def _call_llm(self, prompt: str) -> str:
        from core.llm.router import router
        return router.generate(
            task="hestia_analysis",
            prompt=prompt,
            context={"domain": "strategic", "hestia": True},
            temp=0.3,
        )

    def _parse_llm_response(self, response: str,
                            observations: list, goals: list) -> Dict[str, Any]:
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return self._fallback_analysis(observations, goals)

    def _fallback_analysis(self, observations: list,
                           goals: list) -> Dict[str, Any]:
        all_flags: list[str] = []
        domains: list[str] = []
        for obs in observations:
            domains.append(obs.get("domain", "unknown"))
            try:
                all_flags.extend(json.loads(obs.get("flags", "[]")))
            except Exception:
                pass

        flag_counts = Counter(all_flags)
        domain_counts = Counter(domains)
        top_domains = [d for d, _ in domain_counts.most_common(3)]

        has_high_value = flag_counts.get("high_value_domain", 0) > 0
        has_drains = flag_counts.get("repeated_domain", 0) > 0
        has_blocks = flag_counts.get("guardian_blocked", 0) > 0

        alignment = 0.5
        if has_high_value:
            alignment += 0.2
        if has_drains:
            alignment -= 0.1
        if has_blocks:
            alignment -= 0.15
        alignment = round(max(0.0, min(1.0, alignment)), 2)

        drains = []
        if has_drains:
            repeated = [d for d, c in domain_counts.items() if c > 3]
            drains = [f"Dominio repetido sin variación: {d}" for d in repeated]

        recs = []
        if not has_high_value and observations:
            recs.append({
                "action": "Redirigir tiempo hacia actividad de alto valor económico",
                "priority": 1,
                "why": "No se detectó actividad en dominios de alto valor en el período",
                "estimated_impact": "Alto",
                "time_cost": "Reorientación inmediata",
            })

        verdict = (
            "Actividad registrada en dominios relevantes." if has_high_value
            else "Sin actividad en dominios de alto valor detectada en el período."
        )

        return {
            "alignment_score": alignment,
            "dominant_patterns": top_domains,
            "drains_detected": drains,
            "strengths_unused": [],
            "opportunities": [],
            "recommendations": recs,
            "verdict": verdict,
        }
