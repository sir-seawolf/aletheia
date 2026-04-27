"""Self-Reinforcement Detector (SRD) - Detects cognitive loops."""

from typing import List, Dict, Any
import math


def detect_self_reinforcement(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detects self-convincing loops.
    """
    if len(nodes) < 3:
        return {"risk": "low", "score": 0.0, "action": "no_action"}

    similarity_trend = _compute_similarity_trend(nodes)
    error_trend = _compute_error_trend(nodes)
    memory_dominance = _compute_memory_dominance(nodes)

    score = (
        similarity_trend * 0.4 +
        memory_dominance * 0.4 -
        error_trend * 0.2
    )

    if score > 0.7:
        return {
            "risk": "high",
            "score": score,
            "action": "reduce_memory_influence"
        }

    if score > 0.4:
        return {
            "risk": "medium",
            "score": score,
            "action": "apply_decay_boost"
        }

    return {
        "risk": "low",
        "score": score,
        "action": "no_action"
    }


def _compute_similarity_trend(nodes: List[Dict[str, Any]]) -> float:
    """High similarity between consecutive decisions."""
    if len(nodes) < 2:
        return 0.0

    sims = []
    for i in range(1, len(nodes)):
        sim = nodes[i].get("similarity_score", 0.0)
        sims.append(sim)

    return sum(sims) / len(sims)


def _compute_error_trend(nodes: List[Dict[str, Any]]) -> float:
    """Recent errors - high good (learning)."""
    errors = [n.get("prediction_error", 0) for n in nodes[-5:]]
    return sum(errors) / len(errors) if errors else 0.0


def _compute_memory_dominance(nodes: List[Dict[str, Any]]) -> float:
    """Old memory dominates."""
    weights = [n.get("weight", 0.5) for n in nodes]
    return max(weights) if weights else 0.5
