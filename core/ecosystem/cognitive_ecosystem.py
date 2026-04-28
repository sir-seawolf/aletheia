class LogicBrain:
    def think(self, data):
        return {"content": "Logical analysis: " + data.get("question", ""), "confidence": 0.8}

class ExplorerBrain:
    def think(self, data):
        return {"content": "Exploratory ideas for " + data.get("question", ""), "confidence": 0.6}

class CriticBrain:
    def think(self, data):
        return {"content": "Critical review needed for " + data.get("question", ""), "confidence": 0.7}

class MemoryBrain:
    def __init__(self, memory, palace):
        self.memory = memory
        self.palace = palace
    def think(self, data):
        return {"content": "From memory/palace", "confidence": 0.9}

class EconomyBrain:
    def __init__(self, economy):
        self.economy = economy
    def think(self, data):
        status = self.economy.status()
        return {"content": f"Economic advice: pressure {status['pressure']:.2f}", "confidence": 0.85}

class LLMBrain:
    def __init__(self, router):
        self.router = router
    def think(self, data):
        # Delegate to existing router
        return {"content": self.router._call("ollama", data.get("prompt", ""), 0.3), "confidence": 0.75}

class CognitiveEcosystem:

    def __init__(self, router, memory, palace, economy):

        self.cerebros = {
            "logic": LogicBrain(),
            "explorer": ExplorerBrain(),
            "critic": CriticBrain(),
            "memory": MemoryBrain(memory, palace),
            "economy": EconomyBrain(economy),
            "llm": LLMBrain(router)
        }

        self.meta_controller = MetaController()

    def process(self, input_data):

        proposals = {}

        # 1. Distribución paralela
        for name, brain in self.cerebros.items():
            proposals[name] = brain.think(input_data)

        # 2. Evaluación cruzada
        evaluated = self.meta_controller.evaluate(proposals)

        # 3. Selección final
        return self.meta_controller.select(evaluated)

class MetaController:

    def evaluate(self, proposals):

        scored = []

        for brain, output in proposals.items():

            score = self._score(output)

            scored.append({
                "brain": brain,
                "output": output,
                "score": score
            })

        return scored

    def select(self, scored):

        best = max(scored, key=lambda x: x["score"])

        return {
            "final_output": best["output"],
            "selected_brain": best["brain"],
            "confidence": best["score"]
        }

    def _score(self, output):
        # heurística simple inicial
        return output.get("confidence", 0.5)

