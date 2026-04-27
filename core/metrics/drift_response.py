"""Drift Response v1 - Auto-correction policies."""

from typing import Dict, Any

DRIFT_POLICIES = {
    "degradation": {
        "confidence_factor": 0.85,
        "guardian_sensitivity": "high",
        "memory_weight": 0.7,
        "mode": "conservative"
    },
    "instability": {
        "confidence_factor": 0.8,
        "guardian_sensitivity": "high",
        "memory_weight": 0.6,
        "mode": "stabilize"
    },
    "false_stability": {
        "confidence_factor": 0.75,
        "guardian_sensitivity": "medium",
        "memory_weight": 0.5,
        "mode": "explore_more"
    }
}

def resolve_policy(drift_details: Dict[str, Any]) -> Dict[str, Any]:
    "Select active policy from drift types."
    if drift_details.get("degradation"):
        return DRIFT_POLICIES["degradation"]
    if drift_details.get("instability"):
        return DRIFT_POLICIES["instability"]
    if drift_details.get("false_stability"):
        return DRIFT_POLICIES["false_stability"]
    return {
        "confidence_factor": 1.0,
        "guardian_sensitivity": "normal",
        "memory_weight": 1.0,
        "mode": "normal"
    }

def apply_drift_response(report: Dict[str, Any], drift_details: Dict[str, Any]) -> Dict[str, Any]:
    "Apply policy to report."
    policy = resolve_policy(drift_details)
    
    # Adjust confidence
    report["confidence"] = round(
        report.get("confidence", 0.5) * policy["confidence_factor"], 3
    )
    
    # Add regulation metadata
    report["regulation"] = {
        "mode": policy["mode"],
        "confidence_factor": policy["confidence_factor"],
        "guardian_sensitivity": policy["guardian_sensitivity"],
        "memory_weight": policy["memory_weight"]
    }
    
    return report

