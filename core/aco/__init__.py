"""
ACO - Aletheia Cognitive Optimizer v1
Observer → Adaptive → Learning → Middleware
"""

from .engine import CognitiveOptimizer
from .adaptive_router import AdaptiveACO
from .learning_layer import ACOLearningLayer
from .middleware import apply_aco
from .memory import ACOMemory

__all__ = ["CognitiveOptimizer", "AdaptiveACO", "ACOLearningLayer", "apply_aco", "ACOMemory"]

