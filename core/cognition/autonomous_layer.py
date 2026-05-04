"""
Autonomous Cognition Layer (ACL) - Early decision gate before full LLM.

STATUS: IMPLEMENTED (v1 basic)
Dependencies: memory.service, core.palace.search
Role in pipeline: Pre-ACO, decides LLM bypass for low complexity (INPUT → ACL → ACO → CEL).
Consumes: question complexity, risk from context, memory/palace hits.
Writes to context: 'mode': 'internal' or 'llm'.
Metrics: sources memory/palace counts.
INTEGRATION_POINT: orchestrator.py before apply_aco(): self.acl.process(domain, question, context_dict)
"""

from memory.service import retrieve_context

from core.palace.search import PalaceSearchEngine


class AutonomousCognitionLayer:

    def __init__(self):
        self.palace = PalaceSearchEngine()

    def process(self, domain: str, question: str, context: dict):

        complexity = self._assess_complexity(question)

        decision = self._decide_llm_use(complexity, context)

        if not decision["use_llm"]:
            return self._internal_reasoning(domain, question, context)

        return {
            "mode": "llm",
            "reason": decision["reason"]
        }

    # -------------------------
    # 🧠 DECISION ENGINE
    # -------------------------

    def _decide_llm_use(self, complexity, context):

        if complexity == "low":
            return {"use_llm": False, "reason": "simple_rule_based"}

        if context.get("risk", 0) < 0.3 and complexity == "medium":
            return {"use_llm": False, "reason": "memory_sufficient"}

        return {"use_llm": True, "reason": "high_complexity_or_uncertainty"}

    # -------------------------
    # 🧠 INTERNAL REASONING
    # -------------------------

    def _internal_reasoning(self, domain, question, context):

        memory = retrieve_context(domain)
        palace = self.palace.search(domain, question)

        # razonamiento simbólico simple
        combined = memory + palace

        return {
            "mode": "internal",
            "answer": self._synthesize(combined, question),
            "sources": {
                "memory": len(memory),
                "palace": len(palace)
            }
        }

    def _assess_complexity(self, question):

        q = question.lower()

        if len(q) < 40:
            return "low"

        if "why" in q or "how" in q:
            return "medium"

        if "predict" in q or "strategy" in q:
            return "high"

        return "medium"

    def _synthesize(self, context_items, question):

        # heurística simple (no LLM)
        if not context_items:
            return "insufficient_internal_data"

        return max(context_items, key=lambda x: x.get("score", 0)).get("content", "No content")

