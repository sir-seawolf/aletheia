"""Event bus cognitivo (MVP) para emisión y consumo de eventos en tiempo real."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Any, Dict
from memory.service import store_session_event


@dataclass
class CognitiveEvent:
    """Evento cognitivo base para trazabilidad y streaming en vivo."""

    timestamp: str
    session_id: str
    agent: str
    stage: str
    event_type: str
    payload: Dict[str, Any]
    confidence: float = 0.0


event_streams: Dict[str, Queue[Dict[str, Any]]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_event(
    session_id: str,
    agent: str,
    stage: str,
    event_type: str,
    payload: Dict[str, Any] | None = None,
    confidence: float = 0.0,
) -> Dict[str, Any]:
    """Construye un evento cognitivo normalizado."""
    evt = CognitiveEvent(
        timestamp=_utc_now_iso(),
        session_id=session_id,
        agent=agent,
        stage=stage,
        event_type=event_type,
        payload=payload or {},
        confidence=confidence,
    )
    return asdict(evt)


def get_or_create_stream(session_id: str) -> Queue[Dict[str, Any]]:
    """Obtiene o crea la cola de eventos para una sesión."""
    if session_id not in event_streams:
        event_streams[session_id] = Queue()
    return event_streams[session_id]


def emit_event(event: Dict[str, Any]) -> None:
    """Publica un evento en la cola de la sesión correspondiente y persiste historial."""
    session_id = event.get("session_id", "local")
    stream = get_or_create_stream(session_id)
    stream.put(event)

    try:
        store_session_event(event)
    except Exception:
        # Persistencia best-effort: no bloquear el pipeline por fallo de storage.
        pass


def get_event(session_id: str) -> Dict[str, Any] | None:
    """Consume un evento de la cola de una sesión sin bloqueo."""
    stream = get_or_create_stream(session_id)
    try:
        return stream.get_nowait()
    except Empty:
        return None
