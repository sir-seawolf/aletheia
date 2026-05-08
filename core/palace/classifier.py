from typing import List
import re

AREAS_KEYWORDS = {
    "CREACION": ["creacion", "crear", "crea", "build", "desarroll", "construir", "hacer"],
    "PROFESION": ["profesion", "trabajo", "carrera", "empleo", "negocio"],
    "PSIQUE": ["psique", "emocion", "mental", "identidad", "sentir"],
    "ROL": ["rol", "social", "interaccion", "relacion"],
    "TECNOLOGIA": ["tecnologia", "software", "python", "sistema", "codigo"],
    "VIDA": ["vida", "experiencia", "personal", "dia"]
}

def classify(content: str) -> List[str]:
    '''
    Clasificación determinista offline multi-área.
    Extrae todas las áreas aplicables por keywords (case-insensitive).
    '''
    if not content:
        return []
    
    lower_content = content.lower()
    matched_areas = []
    
    for area, keywords in AREAS_KEYWORDS.items():
        if any(re.search(r"\b" + re.escape(kw) + r"\w*", lower_content) for kw in keywords):
            matched_areas.append(area)
    
    return sorted(matched_areas)

