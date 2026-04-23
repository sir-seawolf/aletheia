"""Director del sistema. Coordina agentes sin pensar ni responder directamente."""

from typing import Dict, Any, List
from core.risk_engine import get_risk_config
from core.context import Context
from agents import explorer, simulator, guardian

# Pipeline explícito de pasos
PIPELINE_STEPS = [
    "explore",
    "simulate",
    "validate",
]


def process_request(
    domain: str,
    question: str,
    memory_data: List[str],
    constraints: List[str] = None,
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

    # 3. Ejecutar pipeline
    step_results = {}

    # 3.1 Exploración
    exploration = explorer.run(context)
    step_results["explore"] = exploration

    # 3.2 Simulación (condicionada por riesgo)
    simulation = simulator.run(context, exploration)
    step_results["simulate"] = simulation

    # 3.3 Validación (solo si el riesgo lo requiere)
    if risk_config.get("require_guardian", False):
        validation = guardian.validate(simulation, risk_config)
        step_results["validate"] = validation
    else:
        step_results["validate"] = {"valid": True, "issues": [], "corrected_output": simulation}

    # 4. Construir respuesta final
    return {
        "domain": domain,
        "risk": risk_config,
        "pipeline": step_results,
        "final_output": step_results["validate"]["corrected_output"],
    }

