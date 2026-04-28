from typing import Dict, Any, List
from .memory import ACOMemory
from core.metrics.decision_quality import compute_dqs  # Existing

class ACOLearningLayer:
    def __init__(self):
        self.memory = ACOMemory()
        self.stats = {\"user_stats\": {}, \"domain_stats\": {}, \"query_stats\": {}}

    def record(self, context: Dict[str, Any], mode: str, result_metrics: Dict[str, Any]):
        user = context.get(\"user_id\", \"anon\")
        domain = context.get(\"domain\", \"unknown\")
        qtype = self._classify_query(context.get(\"question\", \"\"))

        self.memory.record({
            \"user\": user,
            \"domain\": domain,
            \"qtype\": qtype,
            \"mode\": mode,
            **result_metrics
        })

        # Update stats
        for key in [user, domain, qtype]:
            if key not in self.stats:
                self.stats[key] = {}
            if mode not in self.stats[key]:
                self.stats[key][mode] = []
            self.stats[key][mode].append(result_metrics.get(\"dqs\", 0.5))

    def recommend_mode(self, context: Dict[str, Any]) -> str:
        user = context.get(\"user_id\", \"anon\")
        domain = context.get(\"domain\", \"unknown\")
        qtype = self._classify_query(context.get(\"question\", \"\"))

        scores = {}
        for stat_key in [user, domain, qtype]:
            for mode, dqss in self.stats.get(stat_key, {}).items():
                scores[mode] = scores.get(mode, 0) + sum(dqss) / len(dqss) if dqss else 0

        return max(scores, key=scores.get) if scores else \"FULL_PIPELINE\"

    def _classify_query(self, question: str) -> str:
        if any(word in question.lower() for word in [\"why\", \"how\", \"analyze\"]):
            return \"analysis\"
        elif \"fact\" in question.lower() or \"what\" in question.lower():
            return \"factual\"
        return \"general\"

