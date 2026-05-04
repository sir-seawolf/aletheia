"""Learning Rules - Adjust based on evaluation."""

def adjust_confidence(profile: dict, confidence_error: float) -> dict:
    """
    Calibrates confidence bias.
    """
    confidence_bias = profile.get("confidence_bias", 1.0)
    
    if confidence_error > 0.3:
        confidence_bias *= 0.9  # lower confidence
    else:
        confidence_bias *= 1.02  # slight boost
    
    profile["confidence_bias"] = round(confidence_bias, 3)
    return profile

def adjust_memory_weight(node: dict) -> dict:
    """
    Adjusts memory penalty/boost.
    """
    prediction_error = node.get("prediction_error", 0.5)
    
    if prediction_error > 0.4:
        node["memory_penalty"] = 0.5
    elif prediction_error < 0.2:
        node["memory_boost"] = 1.1
    
    return node

def adjust_profile(profile: dict, error: float) -> dict:
    """
    Evolves cognitive profile.
    """
    risk_aversion = profile.get("risk_aversion", 0.5)
    exploration_bias = profile.get("exploration_bias", 0.5)
    
    if error > 0.4:
        risk_aversion += 0.05
        exploration_bias += 0.05
    elif error < 0.2:
        risk_aversion -= 0.02
        exploration_bias -= 0.02
    
    profile["risk_aversion"] = round(risk_aversion, 3)
    profile["exploration_bias"] = round(exploration_bias, 3)
    
    return profile

