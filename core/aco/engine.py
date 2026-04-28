from typing import Dict, Any, List
from .memory import ACOMemory

class CognitiveOptimizer:
    def __init__(self):
        self.memory = ACOMemory()
        self.metrics = []

    def observe(self, pipeline_state: Dict[str, Any]):
        """
        Track: explorer_time, llm_calls, palace_hits, etc.
        """
        self.metrics.append(pipeline_state)
        self.memory.record_metric(pipeline_state)

    def analyze(self) -> Dict[str, float]:
        if not self.metrics:
            return {}
        return {
            "explorer_load": self._avg("explorer_time"),
            "llm_cost": self._avg("llm_calls"),
            "palace_usage": self._avg("palace_hits"),
            "guardian_blocks": self._avg("guardian_block"),
        }

    def propose_optimizations(self) -> List[str]:
        analysis = self.analyze()
        suggestions = []

        if analysis.get("llm_cost", 0) > 0.7:
            suggestions.append("Reduce LLM usage via caching in router")

        if analysis.get("palace_usage", 0) < 0.3:
            suggestions.append("Increase Palace retrieval weight")

        if analysis.get("explorer_load", 0) < 0.2:
            suggestions.append("Bypass explorer in low complexity tasks")

        return suggestions

    def _avg(self, key: str) -> float:
        values = [m.get(key, 0) for m in self.metrics]
        return sum(values) / len(values) if values else 0.0

