"""Modelos de datos para el sistema de memoria."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class MemoryItem:
    """Un item de memoria estructurado."""

    type: str            # fact | idea | goal | event
    content: str
    domain: str
    confidence: float
    created_at: datetime
    id: Optional[int] = None


@dataclass
class UserProfile:
    """Perfil cognitivo del usuario. Tercera dimensión del sistema."""

    verbosity_preference: str = "media"      # baja | media | alta
    structure_preference: str = "sistémica"  # sistémica | narrativa
    abstraction_capacity: str = "media"      # alta | media | baja
    cognitive_style: str = "lineal"          # lineal | arborescente
    abstraction_tolerance: str = "media"     # alta | media | baja
    observed_preferences: List[str] = field(default_factory=list)
    id: Optional[int] = None

