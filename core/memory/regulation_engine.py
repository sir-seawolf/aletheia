"""Memory Regulation Engine (MRE) - Decay, Weighting, Calibration."""

import math
from typing import List, Dict, Any
from datetime import datetime
from .self_reinforcement_detector import detect_self_reinforcement


# -----------------------------
# 1. DECAY CONTROL GLOBAL
# -----------------------------
def apply_decay(age_days: float, lambda_: float = 0.04) -> float:
    """Decay exponencial para memoria antigua."""
    return math.exp(-lambda_ * age_days)


# -----------------------------
# 2. ERROR STABILIZATION
# -----------------------------
def error_stability_penalty(error: float) -> float:
    """
    Evita que errores extremos dominen el sistema.
    Min 0.2 to avoid total discard.
    """
    return max(0.2, 1 - error)


# -----------------------------
# 3. MEMORY WEIGHT REGULATION
# -----------------------------
def regulate_memory_weight(node: Dict[str, Any], similarity: float) -> float:
    """W = similarity * decay * (1-error) * confidence."""
    age_days = node.get("age_days", 1.0)
    decay = apply_decay(age_days)
    error_factor = error_stability_penalty(node.get("prediction_error", 0.0))
    confidence = node.get("confidence_before", 0.5)

    return similarity * decay * error_factor * confidence


# -----------------------------
# 4. SYSTEM DRIFT CONTROL
# -----------------------------
def compute_system_drift(nodes: List[Dict[str, Any]]) -> float:
    """Mean error last decisions."""
    if not nodes:
        return 0.0

    errors = [n.get("prediction_error", 0) for n in nodes]
    return sum(errors) / len(errors)


# -----------------------------
# 5. GLOBAL REGULATION SIGNAL
# -----------------------------
def compute_regulation_signal(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Drift + SRD regulation mode."""
    drift = compute_system_drift(nodes)
    sr = detect_self_reinforcement(nodes)

    if sr["risk"] == "high":
        return {
            "mode": "corrective",
            "bias_multiplier": 0.5,
            "message": "Self-reinforcement detected: forcing memory reset pressure",
            "sr_score": sr["score"]
        }

    if drift > 0.35:
        return {
            "mode": "conservative",
            "bias_multiplier": 0.7,
            "message": "High drift detected",
            "sr_score": sr["score"]
        }

    if drift < 0.15:
        return {
            "mode": "exploratory",
            "bias_multiplier": 1.1,
            "message": "Stable cognition",
            "sr_score": sr["score"]
        }

    return {
        "mode": "stable",
        "bias_multiplier": 1.0,
        "message": "Normal cognitive stability",
        "sr_score": sr["score"]
    }
