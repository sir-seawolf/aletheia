from typing import Dict, Any
from core.context import Context  # Assume exists; extend if needed
from .adaptive_router import AdaptiveACO
from .learning_layer import ACOLearningLayer
from memory.service import retrieve_context
from core.palace.reader import read_palace
from core.llm.router import router

aco_adaptive = AdaptiveACO()
aco_learning = ACOLearningLayer()

def apply_aco(context: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    ACO Middleware: decide policy → inject.
    Called before pipeline.
    \"\"\"
    # Context metrics
    domain = context.get(\"domain\", \"unknown\")
    palace_hits = len(read_palace(domain))
    memory_hits = len(retrieve_context(domain))
    complexity = len(context.get(\"question\", \"\")) / 100  # Simple proxy

    # Learned + rule-based
    learned_mode = aco_learning.recommend_mode(context)
    rule_mode = aco_adaptive.decide_mode({
        \"complexity\": min(1.0, complexity),
        \"palace_hits\": palace_hits,
        \"memory_hits\": memory_hits,
        \"domain\": domain,
        \"cache_hit\": bool(router.cache.get(\"last\", \"\"))
    })

    mode = learned_mode if learned_mode != \"FULL_PIPELINE\" else rule_mode

    policy = {
        \"mode\": mode,
        \"llm_mode\": \"cheap\" if mode == \"FAST_PATH\" else \"balanced\",
        \"use_palace\": palace_hits > 0,
        \"simulation_depth\": \"low\" if mode in [\"FAST_PATH\"] else \"high\",
        \"temperature\": 0.2 if domain == \"tecnologia\" else 0.6,
        \"guardian_strict\": True,
        \"cache_aggressiveness\": 0.9 if mode == \"FAST_PATH\" else 0.5
    }

    context[\"aco_policy\"] = policy
    context[\"constraints\"].append(f\"aco:{mode}\")  # Assume constraints list

    return context

