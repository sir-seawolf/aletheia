"""Drift Detector v1 - Detects degradation/instability/false stability."""

from typing import List, Dict, Any

def detect_drift(dqs_series: List[float]) -> Dict[str, Any]:
    \"\"\"
    Detects 3 drift types on DQS series.
    \"\"\"
    if len(dqs_series) < 5:
        return {
            "drift": False,
            "reason": "not_enough_data",
            "avg_last_5": 0.0,
            "avg_total": 0.0,
            "variance": 0.0
        }

    last_5 = dqs_series[-5:]
    avg_last = sum(last_5) / len(last_5)
    avg_total = sum(dqs_series) / len(dqs_series)

    # Variance for instability
    variance = sum((x - avg_last) ** 2 for x in last_5) / len(last_5)

    # 1. Degradation: last_5 avg < total avg - 0.1
    degradation = avg_last < (avg_total - 0.1)

    # 2. Instability: high variance
    instability = variance > 0.02

    # 3. False stability: low avg + low variance
    false_stability = avg_last < 0.55 and variance < 0.01

    drift = degradation or instability or false_stability

    return {
        "drift": drift,
        "degradation": degradation,
        "instability": instability,
        "false_stability": false_stability,
        "avg_last_5": round(avg_last, 3),
        "avg_total": round(avg_total, 3),
        "variance": round(variance, 4)
    }

