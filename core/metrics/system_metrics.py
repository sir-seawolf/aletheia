"""System Metrics - Drift detection and averages."""

from typing import Dict, Any, List
from memory.decision_store import get_recent_decisions
from core.metrics.decision_quality import compute_dqs
from core.metrics.drift_detector import detect_drift

def get_system_metrics(num_recent: int = 20) -> Dict[str, Any]:
    \"\"\"
    Computes avg DQS, drift, guardian rate.
    \"\"\"
    recent = get_recent_decisions(limit=num_recent)
    
    dqss = []
    guardian_blocks = 0
    for r in recent:
        dqs = r.get('dqs', 0.0)
        dqss.append(dqs)
        if r.get('guardian', {}).get('block', False):
            guardian_blocks += 1
    
    avg_dqs = sum(dqss) / len(dqss) if dqss else 0.0
    last_5_avg = sum(dqss[-5:]) / 5 if len(dqss) >= 5 else avg_dqs
    block_rate = guardian_blocks / len(recent) if recent else 0.0
    
    drift = last_5_avg < avg_dqs * 0.85  # threshold 15%
    
    return {
        "avg_dqs": round(avg_dqs, 2),
        "last_5_dqs": round(last_5_avg, 2),
        "drift_detected": drift,
        "guardian_block_rate": round(block_rate, 2),
        "total_decisions": len(recent)
    }

