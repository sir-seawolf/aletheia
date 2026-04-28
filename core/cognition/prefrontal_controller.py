from memory.service import retrieve_context

from core.palace.search import PalaceSearchEngine


class PrefrontalController:

    def __init__(self):
        self.palace = PalaceSearchEngine()

    def process(self, domain: str, question: str, raw_input: str):

        # 1. INTENT ANALYSIS
        intent = self._analyze_intent(raw_input)

        # 2. STRATEGY DECISION
        strategy = self._decide_strategy(intent)

        # 3. CONTEXT RETRIEVAL
        memory = retrieve_context(domain)
        palace = self.palace.search(domain, question)

        # 4. RISK ANALYSIS
        risk = self._assess_risk(memory, palace, intent)

        # 5. BUILD PLAN
        return {
            "intent": intent,
            "strategy": strategy,
            "memory": memory[-5:],
            "palace": palace[:5],
            "risk": risk,
            "prompt_mode": self._prompt_mode(strategy, risk)
        }

    def _analyze_intent(self, text):

        t = text.lower()

        if "why" in t or "explain" in t:
            return "explain"

        if "should" in t or "best" in t:
            return "decide"

        if "predict" in t:
            return "predict"

        if "create" in t:
            return "create"

        return "analyze"

    def _decide_strategy(self, intent):

        if intent == "explain":
            return "structured"

        if intent == "predict":
            return "reflective"

        if intent == "create":
            return "multi-step"

        return "direct"

    def _assess_risk(self, memory, palace, intent):

        score = 0

        if len(memory) == 0:
            score += 0.2

        if len(palace) == 0:
            score += 0.2

        if intent == "predict":
            score += 0.2

        return min(score, 1.0)

    def _prompt_mode(self, strategy, risk):

        if risk > 0.6:
            return "careful"

        if strategy == "multi-step":
            return "decompose"

        return "normal"

