"""Cognitive Execution Layer (CEL) - Fusión ACO + LLMRouter."""

from typing import Dict, Any, List
from core.context import Context
from core.aco.middleware import apply_aco
from core.llm.router import router
from memory.service import retrieve_context
from core.palace.reader import read_palace
import json

class CognitiveExecutionLayer:
    def execute(self, domain: str, question: str) -> Dict[str, Any]:
        # 1. CONTEXTO BASE
        memory = retrieve_context(domain)
        risk = {"level": "medium"}  # Default
        context = Context.from_request(domain, question, memory, risk)

        # 2. ACO DECIDE ESTRATEGIA (policy fusion)
        context_dict = context.to_dict()
        context_dict = apply_aco(context_dict)
        policy = context_dict["aco_policy"]
        # Extend policy with task_type for router
        policy["task_type"] = "cognitive_execution"  # Core task for CEL

        # 3. MEMORY + PALACE FUSION (recent)
        recent_memory = memory[-5:] if len(memory) >= 5 else memory
        palace = read_palace(domain)[:10]

        # 4. PROMPT COGNITIVO (serialized for router.generate)
        cognitive_prompt_data = {
            "question": question,
            "memory": recent_memory,
            "palace": palace,
            "strategy": policy
        }
        prompt_str = json.dumps(cognitive_prompt_data, indent=2) + "\n\nExecute cognitive strategy."

        # 5. LLM ROUTER EJECUTA SEGÚN POLÍTICA
        response = router.generate(
            task=policy["task_type"],
            prompt=prompt_str,
            context={
                "domain": domain,
                "policy": policy
            }
        )

        # 6. OUTPUT BRUTO (dict for pipeline)
        output = {
            "cognitive_response": response,
            "policy_used": policy,
            "domain": domain,
            "question": question
        }
        return output

    def _build_cognitive_prompt(self, q: str, mem: List, palace: List, policy: Dict) -> str:
        data = {
            "question": q,
            "memory": mem[-5:],
            "palace": palace[:10],
            "strategy": policy
        }
        return json.dumps(data, indent=2) + "\n\nApply cognitive strategy from policy."

# Singleton
cel = CognitiveExecutionLayer()

