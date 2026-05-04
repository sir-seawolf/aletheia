"""CEL Cognition: Fused ACO policy engine."""

from typing import Dict, Any
from core.aco.middleware import apply_aco
from core.cel.cost_model import compute_cognitive_cost

def build_cognitive_policy(context_dict: Dict[str, Any]) -> Dict[str, Any]:
    # Enhance apply_aco with cognitive cost
    policy = apply_aco(context_dict)["aco_policy"]
    cost = compute_cognitive_cost(context_dict)
    policy["cognitive_cost"] = cost
    policy["task_type"] = "cognitive_execution"
    return policy

