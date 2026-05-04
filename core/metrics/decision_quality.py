"""Decision Quality Score - Quantitative metric for report quality."""

from typing import Dict, Any, List

def compute_dqs(report: Dict[str, Any]) -> float:
    """
    DQS 0.0-1.0: Measures decision report quality.
    Components:
    - Scenarios diversity (0.3)
    - Confidence coherence (0.3)
    - Guardian quality (0.3)
    - Structure completeness (0.1)
    """
    scenarios: List[Dict] = report.get('scenarios', [])
    confidence: float = report.get('confidence', 0.5)
    guardian_block: bool = report.get('guardian_block', False)
    guardian_severity: str = report.get('guardian_severity', 'none')
    guardian_adjust: float = report.get('guardian_confidence_adjust', 1.0)
    risks = report.get('risks', {})

    # 1. Scenarios diversity (unique outcomes / total)
    valid_scenarios = [s for s in scenarios if isinstance(s, dict)]
    if valid_scenarios:
        outcomes = set(s.get('outcome', 'unknown') for s in valid_scenarios)
        diversity = len(outcomes) / len(valid_scenarios)
    else:
        diversity = 0.0

    # 2. Confidence coherence (close to guardian adjust)
    coherence = 1 - abs(confidence - guardian_adjust)

    # 3. Guardian quality
    if guardian_block:
        guardian_score = 0.2
    elif guardian_severity == 'high':
        guardian_score = 0.5
    elif guardian_severity == 'low':
        guardian_score = 0.8
    else:
        guardian_score = 1.0

    # 4. Structure completeness (risks coverage)
    structure_score = min(len(risks) * 0.2, 1.0) if risks else 0.5

    # Weighted DQS
    dqs = (
        0.3 * diversity +
        0.3 * coherence +
        0.3 * guardian_score +
        0.1 * structure_score
    )

    return round(max(0.0, min(1.0, dqs)), 2)

