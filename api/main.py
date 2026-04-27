"""API de entrada para Aletheia usando FastAPI."""

import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from core.orchestrator import process_request
from core.contracts.contract_lock import enforce_contract
from core.contracts.api_contract_gate import APIContractGate
from memory.service import save_decision
from core.metrics.system_metrics import get_system_metrics
from api.models import FeedbackRequest
from memory.service import self_evaluate_and_learn
from core.event_bus import get_event
from memory.service import retrieve_session_events

app = FastAPI(title="Aletheia", description="Personal cognitive system for decision-making")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationRequest(BaseModel):
    """Entrada mínima del sistema."""
    domain: str
    question: str
    session_id: Optional[str] = None

@app.post("/simulate")
def simulate(request: SimulationRequest):
    """
    Endpoint principal - Pipeline limpio: input → process → contract.
    """
    # 1. Validate input
    validated_input = APIContractGate.validate_request({
        "domain": request.domain,
        "question": request.question
    })

    # 2. Process
    result = process_request(
        domain=validated_input["domain"],
        question=validated_input["question"],
    )

    # 3. Enforce contract
    final = enforce_contract(result)

    save_decision(final)
    return final

@app.get("/system/metrics")
def system_metrics():
    return get_system_metrics()

@app.get("/")
def root():
    """Información básica del sistema."""
    return {"system": "Aletheia", "status": "running", "mode": "local-first cognitive engine"}

@app.get("/health")
def health_check():
    """Verificación de estado del sistema."""
    return {"status": "ok", "system": "aletheia"}

@app.get("/sessions/{session_id}/events")
def get_session_events(session_id: str, limit: int = 1000):
    """Recupera el historial de eventos cognitivos de una sesión."""
    return {
        "session_id": session_id,
        "events": retrieve_session_events(session_id=session_id, limit=limit),
    }

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

