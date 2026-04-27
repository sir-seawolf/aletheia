"""
Runtime FastAPI app for Aletheia Kernel v1.0.
Lightweight - kernel init via CLI.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Dict, Any

app = FastAPI(title="Aletheia Kernel v1.0", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Lightweight startup - kernel pre-initialized by CLI."""
    mode = os.getenv("ALETHEIA_MODE", "DEV")
    print(f"🧠 Aletheia API ready in {mode} mode")
    print("Endpoints: /health /api/simulate /docs")

@app.get("/")
async def root():
    return {"system": "Aletheia Kernel v1.0", "status": "ready", "endpoints": ["/health", "/api/simulate", "/docs"]}

@app.get("/health")
async def health():
    """Basic API health."""
    return {"status": "healthy", "kernel": "v1.0"}

@app.get("/system/health")
async def system_health():
    """Full system health (memory/LLM pre-checked by CLI)."""
    return {"status": "healthy", "components": {"api": "ok", "contract": "enforced"}}

@app.post("/api/simulate")
async def simulate_endpoint(request: Dict):
    """
    Full cognitive simulation with contract lock.
    """
    domain = request.get("domain", "unknown")
    question = request.get("question", "")
    from core.orchestrator import process_request
    result = process_request(domain, question)
    from core.contracts.contract_lock import validate_final_report
    validated = validate_final_report(result)
    return validated

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    await websocket.send_text(f"Connected to Aletheia Kernel v1.0 - session {session_id}")
    await websocket.close()

def run(mode: str = "DEV", host: str = "127.0.0.1", port: int = 8000):
    """Run API server."""
    reload = (mode == "DEV")
    uvicorn.run("core.bootstrap.runtime:app", host=host, port=port, reload=reload, log_level="info")

if __name__ == "__main__":
    run()

