"""Feedback Collector, Analyzer y Learning Engine para Aletheia.

Arquitectura:
    Feedback (usuario) → analyze → signals → apply_learning → adjustments

Principios:
    - Cambios pequeños y acumulativos
    - Reversibles
    - Patrón repetido antes de ajuste real
"""

from typing import Dict, Any, List, Optional
from feedback.models import Feedback, FeedbackSignal, SystemAdjustment
from memory.service import store_feedback, store_preference
from memory.storage import get_recent_feedback_signals


# Umbral mínimo de repeticiones para aplicar un ajuste
MIN_REPETITIONS = 3


def collect_feedback(feedback: Feedback) -> int:
    """Persiste feedback del usuario en memoria.

    Returns:
        ID del feedback guardado.
    """
    signals = {
        "too_verbose": feedback.too_verbose,
        "missed_key_info": feedback.missed_key_info,
        "good_structure": feedback.good_structure,
        "confusing": feedback.confusing,
    }
    return store_feedback(
        interaction_id=feedback.interaction_id,
        rating=feedback.rating,
        signals=signals,
        comment=feedback.comment,
    )


def analyze_feedback(feedback: Feedback) -> List[FeedbackSignal]:
    """Traduce feedback crudo en señales cognitivas de sistema.

    Mapeo:
        too_verbose     → exceso de exploración / verbosity alta
        missed_key_info → fallo del Explorer / relevance_threshold
        confusing       → fallo de estructura del Simulator
        good_structure  → refuerzo de patrón
    """
    signals = []

    if feedback.too_verbose:
        signals.append(FeedbackSignal(
            signal_type="too_verbose",
            source="user",
            confidence=_confidence_from_rating(feedback.rating),
            context={"rating": feedback.rating},
        ))

    if feedback.missed_key_info:
        signals.append(FeedbackSignal(
            signal_type="missed_key_info",
            source="user",
            confidence=_confidence_from_rating(feedback.rating),
            context={"rating": feedback.rating},
        ))

    if feedback.confusing:
        signals.append(FeedbackSignal(
            signal_type="confusing",
            source="user",
            confidence=_confidence_from_rating(feedback.rating),
            context={"rating": feedback.rating},
        ))

    if feedback.good_structure:
        signals.append(FeedbackSignal(
            signal_type="good_structure",
            source="user",
            confidence=_confidence_from_rating(feedback.rating),
            context={"rating": feedback.rating},
        ))

    return signals


def detect_implicit_signals(interaction_history: List[Dict[str, Any]]) -> List[FeedbackSignal]:
    """Genera señales implícitas basadas en comportamiento del usuario.

    Ejemplo: si el usuario reabre la misma pregunta múltiples veces,
    la respuesta probablemente fue confusa o incompleta.
    """
    signals = []
    question_counts: Dict[str, int] = {}

    for entry in interaction_history:
        q = entry.get("question", "")
        question_counts[q] = question_counts.get(q, 0) + 1

    for question, count in question_counts.items():
        if count >= 2:
            signals.append(FeedbackSignal(
                signal_type="confusing_or_incomplete",
                source="implicit",
                confidence=min(count * 0.3, 0.9),
                context={"question": question, "reopen_count": count},
            ))

    return signals


def apply_learning(
    signals: List[FeedbackSignal],
    current_profile: Optional[Dict[str, Any]] = None,
) -> List[SystemAdjustment]:
    """Aplica ajustes conservadores al sistema basados en señales acumuladas.

    Reglas:
        - Señal low confidence → ignorada
        - Señal medium → ajuste ligero
        - Señal high + repetida ≥ MIN_REPETITIONS → ajuste real
    """
    adjustments: List[SystemAdjustment] = []

    # Agrupar señales por tipo para detectar patrones
    signal_counts: Dict[str, List[FeedbackSignal]] = {}
    for s in signals:
        signal_counts.setdefault(s.signal_type, []).append(s)

    for signal_type, instances in signal_counts.items():
        avg_confidence = sum(s.confidence for s in instances) / len(instances)

        # Ignorar señales de baja confianza
        if avg_confidence < 0.4:
            continue

        # Verificar patrón repetido antes de ajustar
        if len(instances) < MIN_REPETITIONS:
            continue

        # Ajustes por tipo de señal
        if signal_type == "too_verbose":
            adjustments.append(SystemAdjustment(
                component="profile",
                change_description="verbosity_preference → baja",
                change_value=-1.0,
                reversible=True,
                reason=f"too_verbose reportado {len(instances)} veces (conf={avg_confidence:.2f})",
            ))

        elif signal_type == "missed_key_info":
            adjustments.append(SystemAdjustment(
                component="explorer",
                change_description="relevance_threshold -0.1",
                change_value=-0.1,
                reversible=True,
                reason=f"missed_key_info reportado {len(instances)} veces (conf={avg_confidence:.2f})",
            ))

        elif signal_type == "confusing":
            adjustments.append(SystemAdjustment(
                component="simulator",
                change_description="structure_mode → más jerárquico",
                change_value=1.0,
                reversible=True,
                reason=f"confusing reportado {len(instances)} veces (conf={avg_confidence:.2f})",
            ))

        elif signal_type == "good_structure":
            adjustments.append(SystemAdjustment(
                component="prompts",
                change_description="explicit_structure weight +0.1",
                change_value=0.1,
                reversible=True,
                reason=f"good_structure reportado {len(instances)} veces (conf={avg_confidence:.2f})",
            ))

    return adjustments


def process_feedback(
    feedback: Feedback,
    interaction_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Pipeline completo: collect → analyze → detect implicit → apply learning.

    Returns:
        Dict con signals, adjustments y metadata.
    """
    # 1. Persistir
    feedback_id = collect_feedback(feedback)

    # 2. Analizar explícito
    explicit_signals = analyze_feedback(feedback)

    # 3. Detectar implícito
    implicit_signals: List[FeedbackSignal] = []
    if interaction_history:
        implicit_signals = detect_implicit_signals(interaction_history)

    all_signals = explicit_signals + implicit_signals

    # 4. Aplicar aprendizaje
    adjustments = apply_learning(all_signals)

    # 5. Persistir preferencias derivadas (por ahora solo verbosity)
    for adj in adjustments:
        if adj.component == "profile" and "verbosity" in adj.change_description:
            store_preference("global", f"verbosity_adjusted:{adj.reason}")

    return {
        "feedback_id": feedback_id,
        "signals": [
            {"type": s.signal_type, "source": s.source, "confidence": s.confidence}
            for s in all_signals
        ],
        "adjustments": [
            {
                "component": a.component,
                "change": a.change_description,
                "reversible": a.reversible,
                "reason": a.reason,
            }
            for a in adjustments
        ],
        "meta": {
            "explicit_signals": len(explicit_signals),
            "implicit_signals": len(implicit_signals),
            "adjustments_applied": len(adjustments),
        },
    }


def _confidence_from_rating(rating: int) -> float:
    """Convierte rating 1-5 en confianza 0.0-1.0."""
    return min(max((rating - 1) / 4.0, 0.0), 1.0)

