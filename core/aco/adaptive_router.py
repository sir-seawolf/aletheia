from typing import Dict, Any

class AdaptiveACO:
    MODES = {
        "FAST_PATH": "LLMRouter -> guardian",
        "FULL_PIPELINE": "explorer -> simulator -> guardian",
        "MEMORY_DOMINANT": "memory + palace -> simulator -> guardian",
        "LLM_HEAVY": "LLMRouter (enriched) -> simulator -> guardian",
        "DEBUG": "all + logging",
    }

    def decide_mode(self, context: Dict[str, Any]) -> str:
        complexity = context.get("complexity", 0.5)
        cache_hit = context.get("cache_hit", False)
        domain = context.get("domain", "")
        palace_hits = context.get("palace_hits", 0)

        if cache_hit or complexity < 0.3:
            return "FAST_PATH"

        if domain in ["psique", "vida"] or palace_hits > 3:
            return "MEMORY_DOMINANT"

        if complexity > 0.8:
            return "LLM_HEAVY"

        return "FULL_PIPELINE"

