"""CEL Adaptive Routing."""

from core.llm.router import router
from typing import Dict, Any, Optional

def adaptive_generate(task: str, prompt: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    """Router.generate with CEL policy adaptation."""
    # Policy-aware temp/cost
    policy = context.get("policy", {}) if context else {}
    temp = policy.get("temperature", 0.3)
    return router.generate(task=task, prompt=prompt, context=context, temp=temp, **kwargs)

