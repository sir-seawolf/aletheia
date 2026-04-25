"""Capa de servicio para el sistema de memoria.

Decide qué memoria entra en el sistema y cómo se recupera el contexto.
"""

from datetime import datetime
from typing import List
from memory.storage import get_by_domain, save_memory
from memory.models import MemoryItem


def retrieve_context(domain: str) -> List[str]:
    """Recupera el contenido de las últimas memorias para un dominio.

    Args:
        domain: Dominio de la consulta.

    Returns:
        Lista de strings con el contenido de cada memoria.
    """
    memories = get_by_domain(domain)
    return [m.content for m in memories]


def store_event(question: str, domain: str, confidence: float = 0.8) -> int:
    """Guarda una pregunta/evento en la memoria tras una ejecución.

    Args:
        question: Pregunta o contenido del evento.
        domain: Dominio al que pertenece.
        confidence: Nivel de confianza (por defecto 0.8).

    Returns:
        ID del item guardado.
    """
    item = MemoryItem(
        type="event",
        content=question,
        domain=domain,
        confidence=confidence,
        created_at=datetime.now(),
    )
    return save_memory(item)

