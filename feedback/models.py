"""Modelos de datos para el sistema de feedback y aprendizaje."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class Feedback:
    """Entrada estándar de feedback del usuario."""

    user_id: str
    interaction_id: str
    rating: int                     # 1-5

    too_verbose: bool = False
    missed_key_info: bool = False
    good_structure: bool = False
    confusing: bool = False

    comment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackSignal:
    """Señal cognitiva traducida desde el feedback crudo."""

    signal_type: str                # too_verbose | missed_key_info | confusing | good_structure
    source: str                     # user | implicit
    confidence: float = 1.0         # 0.0 - 1.0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemAdjustment:
    """Ajuste aplicado al sistema tras analizar señales."""

    component: str                  # profile | explorer | simulator | prompts
    change_description: str
    change_value: float
    reversible: bool = True
    applied_at: datetime = field(default_factory=datetime.now)
    reason: str = ""

