"""API de entrada para Aletheia usando FastAPI."""

import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from core.orchestrator import process_request
from core.event_bus import get_event
from memory.models import UserProfile

app = FastAPI(title="Aletheia", description="Personal cognitive system for decision-making")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RiskConfig(BaseModel):
    """Configuración de riesgo tipada."""

    level: str
    require_scenarios: bool
    require_guardian: bool


class UserProfileInput(BaseModel):
    """Perfil cognitivo del usuario para adaptar el comportamiento del sistema."""

    verbosity_preference: str = "media"
    structure_preference: str = "sistémica"
    abstraction_capacity: str = "media"


class SimulationRequest(BaseModel):
    """Modelo de entrada para solicitudes de simulación."""

    domain: str
    question: str
    session_id: Optional[str] = None
    memory: List[str] = []
    constraints: Optional[List[str]] = None
    user_profile: Optional[UserProfileInput] = None


class SimulationResponse(BaseModel):
    """Modelo de salida para respuestas de simulación."""

    domain: str
    risk: dict
    pipeline: dict
    final_output: dict
    meta: dict


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest):
    """
    Endpoint principal para ejecutar una simulación cognitiva.
    """
    request_session_id = request.session_id or str(uuid.uuid4())
    print(
        f"[Aletheia] Session: {request_session_id} | Domain: {request.domain} | "
        f"Question: {request.question}"
    )

    # Convertir perfil de entrada si existe
    profile = None
    if request.user_profile:
        profile = UserProfile(
            verbosity_preference=request.user_profile.verbosity_preference,
            structure_preference=request.user_profile.structure_preference,
            abstraction_capacity=request.user_profile.abstraction_capacity,
        )

    # Si memory viene vacío, el orchestrator auto-recupera desde SQLite
    result = process_request(
        domain=request.domain,
        question=request.question,
        memory_data=request.memory if request.memory else None,
        constraints=request.constraints,
        user_profile=profile,
        session_id=request_session_id,
    )
    return result


@app.get("/")
def root():
    """Información básica del sistema."""
    return {"system": "Aletheia", "status": "running", "mode": "local-first cognitive engine"}


@app.get("/health")
def health_check():
    """Verificación de estado del sistema."""
    return {"status": "ok", "system": "aletheia"}


@app.websocket("/stream/{session_id}")
async def stream(websocket: WebSocket, session_id: str):
    """Streaming de eventos cognitivos en tiempo real por sesión."""
    print(f"[WS] Connected session: {session_id}")
    await websocket.accept()
    try:
        while True:
            event = get_event(session_id)
            if event is not None:
                print(f"[EVENT] {event}")
                await websocket.send_json(event)
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        return

