"""CEL Auto-optimization Loop."""

from core.aco.learning_layer import ACOLearningLayer
from core.learning.evaluator import ResponseEvaluator  # Assume exists

aco_learning = ACOLearningLayer()
evaluator = ResponseEvaluator()

def feedback_loop(policy: dict, response: str, score: float):
    """Learn from execution."""
    aco_learning.record({}, policy["mode"], {"dqs": score})
    # Future: router.learning.process(...)

