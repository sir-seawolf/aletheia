"""
User profile: persistent demographic + financial data extracted progressively from conversations.
Stored in PALACE/IDENTITY/profile.json. Read on every request, updated when new data is found.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any

PROFILE_PATH = Path(__file__).parent.parent.parent / "PALACE" / "IDENTITY" / "profile.json"

_EMPTY: Dict[str, Any] = {
    "nombre": None,
    "edad": None,
    "pais": None,
    "ciudad": None,
    "ingresos_anuales": None,
    "ocupacion": None,
    "situacion_familiar": None,
    "ahorros": None,
    "gastos_mensuales": None,
    "tolerancia_riesgo": "medium",
}


def load() -> Dict[str, Any]:
    if PROFILE_PATH.exists():
        try:
            return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(_EMPTY)


def save(profile: Dict[str, Any]) -> None:
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def merge(profile: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge updates into profile, only overwriting None fields."""
    updated = dict(profile)
    for k, v in updates.items():
        if v is not None and not updated.get(k):
            updated[k] = v
    return updated


def extract_from_text(text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract demographic clues from any user text and merge into profile.
    Only fills fields that are currently None (never overwrites known data).
    Saves to disk if anything changed.
    """
    updated = dict(profile)
    q = text.lower()

    # Country / nationality
    if not updated.get("pais"):
        if any(w in q for w in ["español", "española", "españa", "spain"]):
            updated["pais"] = "España"
        elif any(w in q for w in ["mexicano", "mexicana", "méxico", "mexico"]):
            updated["pais"] = "México"
        elif any(w in q for w in ["argentino", "argentina"]):
            updated["pais"] = "Argentina"
        elif any(w in q for w in ["colombiano", "colombiana", "colombia"]):
            updated["pais"] = "Colombia"
        elif any(w in q for w in ["chileno", "chilena", "chile"]):
            updated["pais"] = "Chile"

    # Annual income — patterns: "gano 22k", "22000€", "sueldo de 22k"
    if not updated.get("ingresos_anuales"):
        for pattern in [
            r"(?:gano|cobro|sueldo|salario|ingreso[s]?)\s+(?:de\s+|sobre\s+|unos?\s+)?(\d+(?:[.,]\d+)?)\s*k",
            r"(?:gano|cobro|sueldo|salario)\s+(?:de\s+|sobre\s+)?(\d{4,6})\s*(?:€|euros?)",
            r"(\d{4,6})\s*(?:€|euros?)\s*(?:al\s+)?(?:año|anuales?|brutos?)",
        ]:
            m = re.search(pattern, q)
            if m:
                val = float(m.group(1).replace(",", "."))
                updated["ingresos_anuales"] = int(val * 1000 if val < 1000 else val)
                break

    # Age
    if not updated.get("edad"):
        for pattern in [
            r"tengo\s+(\d{2})\s+años",
            r"soy\s+(?:un\s+)?(?:hombre|mujer|chico|chica)\s+de\s+(\d{2})",
            r"(?:^|\s)(\d{2})\s+años(?:\s|$)",
        ]:
            m = re.search(pattern, q)
            if m:
                age = int(m.group(1))
                if 15 <= age <= 90:
                    updated["edad"] = age
                    break

    # Savings
    if not updated.get("ahorros"):
        for pattern in [
            r"(?:tengo|cuento con)\s+(?:ahorrados?\s+)?(\d+(?:[.,]\d+)?)\s*k",
            r"ahorros?\s+de\s+(\d+(?:[.,]\d+)?)\s*k",
            r"(?:tengo|cuento con)\s+(\d{3,6})\s*(?:€|euros?)\s*(?:ahorrados?|en\s+el\s+banco|guardados?)",
        ]:
            m = re.search(pattern, q)
            if m:
                val = float(m.group(1).replace(",", "."))
                updated["ahorros"] = int(val * 1000 if val < 1000 else val)
                break

    # Monthly expenses
    if not updated.get("gastos_mensuales"):
        for pattern in [
            r"gasto\s+(\d+(?:[.,]\d+)?)\s*(?:€|euros?)\s*(?:al\s+mes|mensual)",
            r"gastos?\s+(?:mensuales?\s+)?(?:de\s+)?(\d+(?:[.,]\d+)?)\s*(?:€|euros?)",
        ]:
            m = re.search(pattern, q)
            if m:
                updated["gastos_mensuales"] = int(float(m.group(1).replace(",", ".")))
                break

    # Occupation
    if not updated.get("ocupacion"):
        job_map = {
            "programador": "Programador/a", "desarrollador": "Desarrollador/a",
            "enfermero": "Enfermero/a", "enfermera": "Enfermero/a",
            "médico": "Médico/a", "medico": "Médico/a",
            "profesor": "Profesor/a", "maestra": "Profesor/a",
            "ingeniero": "Ingeniero/a", "ingeniera": "Ingeniero/a",
            "arquitecto": "Arquitecto/a", "abogado": "Abogado/a",
            "freelance": "Freelance", "autónomo": "Autónomo/a",
            "autonomo": "Autónomo/a", "empresario": "Empresario/a",
            "directivo": "Directivo/a", "comercial": "Comercial",
            "administrativo": "Administrativo/a",
        }
        for kw, label in job_map.items():
            if kw in q:
                updated["ocupacion"] = label
                break

    # Family situation
    if not updated.get("situacion_familiar"):
        if any(w in q for w in ["soltero", "soltera", "sin pareja"]):
            updated["situacion_familiar"] = "Soltero/a"
        elif any(w in q for w in ["casado", "casada", "pareja"]):
            updated["situacion_familiar"] = "En pareja/Casado"
        elif any(w in q for w in ["hijo", "hija", "hijos", "niños"]):
            updated["situacion_familiar"] = "Con hijos"

    if updated != profile:
        save(updated)
    return updated


def to_context_str(profile: Dict[str, Any]) -> str:
    """Build a concise context string for LLM injection. Returns empty string if no data."""
    lines = []
    if profile.get("nombre"):           lines.append(f"Nombre: {profile['nombre']}")
    if profile.get("edad"):             lines.append(f"Edad: {profile['edad']} años")
    if profile.get("pais"):             lines.append(f"País: {profile['pais']}")
    if profile.get("ciudad"):           lines.append(f"Ciudad: {profile['ciudad']}")
    if profile.get("ingresos_anuales"): lines.append(f"Ingresos anuales brutos: {profile['ingresos_anuales']:,} €/año")
    if profile.get("ocupacion"):        lines.append(f"Ocupación: {profile['ocupacion']}")
    if profile.get("situacion_familiar"): lines.append(f"Situación familiar: {profile['situacion_familiar']}")
    if profile.get("ahorros"):          lines.append(f"Ahorros actuales: {profile['ahorros']:,} €")
    if profile.get("gastos_mensuales"): lines.append(f"Gastos mensuales: {profile['gastos_mensuales']:,} €/mes")
    if not lines:
        return ""
    return "DATOS CONOCIDOS DEL USUARIO:\n" + "\n".join(f"  • {l}" for l in lines)
