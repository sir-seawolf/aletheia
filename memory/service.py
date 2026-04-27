"""Capa de servicio para el sistema de memoria.

Decide qué memoria entra en el sistema y cómo se recupera el contexto.
"""

from datetime import datetime
from typing import List, Optional
from memory.storage import (
    get_by_domain,
    save_memory,
    get_preferences_by_domain,
    save_preference,
    save_feedback,
    save_session_event as storage_save_session_event,
    get_session_events as storage_get_session_events,
    get_memory_nodes_by_domain,
)
from memory.models import MemoryItem, UserProfile, FeedbackItem, MemoryNode, MemoryMeta


def retrieve_context(domain: str) -> List[str]:
    """Recupera el contenido de las últimas memorias para un dominio."""
    memories = get_by_domain(domain)
    return [m.content for m in memories]


def retrieve_context_nodes(domain: str) -> List[MemoryNode]:
    """Recupera memoria estructurada; prioriza memory_nodes y cae a memory legacy."""
    nodes = get_memory_nodes_by_domain(domain=domain, limit=50)
    if nodes:
        return nodes

    memories = get_by_domain(domain)
    legacy_nodes: List[MemoryNode] = []

    for m in memories:
        legacy_nodes.append(
            MemoryNode(
                type=m.type if m.type else "note",
                title=m.content[:80] if m.content else "memory_item",
                content={"text": m.content},
                meta=MemoryMeta(
                    source="system",
                    confidence=float(m.confidence) if m.confidence is not None else 0.7,
                    domain=m.domain,
                ),
            )
        )

    return legacy_nodes


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


def get_or_create_profile(domain: str) -> UserProfile:
    """Recupera preferencias observadas y construye un perfil adaptado al dominio.

    Args:
        domain: Dominio de la consulta.

    Returns:
        UserProfile con preferencias observadas para ese dominio.
    """
    preferences = get_preferences_by_domain(domain)
    return UserProfile(
        verbosity_preference="media",
        structure_preference="sistémica",
        abstraction_capacity="media",
        observed_preferences=preferences,
    )


def store_preference(domain: str, preference: str) -> int:
    """Guarda una preferencia observada para que el perfil evolucione.

    Args:
        domain: Dominio al que pertenece la preferencia.
        preference: Descripción de la preferencia observada.

    Returns:
        ID de la preferencia guardada.
    """
    return save_preference(domain, preference)


def store_feedback(interaction_id: str, rating: int, signals: dict, comment: Optional[str] = None) -> int:
    """Guarda feedback del usuario sobre una interacción.

    Args:
        interaction_id: ID de la interacción evaluada.
        rating: Puntuación 1-5.
        signals: Dict con señales de sistema (too_verbose, missed_key_info, etc.).
        comment: Comentario opcional del usuario.

    Returns:
        ID del feedback guardado.
    """
    item = FeedbackItem(
        interaction_id=interaction_id,
        rating=rating,
        signals=signals,
        comment=comment,
        created_at=datetime.now(),
    )
    return save_feedback(item)


def store_session_event(event: dict) -> int:
    """Guarda un evento cognitivo asociado a una sesión."""
    return storage_save_session_event(event)


def retrieve_session_events(session_id: str, limit: int = 1000) -> List[dict]:
    """Recupera historial de eventos por sesión."""
    return storage_get_session_events(session_id=session_id, limit=limit)

