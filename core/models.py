from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class DecisionReport:
    """Informe de decisión unificado como output único del sistema."""
    interaction_id: str
    timestamp: str  # ISO string
    domain: str
    question: str
    
    # Snapshot cognitivo
    snapshot: Dict[str, Any]
    
    # Exploración
    facts: List[str]
    gaps: List[str]
    exploration_confidence: float
    
    # Simulación
    scenarios: List[Dict[str, Any]]
    risks: List[str]
    assumptions: List[str]
    
    # Validación
    validation_issues: List[str]
    valid: bool
    
    # Meta
    overall_confidence: float
    risk_level: str
    node_id: Optional[str] = None
    steps_executed: List[str]

    llm_insight: str = ""
    
    @classmethod
    def from_pipeline(cls, pipeline_result: Dict[str, Any], context: Dict[str, Any]) -> 'DecisionReport':
        explore = pipeline_result.get('explore', {})
        simulate = pipeline_result.get('simulate', {})
        validate = pipeline_result.get('validate', {})
        
        return cls(
            interaction_id=context.get('interaction_id', 'unknown'),
            timestamp=datetime.now(timezone.utc).isoformat(),
            domain=context.get('domain', 'unknown'),
            question=context.get('question', ''),
            snapshot=context.get('snapshot', {}),
            facts=explore.get('facts', []),
            gaps=explore.get('gaps', []),
            exploration_confidence=explore.get('confidence', 0.0),
            scenarios=simulate.get('scenarios', []),
            risks=simulate.get('risks', []),
            assumptions=simulate.get('assumptions', []),
            validation_issues=validate.get('issues', []),
            valid=validate.get('valid', False),
            overall_confidence=min(1.0, explore.get('confidence', 0.5) * 0.8 + (1.0 if validate.get('valid', False) else 0.3) * 0.2),
            risk_level=context.get('risk_level', 'medium'),
            steps_executed=context.get('steps_executed', []),
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d
