"""Capa de servicio para memoria - persistencia pura."""

from datetime import datetime
from typing import Dict
from memory.storage import init_db, save_memory
from memory.models import MemoryItem, DecisionMemoryNode
from memory.decision_store import save_node
from core.metrics.decision_quality import compute_dqs

def self_evaluate_and_learn(node_id: str, real_outcome: str, user_profile: dict):
    \"\"\"
    Closes SEL loop.
    \"\"\"
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
    # TODO: save_profile(user_profile)
    
    return {"error": node.prediction_error, "adjusted": True}

# Legacy (keep minimal)
def retrieve_context(domain: str) -> list:
    return []

def init_memory():
    init_db()

