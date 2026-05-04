from typing import Dict, Any, List
from .memory import ACOMemory

class ACOLearningLayer:
    def __init__(self):
        self.memory = ACOMemory()
        self.stats = {"user_stats": {}, "domain_stats": {}, "query_stats": {}}

    def recommend_mode(self, context: Dict[str, Any]) -> str:
        domain = context.get("domain", "unknown")
        # Learned recommendation logic (stub for v1)
        return "FULL_PIPELINE"

    def record(self, context: Dict[str, Any], mode: str, metrics: Dict[str, Any]):
        record = {
            "context": context,
            "mode_used": mode,
            **metrics
        }
        self.memory.record(record)

    def get_stats(self) -> Dict[str, Any]:
        return self.memory.stats()

