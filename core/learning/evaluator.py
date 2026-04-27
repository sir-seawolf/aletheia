"""Self-Evaluation Loop - Prediction error computation."""

def compute_prediction_error(expected: str, actual: str) -> float:
    \"\"\"
    Computes error 0.0-1.0 from expected vs actual outcome.
    \"\"\"
    if not expected or not actual:
        return 0.5
    
    expected_words = set(expected.lower().split())
    actual_words = set(actual.lower().split())
    
    if expected_words == actual_words:
        return 0.0
    
    overlap = len(expected_words & actual_words)
    total = max(len(expected_words), 1)
    
    similarity = overlap / total
    return round(1 - similarity, 3)

def evaluate_decision(node: dict) -> dict:
    \"\"\"
    Evaluates prediction/confidence error.
    \"\"\"
    error = compute_prediction_error(
        node.get("expected_outcome", ""),
        node.get("real_outcome", "")
    )
    
    confidence_error = abs(node.get("confidence_before", 0.5) - (1 - error))
    
    return {
        "prediction_error": error,
        "confidence_error": round(confidence_error, 3)
    }

