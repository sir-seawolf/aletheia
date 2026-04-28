"""
Learning Loop v1 for LLMRouter
Feedback del resultado → Memory + Palace para auto-mejora.
"""

from memory.service import store_event
from core.palace.writer import write_to_palace
from datetime import datetime


class LearningLoop:

    def process(self, task: str, prompt: str, response: str, evaluation: dict, context: dict = None):

        domain = (context or {}).get("domain", "global")

        # 1. MEMORY EVENT (operativo)
        self._store_memory(task, prompt, response, evaluation, domain)

        # 2. PALACE ENTRY (estructural)
        self._store_palace(task, prompt, response, evaluation, domain)

        # 3. LEARNING SIGNAL
        return self._learning_signal(evaluation)

    def _store_memory(self, task, prompt, response, evaluation, domain):

        store_event({
            "type": "llm_interaction",
            "task": task,
            "domain": domain,
            "prompt": prompt,
            "response": response,
            "score": evaluation.get("score", 0),
            "flags": evaluation.get("flags", []),
            "timestamp": str(datetime.utcnow())
        })

    def _store_palace(self, task, prompt, response, evaluation, domain):

        # Solo guardar si hay valor suficiente
        if evaluation.get("score", 0) < 0.4:
            return

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "areas": [self._classify_area(task, domain)],
            "type": "llm_insight",
            "content": response,
            "tags": [domain],
            "source": "llm_router",
            "meta": {
                "task": task,
                "score": evaluation.get("score"),
                "flags": evaluation.get("flags", [])
            }
        }

        write_to_palace(entry["areas"], entry)

    def _classify_area(self, task, domain):

        task = task.lower()

        if "code" in task or "tech" in task:
            return "TECNOLOGIA"

        if "life" in task or "decision" in task:
            return "VIDA"

        if "role" in task:
            return "ROL"

        if "emotion" in task:
            return "PSIQUE"

        if "job" in task:
            return "PROFESION"

        return "CREACION"

    def _learning_signal(self, evaluation):

        score = evaluation.get("score", 0)

        return {
            "learn": score > 0.6,
            "reinforce": score > 0.8,
            "ignore": score < 0.3
        }
