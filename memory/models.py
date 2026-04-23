"""Modelos de datos para el sistema de memoria."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MemoryItem:
    """Un item de memoria estructurado."""

    type: str            # fact | idea | goal | event
    content: str
    domain: str
    confidence: float
    created_at: datetime
    id: Optional[int] = None

