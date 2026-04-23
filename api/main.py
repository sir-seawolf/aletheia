"""API de entrada para Aletheia usando FastAPI."""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from core.orchestrator import process_request

app = FastAPI(title="Aletheia", description="Personal cognitive system for decision-making")


class RiskConfig(BaseModel):
    """Configuración de riesgo tipada."""

    level: str
    require_scenarios: bool
    require_guardian: bool


class SimulationRequest(BaseModel):
    """Modelo de entrada para solicitudes de simulación."""

    domain: str
    question: str
    memory: List[str] = []
    constraints: Optional[List[str]] = None


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
    print(f"[Aletheia] Domain: {request.domain} | Question: {request.question}")
    # Si memory viene vacío, el orchestrator auto-recupera desde SQLite
    result = process_request(
        domain=request.domain,
        question=request.question,
        memory_data=request.memory if request.memory else None,
        constraints=request.constraints,
    )
    return result


@app.get("/")
def root():
    """Información básica del sistema."""
    return {"system": "Aletheia", "mode": "local-first cognitive engine"}


@app.get("/health")
def health_check():
    """Verificación de estado del sistema."""
    return {"status": "ok", "system": "aletheia"}

