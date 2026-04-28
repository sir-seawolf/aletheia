"""
Palace Cognitive Search Engine v1 (PCSE)
Recuperación semántica del Palace como memoria activa para router.
"""

from core.palace.reader import read_palace


class PalaceSearchEngine:

    def search(self, domain: str, query: str = None):

        # 1. cargar todas las áreas
        all_data = self._load_all()

        # 2. scoring simple semántico (v1 heurístico)
        results = []

        for area, entries in all_data.items():
            for entry in entries:

                score = self._score(entry, query, area, domain)

                if score > 0.3:
                    results.append({
                        "area": area,
                        "content": entry.get("content"),
                        "score": score,
                        "meta": entry.get("meta", {})
                    })

        # 3. ordenar por relevancia
        return sorted(results, key=lambda x: x["score"], reverse=True)[:10]

    def _load_all(self):

        areas = ["CREACION", "PROFESION", "PSIQUE", "ROL", "TECNOLOGIA", "VIDA"]

        return {
            area: read_palace(area)
            for area in areas
        }

    def _score(self, entry, query, area, domain):

        score = 0.0

        content = str(entry.get("content", "")).lower()

        # coincidencia directa
        if query and query.lower() in content:
            score += 0.5

        # match de dominio
        if domain.lower() in content:
            score += 0.2

        # bonus por área relevante
        if area.lower() in ["tecnoogia", "vida", "psique"]:
            score += 0.1

        # penalización por baja calidad previa
        meta = entry.get("meta", {})
        score += float(meta.get("score", 0)) * 0.2

        return min(score, 1.0)
