"""CEL Cost Model."""

from typing import Dict, Any

def compute_cognitive_cost(context: Dict[str, Any]) -> float:
    """Proxy cognitive cost."""
    question_len = len(context.get("question", ""))
    domain = context.get("domain", "")
    complexity = question_len / 200.0  # Normalize
    # Base cost factors
    cost = min(1.0, 0.1 + complexity * 0.5 + (0.1 if "high_risk" in domain else 0))
    return cost

