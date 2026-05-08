"""
FastAPI entry point for Aletheia cognitive system.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: fastapi, core.orchestrator, core.contracts.*, memory.service, core.metrics.*
Last stable version: v1.1

Main endpoint: POST /simulate for decision pipeline.
"""

import asyncio
import uuid
from fastapi import Body, FastAPI, WebSocket, WebSocketDisconnect
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
    """
    Input model for decision simulation requests.

    Responsibility: Validate minimal input for cognitive pipeline.
    """ 
    domain: str
    question: str
    session_id: Optional[str] = None

@app.post("/simulate")
def simulate(request: SimulationRequest):
    """
    Main endpoint: Run full cognitive pipeline and enforce output contract.

    Args:
        request (SimulationRequest): Input domain, question, optional session_id

    Returns:
        dict: Validated DecisionReport with scenarios, risks, confidence

    Raises:
        ValidationError: Invalid input format
        ContractViolation: Output fails schema enforcement
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
    """
    Retrieve current system performance metrics.

    Args:
        None

    Returns:
        dict: System metrics data

    Raises:
        None
    """
    return get_system_metrics()

@app.get("/")
def root():
    """
    Root endpoint with system info.

    Args:
        None

    Returns:
        dict: Basic system status

    Raises:
        None
    """
    return {"system": "Aletheia", "status": "running", "mode": "local-first cognitive engine"}

@app.get("/health")
def health_check():
    """
    Health check endpoint.

    Args:
        None

    Returns:
        dict: Health status

    Raises:
        None
    """
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


# ── HESTIA endpoints ─────────────────────────────────────────────────────────

from core.hestia.engine import hestia as _hestia


class HestiaAnalysisRequest(BaseModel):
    hours_back: int = 24
    goal_ids: Optional[list] = None


class HestiaGoalRequest(BaseModel):
    title: str
    description: str
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    deadline: Optional[str] = None
    priority: int = 1
    notes: Optional[str] = None


class HestiaGoalUpdateRequest(BaseModel):
    current_value: float
    notes: Optional[str] = None


@app.post("/hestia/analyze")
def hestia_analyze(request: HestiaAnalysisRequest):
    """Activación bajo demanda de HESTIA."""
    return _hestia.trigger_analysis(
        hours_back=request.hours_back,
        goal_ids=request.goal_ids,
    )


@app.get("/hestia/status")
def hestia_status():
    """Estado rápido de HESTIA."""
    return _hestia.status()


@app.post("/hestia/goals")
def hestia_add_goal(request: HestiaGoalRequest):
    """Añade un nuevo objetivo estratégico."""
    goal_id = _hestia.add_goal(request.model_dump())
    return {"created": True, "goal_id": goal_id}


@app.put("/hestia/goals/{goal_id}/progress")
def hestia_update_progress(goal_id: int, request: HestiaGoalUpdateRequest):
    """Actualiza progreso hacia un objetivo."""
    _hestia.update_goal_progress(goal_id, request.current_value, request.notes)
    return {"updated": True}


@app.put("/hestia/goals/{goal_id}")
def hestia_edit_goal(goal_id: int, updates: dict = Body(...)):
    """Edita un objetivo existente."""
    _hestia.edit_goal(goal_id, updates)
    return {"edited": True}


@app.get("/hestia/goals")
def hestia_get_goals():
    """Lista objetivos activos con progreso."""
    return {"goals": _hestia.memory.get_active_goals()}


# ── TURBO endpoints ──────────────────────────────────────────────────────────

from core.turbo.mode import turbo_mode as _turbo_mode
from core.turbo.panel import turbo_panel as _turbo_panel


class TurboActivateRequest(BaseModel):
    strategy: str = "specialist"   # "specialist" | "race" | "panel"


@app.post("/turbo/on")
def turbo_on(request: TurboActivateRequest):
    """
    Activa TURBO mode.
    Lanza un probe paralelo a todos los providers y devuelve
    cuáles se conectaron, con qué modelo y latencia.
    """
    probe = _turbo_panel.probe_all()
    _turbo_mode.activate(strategy=request.strategy)
    _turbo_mode.set_probe(probe)

    available = [name for name, d in probe.items() if d["status"] == "ok"]

    return {
        "turbo": "on",
        "strategy": request.strategy,
        "available_count": len(available),
        "providers": probe,
        "routing": _turbo_mode.effective_routing(),
    }


@app.post("/turbo/off")
def turbo_off():
    """Desactiva TURBO mode. El router vuelve al provider primario configurado."""
    _turbo_mode.deactivate()
    return {"turbo": "off"}


@app.get("/turbo/status")
def turbo_status():
    """Estado actual de TURBO: activo, estrategia, providers y routing."""
    return {
        "active":          _turbo_mode.is_active(),
        "strategy":        _turbo_mode.get_strategy(),
        "available_count": len(_turbo_mode.available_providers()),
        "providers":       _turbo_mode.get_probe(),
        "routing":         _turbo_mode.effective_routing() if _turbo_mode.is_active() else {},
    }

