"""
Palace Injection Engine v1
Inserta memoria estructural del Palace en el prompt de forma inteligente.
"""

from core.palace.reader import read_palace


AREA_WEIGHTS = {
    "CREACION": 0.2,
    "PROFESION": 0.3,
    "PSIQUE": 0.5,
    "ROL": 0.3,
    "TECNOLOGIA": 0.4,
    "VIDA": 0.2
}


def extract_relevant_palace(domain: str, task: str):
    """
    Devuelve contexto relevante del Palace según peso
    """

    raw = read_palace(domain) or []

    weighted = []

    for entry in raw:
        area = entry.get("area", "VIDA")
        weight = AREA_WEIGHTS.get(area, 0.1)

        weighted.append({
            "content": entry,
            "weight": weight
        })

    # ordenar por relevancia
    weighted.sort(key=lambda x: x["weight"], reverse=True)

    # top context
    return [w["content"] for w in weighted[:5]]


def inject_palace(prompt: str, domain: str, task: str):
    """
    Inserta memoria estructural en el prompt
    """

    palace_context = extract_relevant_palace(domain, task)

    if not palace_context:
        return prompt

    structured = "\n".join([
        f"- {p.get('area','?')}: {p.get('content','')}"
        for p in palace_context
    ])

    return f"""
CONTEXT MEMORY (PALACE):
{structured}

TASK:
{prompt}
"""
