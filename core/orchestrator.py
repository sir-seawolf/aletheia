"""Director del sistema. Coordina agentes sin pensar ni responder directamente."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.risk_engine import get_risk_config
from core.context import Context
from agents import explorer, simulator, guardian

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


def process_request(
    domain: str,
    question: str,
    memory_data: List[str],
    constraints: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Orquesta el flujo completo de procesamiento de una solicitud.

    Args:
        domain: Dominio de la consulta
        question: Pregunta del usuario
        memory_data: Datos de memoria relevantes
        constraints: Restricciones adicionales

    Returns:
        Resultado estructurado del pipeline
    """
    # 1. Calcular configuración de riesgo
    risk_config = get_risk_config(domain)

    # 2. Construir contexto
    context = Context.from_request(
        domain=domain,
        question=question,
        memory=memory_data,
        risk_config=risk_config,
        constraints=constraints,
    )

    # 3. Ejecutar pipeline dinámicamente
    step_results = {}
    steps_executed = []

    for step in PIPELINE_STEPS:
        # Bypass de validate si no requiere guardian
        if step == "validate" and not risk_config.get("require_guardian"):
            step_results["validate"] = {
                "valid": True,
                "issues": [],
                "corrected_output": step_results["simulate"],
            }
            steps_executed.append("validate (bypass)")
            continue

        if step == "explore":
            step_results["explore"] = PIPELINE_MAP[step](context)
            steps_executed.append("explore")

        elif step == "simulate":
            step_results["simulate"] = PIPELINE_MAP[step](
                context, step_results["explore"]
            )
            steps_executed.append("simulate")

        elif step == "validate":
            step_results["validate"] = PIPELINE_MAP[step](
                step_results["simulate"], risk_config
            )
            steps_executed.append("validate")

    # 4. Construir respuesta final con trazabilidad
    return {
        "domain": domain,
        "risk": risk_config,
        "pipeline": step_results,
        "final_output": step_results["validate"]["corrected_output"],
        "meta": {
            "steps_executed": steps_executed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "0.2.0",
        },
    }

