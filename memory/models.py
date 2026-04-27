from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class MemoryItem:
    id: Optional[int] = None
    type: str = ""
    content: str = ""
    domain: str = ""
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class FeedbackItem:
    id: Optional[int] = None
    interaction_id: str = ""
    rating: int = 0
    signals: Dict[str, Any] = field(default_factory=dict)
    comment: str = ""
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class MemoryMeta:
    source: str = "system"
    confidence: float = 0.7
    tags: List[str] = field(default_factory=list)
    emotion: Optional[str] = None
    domain: Optional[str] = None

@dataclass
class MemoryRef:
    target_id: str = ""
    relation: str = ""
    weight: float = 1.0

@dataclass
class MemoryNode:
    id: str = ""
    type: str = ""
    title: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    meta: MemoryMeta = field(default_factory=MemoryMeta)
    refs: List[MemoryRef] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    version: int = 1
    active: bool = True

@dataclass
class UserProfile:
    domain: str = ""
    verbosity_preference: str = "medium"
    risk_tolerance: str = "medium"
    max_scenarios: int = 3

@dataclass
class DecisionMemoryNode:
    id: str = ""
    timestamp: str = ""
    domain: str = ""
    question: str = ""
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    scenarios: List[Dict[str, Any]] = field(default_factory=list)
    chosen_scenario: Optional[str] = None
    llm_insight: Dict[str, Any] = field(default_factory=dict)
    guardian: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Optional[str] = None
    real_outcome: Optional[str] = None
    delta: Optional[str] = None
    prediction_error: Optional[float] = None
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    tags: List[str] = field(default_factory=list)
