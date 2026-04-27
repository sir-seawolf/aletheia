from pydantic import BaseModel, Field
from typing import Optional

class FeedbackRequest(BaseModel):
    node_id: str = Field(..., description="ID de la decision a evaluar")
    real_outcome: str = Field(..., min_length=3, description="Resultado real observado")
    outcome_score: Optional[float] = Field(None, ge=0, le=1, description="Opcional: valoracion 0-1")
    notes: Optional[str] = Field(None, max_length=500)
