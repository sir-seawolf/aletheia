from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class DecisionMemoryNode:
    id: str
    timestamp: str

    domain: str
    question: str

    context_snapshot: Dict[str, Any]

    scenarios: List[Dict[str, Any]]
    chosen_scenario: Optional[str] = None

    llm_insight: Dict[str, Any] = field(default_factory=dict)
    guardian: Dict[str, Any] = field(default_factory=dict)

    expected_outcome: Optional[str] = None

    real_outcome: Optional[str] = None
    delta: Optional[str] = None

    tags: List[str] = field(default_factory=list)
