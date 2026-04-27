"""Director del sistema. Coordina agentes sin pensar ni responder directamente."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4
from core.risk_engine import get_risk_config
from core.context import Context
from core.event_bus import build_event, emit_event
from agents import explorer, simulator, guardian
from memory.service import retrieve_context, store_event, get_or_create_profile, store_preference
from memory.models import UserProfile

# Pipeline explícito de pasos
PIPELINE_STEPS = [
    "explore",
    "simulate",
    "validate",
]

# Mapa dinámico de pasos a funciones ejecutables
PIPELINE_MAP = {
    "explore": explorer.run,
    "simulate": simulator.run,
    "validate": guardian.validate,
}

# Contratos de salida esperados por paso (documentación de interfaz)
EXPLORATION_SCHEMA = {
    "facts": list,       # hechos relevantes extraídos
    "gaps": list,        # información faltante
    "confidence": float, # confianza en la exploración (0.0 - 1.0)
}

SIMULATION_SCHEMA = {
    "scenarios": list,    # escenarios generados
    "risks": list,       # riesgos identificados
    "assumptions": list, # supuestos explícitos
}


def process_request(
    domain: str,
    question: str,
    memory_data: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    user_profile: Optional[UserProfile] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Orquesta el flujo completo de procesamiento de una solicitud.

    Args:
        domain: Dominio de la consulta
        question: Pregunta del usuario
        memory_data: Datos de memoria relevantes (auto-recuperados si no se proveen)
        constraints: Restricciones adicionales
        user_profile: Perfil cognitivo del usuario (opcional)

    Returns:
        Resultado estructurado del pipeline
    """
    # Session para correlacionar eventos en stream
    session_id = session_id or str(uuid4())

    emit_event(
        build_event(
            session_id=session_id,
            agent="orchestrator",
            stage="thinking",
            event_type="request_received",
            payload={"domain": domain, "question": question},
            confidence=1.0,
        )
    )

    # 1. Calcular configuración de riesgo
    risk_config = get_risk_config(domain)

    # 2. Auto-recuperar memoria si no se provee
    if memory_data is None:
        memory_data = retrieve_context(domain)

    # 3. Resolver perfil: si no viene explícito, intentar recuperar de memoria
    if user_profile is None:
        user_profile = get_or_create_profile(domain)

    # 4. Construir contexto
    context = Context.from_request(
        domain=domain,
        question=question,
        memory=memory_data,
        risk_config=risk_config,
        constraints=constraints,
        user_profile=user_profile,
        session_id=session_id,
    )

    # 5. Ejecutar pipeline dinámicamente
    step_results = {}
    steps_executed = []

    emit_event(
        build_event(
            session_id=session_id,
            agent="orchestrator",
            stage="thinking",
            event_type="pipeline_started",
            payload={"steps": PIPELINE_STEPS},
            confidence=1.0,
        )
    )

    for step in PIPELINE_STEPS:
        try:
            # Bypass de validate si no requiere guardian
            if step == "validate" and not risk_config.get("require_guardian"):
                step_results["validate"] = {
                    "valid": True,
                    "issues": [],
                    "corrected_output": step_results["simulate"],
                }
                steps_executed.append("validate (bypass)")
                emit_event(
                    build_event(
                        session_id=session_id,
                        agent="guardian",
                        stage="done",
                        event_type="validation_bypassed",
                        payload={"reason": "require_guardian=False"},
                        confidence=1.0,
                    )
                )
                continue

            if step == "explore":
                emit_event(
                    build_event(
                        session_id=session_id,
                        agent="explorer",
                        stage="thinking",
                        event_type="exploration_started",
                        payload={},
                        confidence=0.0,
                    )
                )
                step_results["explore"] = PIPELINE_MAP[step](context, session_id=session_id)
                steps_executed.append("explore")

            elif step == "simulate":
                emit_event(
                    build_event(
                        session_id=session_id,
                        agent="simulator",
                        stage="thinking",
                        event_type="simulation_started",
                        payload={},
                        confidence=0.0,
                    )
                )
                step_results["simulate"] = PIPELINE_MAP[step](
                    context, step_results["explore"], session_id=session_id
                )
                steps_executed.append("simulate")

            elif step == "validate":
                emit_event(
                    build_event(
                        session_id=session_id,
                        agent="guardian",
                        stage="thinking",
                        event_type="validation_started",
                        payload={},
                        confidence=0.0,
                    )
                )
                step_results["validate"] = PIPELINE_MAP[step](
                    step_results["simulate"], risk_config, session_id=session_id
                )
                steps_executed.append("validate")
        except Exception as e:
            emit_event(
                build_event(
                    session_id=session_id,
                    agent=step,
                    stage="blocked",
                    event_type="error",
                    payload={"error": str(e)},
                    confidence=0.0,
                )
            )
            raise

    # 6. Guardar evento en memoria para trazabilidad
    try:
        store_event(question=question, domain=domain)
    except Exception:
        # Fallo silencioso: no bloquear respuesta por error de memoria
        pass

    emit_event(
        build_event(
            session_id=session_id,
            agent="orchestrator",
            stage="done",
            event_type="pipeline_finished",
            payload={"steps_executed": steps_executed},
            confidence=1.0,
        )
    )

    # 7. Construir trace cognitivo
    interaction_id = str(uuid4())
    cognitive_trace = _build_cognitive_trace(
        interaction_id=interaction_id,
        domain=domain,
        question=question,
        context=context,
        risk_config=risk_config,
        step_results=step_results,
        steps_executed=steps_executed,
    )

    # 8. Construir respuesta final con trazabilidad
    return {
        "domain": domain,
        "risk": risk_config,
        "pipeline": step_results,
        "final_output": step_results["validate"]["corrected_output"],
        "meta": {
            "interaction_id": interaction_id,
            "steps_executed": steps_executed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "0.3.0",
        },
        "trace": cognitive_trace,
    }


def _build_cognitive_trace(
    interaction_id: str,
    domain: str,
    question: str,
    context: Context,
    risk_config: Dict[str, Any],
    step_results: Dict[str, Any],
    steps_executed: List[str],
) -> Dict[str, Any]:
    """Construye el trace cognitivo completo del proceso de pensamiento."""
    explore = step_results.get("explore", {})
    simulate = step_results.get("simulate", {})
    validate = step_results.get("validate", {})

    # Uncertainty map
    gaps = explore.get("gaps", [])
    high_uncertainty = []
    medium_uncertainty = []
    low_uncertainty = []

    for gap in gaps:
        if any(k in gap.lower() for k in ["crítico", "falta", "desconocido", "sin"]):
            high_uncertainty.append(gap)
        elif any(k in gap.lower() for k in ["variable", "posible", "quizás"]):
            medium_uncertainty.append(gap)
        else:
            medium_uncertainty.append(gap)

    facts = explore.get("facts", [])
    if facts:
        low_uncertainty.append(f"{len(facts)} hechos confirmados")

    return {
        "request": {
            "domain": domain,
            "question": question,
            "profile_influence": context.user_profile is not None,
        },
        "context_snapshot": {
            "facts_loaded": len(facts),
            "memory_sources": [domain],
            "missing_fields": gaps,
            "profile_influence": context.user_profile is not None,
        },
        "risk_assessment": {
            "level": risk_config.get("level"),
            "reasons": [f"dominio={domain}"],
            "constraints_applied": [
                "require_multiple_scenarios" if risk_config.get("require_scenarios") else None,
                "low_temperature_reasoning" if not risk_config.get("allow_creativity") else None,
            ],
        },
        "pipeline": {
            "explorer": {
                "facts": facts,
                "gaps": gaps,
                "confidence": explore.get("confidence", 0.0),
            },
            "simulator": {
                "scenarios": [
                    {
                        "type": s.get("type"),
                        "description_preview": s.get("description", "")[:80] + "..."
                        if len(s.get("description", "")) > 80
                        else s.get("description", ""),
                    }
                    for s in simulate.get("scenarios", [])
                ],
            },
            "guardian": {
                "valid": validate.get("valid", False),
                "warnings": validate.get("issues", []),
                "constraints_enforced": risk_config.get("require_guardian", False),
            },
            "orchestrator_decision": {
                "flow_selected": "multi-scenario + conservative bias" if risk_config.get("level") == "high" else "exploratory",
                "agents_used": steps_executed,
            },
        },
        "reasoning_flow": [
            f"1. Se identifica riesgo {risk_config.get('level')} por dominio {domain}.",
            f"2. Explorer detecta {len(facts)} datos y {len(gaps)} lagunas.",
            "3. Simulator genera escenarios según nivel de riesgo.",
            "4. Guardian valida output contra reglas de calidad.",
            "5. Se evita recomendación directa.",
        ],
        "uncertainty_map": {
            "high_uncertainty": high_uncertainty,
            "medium_uncertainty": medium_uncertainty,
            "low_uncertainty": low_uncertainty,
        },
        "memory_updates": {
            "new_memories": [f"usuario consulta: {question}"],
            "confidence": 0.8,
            "type": "intentional_state",
        },
        "system_adjustments": {
            "profile_updates": {
                "verbosity": getattr(context.user_profile, "verbosity_preference", "media") if context.user_profile else "media",
                "structure_preference": getattr(context.user_profile, "structure_preference", "sistémica") if context.user_profile else "sistémica",
            },
            "agent_tuning": {
                "simulator_temperature": 0.3 if not risk_config.get("allow_creativity") else 0.7,
            },
        },
    }
