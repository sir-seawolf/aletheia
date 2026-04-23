"""Modelos de datos para el sistema de memoria."""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import uuid


@dataclass
class MemoryItem:
    """Un item de memoria estructurado."""

    content: str
    type: str = "fact"  # fact, idea, goal, event, note
    domain: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0
    date: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def __post_init__(self):
        if self.date is None:
            self.date = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "date": self.date,
            "confidence": self.confidence,
            "source": self.source,
            "domain": self.domain,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            type=data.get("type", "fact"),
            content=data["content"],
            date=data.get("date"),
            confidence=data.get("confidence", 1.0),
            source=data.get("source"),
            domain=data.get("domain"),
            tags=data.get("tags", []),
        )

