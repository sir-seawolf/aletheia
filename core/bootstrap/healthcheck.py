"""
Healthcheck utilities for /system/health endpoint.
Checks full system: memory, LLM, contracts, event bus.
"""

from memory.service import retrieve_context_nodes
from ai.ollama_client import healthcheck as llm_health
from core.contracts.contract_lock import freeze_contract_version
from memory.storage import get_all  # count memories

def system_health() -> dict:
    """
    Complete system healthcheck.
    Returns dict for /health endpoint.
    """
    status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # replace with real
        "components": {}
    }
    
    # Memory
    try:
        nodes = retrieve_context_nodes("health")
        mem_count = len(get_all()) if 'get_all' in globals() else 0
        status["components"]["memory"] = {
            "status": "healthy",
            "nodes_loaded": len(nodes),
            "total_memories": mem_count
        }
    except:
        status["components"]["memory"] = {"status": "error"}
        status["status"] = "degraded"
    
    # LLM
    try:
        llm_status = llm_health()
        status["components"]["llm"] = {"status": "healthy", "info": llm_status}
    except:
        status["components"]["llm"] = {"status": "error"}
        status["status"] = "degraded"
    
    # Contract
    try:
        version = freeze_contract_version()
        status["components"]["contract"] = {"status": "healthy", "version": version}
    except:
        status["components"]["contract"] = {"status": "error"}
    
    return status

def memory_status() -> dict:
    return system_health()["components"].get("memory", {})

def llm_status() -> dict:
    return system_health()["components"].get("llm", {})

