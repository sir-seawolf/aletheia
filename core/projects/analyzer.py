"""Multi-dimensional scoring and LLM analysis for project cards."""
from __future__ import annotations


def compute_score(project: dict) -> float:
    """
    Returns a score from -10 to +10.
    Positive = net benefit over time, negative = net burden.

    Weights: financial 40%, psychological 30%, physical 15%, relational 15%.
    """
    # Financial axis [-10, +10]
    cost_upfront = float(project.get("cost_upfront") or 0)
    benefit_monthly = float(project.get("benefit_monthly") or 0)
    cost_recurring = float(project.get("cost_recurring_monthly") or 0)
    net_monthly = benefit_monthly - cost_recurring

    if cost_upfront == 0 and net_monthly > 0:
        # Pure gain (e.g. career move to higher salary) — cap at 10
        fin = min(10.0, net_monthly / 100)
    elif cost_upfront > 0 and net_monthly > 0:
        # ROI: payback <12m = excellent (10), 120m = poor (0)
        payback = cost_upfront / net_monthly
        fin = max(0.0, 10.0 - payback / 12)
    elif cost_upfront > 0:
        # Pure cost — penalty capped at -5
        fin = max(-5.0, -cost_upfront / 5000)
    else:
        fin = 0.0

    # Psychological axis [-8, +8]
    stress = int(project.get("psychological_stress") or 3)
    reward = int(project.get("psychological_reward") or 3)
    psy = (reward - stress) * 2.0  # (-4 to +4) * 2

    # Physical axis [-6, +6]
    effort = int(project.get("physical_effort") or 1)
    benefit_phys = int(project.get("physical_benefit") or 1)
    phys = (benefit_phys - effort) * 1.5

    # Relational axis [-8, +8]
    relational = int(project.get("relational_impact") or 0)
    rel = relational * 4.0

    score = fin * 0.40 + psy * 0.30 + phys * 0.15 + rel * 0.15
    return round(max(-10.0, min(10.0, score)), 2)


def get_recommendation(score: float, project: dict) -> str:
    """Map score to recommendation string."""
    savings_required = float(project.get("savings_required") or 0)
    if savings_required > 0 and score >= 3:
        # Good project but has a financial prerequisite — flag for review
        return "review"
    if score >= 5:
        return "proceed"
    if score >= 1:
        return "defer"
    if score >= -2:
        return "review"
    return "discard"


async def analyze_with_llm(project: dict) -> dict:
    """Generate narrative analysis + recommendation via LLM."""
    try:
        from core.llm.router import LLMRouter
        router = LLMRouter()

        ptype = project.get("project_type", "other")
        title = project.get("title", "Proyecto")
        desc = project.get("description", "")

        pros_txt = "\n".join(f"+ {p}" for p in (project.get("pros") or []))
        cons_txt = "\n".join(f"- {c}" for c in (project.get("cons") or []))
        risks_txt = "\n".join(
            f"⚠ {r.get('description', r) if isinstance(r, dict) else r}"
            for r in (project.get("risks") or [])
        )

        cost = project.get("cost_upfront") or 0
        recurring = project.get("cost_recurring_monthly") or 0
        benefit = project.get("benefit_monthly") or 0
        payback = project.get("payback_months")
        savings_req = project.get("savings_required") or 0
        time_total = (
            (project.get("time_research_hours") or 0)
            + (project.get("time_execution_hours") or 0)
        )
        stress = project.get("psychological_stress") or 3
        reward = project.get("psychological_reward") or 3
        relational = project.get("relational_impact") or 0

        prompt = f"""Analiza este proyecto personal de forma concisa y honesta. Responde en español.

PROYECTO: {title} (tipo: {ptype})
{desc}

IMPACTO ECONÓMICO:
- Coste inicial: {cost:,.0f}€
- Coste recurrente: {recurring:,.0f}€/mes
- Beneficio/ahorro/ingreso generado: {benefit:,.0f}€/mes
- Meses hasta retorno inversión: {payback if payback else 'N/A'}
- Ahorro previo necesario para dar el paso: {savings_req:,.0f}€

TIEMPO COMPROMETIDO: {time_total:.0f}h totales

PROS:{chr(10) + pros_txt if pros_txt else ' (ninguno indicado)'}
CONTRAS:{chr(10) + cons_txt if cons_txt else ' (ninguno indicado)'}
RIESGOS:{chr(10) + risks_txt if risks_txt else ' (ninguno indicado)'}

BIENESTAR: estrés estimado {stress}/5, satisfacción esperada {reward}/5
IMPACTO RELACIONAL: {relational:+d} (escala -2 muy negativo, +2 muy positivo)

Responde con EXACTAMENTE este formato (sin texto extra antes o después):
ANÁLISIS: [3-5 oraciones sobre si merece la pena, cuándo y bajo qué condiciones]
RECOMENDACIÓN: [PROCEDER|DIFERIR|REVISAR|DESCARTAR]
CONDICIÓN: [La condición clave para proceder, en 1 frase, o N/A]"""

        reply = await router.generate(prompt, session_id="projects-llm")

        rec_map = {
            "PROCEDER": "proceed",
            "DIFERIR": "defer",
            "REVISAR": "review",
            "DESCARTAR": "discard",
        }
        recommendation = "review"
        for es_key, en_val in rec_map.items():
            if es_key in reply.upper():
                recommendation = en_val
                break

        return {"analysis_summary": reply, "recommendation": recommendation}

    except Exception as exc:
        return {
            "analysis_summary": f"Análisis no disponible: {exc}",
            "recommendation": "review",
        }
