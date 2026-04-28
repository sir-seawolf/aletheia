"""
Memory service layer - persistence and learning feedback loops.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: memory.storage, memory.models, core.learning.*, core.metrics.*
Last stable version: v1.1

Handles decision storage, context retrieval, SEL (self-evaluate-learn) loops.
"""

from datetime import datetime
from typing import Dict
from memory.storage import init_db, save_memory
from memory.models import MemoryItem, DecisionMemoryNode
from memory.decision_store import save_node
from core.metrics.decision_quality import compute_dqs

def self_evaluate_and_learn(node_id: str, real_outcome: str, user_profile: dict):
    """
    Self-Evaluate-Learn feedback loop for decision improvement.

    Args:
        node_id (str): ID of decision memory node
        real_outcome (str): Actual outcome vs predicted
        user_profile (dict): User cognitive profile

    Returns:
        dict: Evaluation metrics {'error': float, 'adjusted': bool}

    Raises:
        Exception: If node retrieval or adjustment fails
    """
    from memory.decision_store import get_node
    from core.learning.evaluator import evaluate_decision
    from core.learning.rules import adjust_confidence, adjust_memory_weight, adjust_profile
    
    node = get_node(node_id)
    node.real_outcome = real_outcome
    
    eval_metrics = evaluate_decision(node)
    
    node.prediction_error = eval_metrics["prediction_error"]
    node.confidence_after = 1 - node.prediction_error
    
    # Apply rules
    user_profile = adjust_confidence(user_profile, eval_metrics["confidence_error"])
    user_profile = adjust_profile(user_profile, node.prediction_error)
    node = adjust_memory_weight(node)
    
    # Persist
    save_node(node)
    # TODO: IMPLEMENT save_profile(user_profile) persistence
    
    return {"error": node.prediction_error, "adjusted": True}

# Legacy (keep minimal)
_STORE = []

def store_event(event: dict):
    _STORE.append(event)
    return len(_STORE)

def retrieve_context(domain: str) -> list:
    return [e for e in _STORE if e.get("domain") == domain]

def retrieve_context_nodes(domain: str) -> list:
    """Legacy compatibility for healthcheck."""
    return retrieve_context(domain)

def init_memory():
    init_db()

def save_decision(report: dict) -> None:
    """Persists final DecisionReport to memory store."""
    item = MemoryItem(
        type="decision",
        content=str(report),
        domain=report.get("domain", "unknown"),
        confidence=report.get("confidence", 0.5),
        created_at=datetime.now()
    )
    save_memory(item)

def retrieve_session_events(session_id: str, limit: int = 1000) -> list:
    """Retrieve session events from storage."""
    from memory.storage import get_session_events
    return get_session_events(session_id, limit)

def store_session_event(event: dict) -> int:
    """Store session event (compatibility stub)."""
    from memory.storage import save_session_event
    return save_session_event(event)

