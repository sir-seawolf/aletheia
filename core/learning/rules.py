"""Learning Rules base - Simple adjustments to profile based on prediction errors.

Sprint 1: Basic rule for accumulated error adjustment.
"""

from typing import Optional
from copy import deepcopy
from memory.models import UserProfile


def adjust_profile_based_on_error(
    profile: UserProfile, 
    prediction_error: float, 
    domain: str,
    error_threshold: float = 0.3
) -> UserProfile:
    """
    Ajuste simple de profile basado en error de predicción acumulado.
    
    Si error > threshold, reduce abstraction_capacity o verbosity.
    """
    new_profile = deepcopy(profile)
    
    # Acumular señal de error en observed_preferences
    error_signal = f"high_error_{domain}: {prediction_error:.2f}"
    if error_signal not in new_profile.observed_preferences:
        new_profile.observed_preferences.append(error_signal)
    
    # Regla simple: si error alto repetido, ajustar preferencias
    high_errors = sum(1 for p in new_profile.observed_preferences if 'high_error_' in p)
    if high_errors >= 2:
        if new_profile.abstraction_capacity == "alta":
            new_profile.abstraction_capacity = "media"
        elif new_profile.verbosity_preference == "alta":
            new_profile.verbosity_preference = "media"
    
    return new_profile
