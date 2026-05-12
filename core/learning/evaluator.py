"""
Response Evaluator v1 for LLMRouter
Evalúa calidad de respuesta LLM: coherencia, relevancia, estructura.
"""

import json


class ResponseEvaluator:

    def evaluate(self, prompt: str, response: str, context: dict = None) -> dict:
        """
        Evalúa calidad del output sin romper contrato.
        """

        score = 0.0
        flags = []

        # 1. coherencia básica
        if len(response) > 20:
            score += 0.3
        else:
            flags.append("too_short")

        # 2. relación con prompt
        if any(word in response.lower() for word in prompt.lower().split()[:5]):
            score += 0.3
        else:
            flags.append("low_relevance")

        # 3. estructura mínima
        if isinstance(response, str) and response.strip():
            score += 0.2
        else:
            flags.append("empty_response")

        # 4. contexto disponible
        if context and context.get("domain"):
            score += 0.2

        return {
            "score": min(score, 1.0),
            "flags": flags,
            "retry": score < 0.5
        }
