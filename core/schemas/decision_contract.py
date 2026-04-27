from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class DecisionReport(BaseModel):
    """
    DecisionReport Schema v1.0 - Contrato único de cognición.
    Validación estricta - todos campos obligatorios/controlados.
    """
    version: str = "1.0"

    
    # Identificación
    node_id: Optional[str] = None
    timestamp: datetime
    domain: str
    question: str
    
    # Cognitive core
    facts: List[str]
    gaps: List[str]
    scenarios: List[Dict[str, Any]]  # min 2 expected
    risks: Dict[str, float]  # {risk_name: score}
    assumptions: List[str]
    
    # Intelligence layer
    llm_insight: str
    llm_explanation: str  # NEW - explicación LLM unificada
    
    # Meta layer
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: str  # 'low'|'medium'|'high'
    validation_issues: List[str] = []
    
    # Memory coupling
    memory_influence: Optional[Dict[str, Any]] = None
    similar_cases: List[Dict[str, Any]] = []
    
    # Learning loop
    prediction: str
    outcome: Optional[str] = None  # future

    @validator('scenarios')
    def validate_scenarios(cls, v):
        if len(v) < 2:
            raise ValueError('Min 2 scenarios required')
        return v

    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

    class Config:
        schema_extra = {
            "example": {
                "version": "1.0",
                "node_id": "node-123",
                "timestamp": "2024-01-01T00:00:00",
                "domain": "business",
                "question": "¿Lanzar producto X?",
                "facts": ["Mercado crece 20%"],
                "gaps": ["Competencia desconocida"],
                "scenarios": [{"optimistic": "..."}, {"pessimistic": "..."}],
                "risks": {"mercado": 0.3},
                "assumptions": ["Economía estable"],
                "llm_insight": "Recomendación...",
                "llm_explanation": "Explicación detallada...",
                "confidence": 0.85,
                "risk_level": "medium",
                "validation_issues": [],
                "memory_influence": {"bias": "cautious"},
                "similar_cases": [],
                "prediction": "Éxito probable",
                "outcome": None
            }
        }
        validate_assignment = True
        extra = "forbid"  # Strict - no extra fields
