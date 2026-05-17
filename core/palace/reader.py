from typing import List, Dict, Any, Optional
from pathlib import Path
import re

_AREAS = ["CREACION", "PROFESION", "PSIQUE", "ROL", "TECNOLOGIA", "VIDA"]

# Runtime domain names → PALACE area names.
# Unknown domains fall back to all areas so no data is ever silently lost.
_DOMAIN_TO_AREA: Dict[str, str] = {
    "finanzas":    "VIDA",
    "finance":     "VIDA",
    "fiscal":      "VIDA",
    "economia":    "VIDA",
    "tecnico":     "TECNOLOGIA",
    "tech":        "TECNOLOGIA",
    "tecnologia":  "TECNOLOGIA",
    "profesion":   "PROFESION",
    "profesional": "PROFESION",
    "trabajo":     "PROFESION",
    "personal":    "PSIQUE",
    "psique":      "PSIQUE",
    "emocional":   "PSIQUE",
    "creacion":    "CREACION",
    "rol":         "ROL",
    "vida":        "VIDA",
}


def parse_entry(block: str) -> Dict[str, Any]:
    entry = {}
    for line in block.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            entry[key.strip()] = value.strip()
    return entry


def read_palace(area: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Read PALACE memory entries.

    - area=None           → all six areas merged
    - area=raw area name  → that area only (e.g. "VIDA")
    - area=runtime domain → mapped to the closest area (e.g. "finanzas" → "VIDA")
    - area=unknown string → all areas (safe fallback, never silently empty)
    """
    if area is None:
        target_areas = _AREAS
    else:
        canonical = area.upper()
        if canonical in _AREAS:
            target_areas = [canonical]
        elif area.lower() in _DOMAIN_TO_AREA:
            target_areas = [_DOMAIN_TO_AREA[area.lower()]]
        else:
            # Unknown domain — return all areas so callers always get data
            target_areas = _AREAS

    entries: List[Dict[str, Any]] = []
    for a in target_areas:
        path = Path(f"PALACE/{a}/memory.txt")
        if path.exists():
            content = path.read_text(encoding="utf-8")
            for block in re.finditer(
                r'---ENTRY---(.*?)(?=---ENTRY---|---END---|$)', content, re.DOTALL
            ):
                block_text = block.group(1).strip()
                if "timestamp:" in block_text:
                    entry = parse_entry(block_text)
                    entry["_area"] = a
                    entries.append(entry)
    return entries

