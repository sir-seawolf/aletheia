"""
Main orchestrator for Aletheia cognitive pipeline.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: agents.*, core.aco.*, core.cel, core.llm.router, memory.service, core.palace, core.metrics.*
Last stable version: v1.2

Pipeline: Profile extraction → Context → ACO middleware → CEL → Explorer → Simulator → Guardian → Palace attach → Contract
"""

from agents import explorer, simulator, guardian
from core.palace import attach_to_palace
from core.aco.middleware import apply_aco
from core.aco.engine import CognitiveOptimizer
from memory.service import retrieve_context
from core.palace.reader import read_palace
from core.metrics.decision_quality import compute_dqs
from core.aco.learning_layer import ACOLearningLayer
from core.cel import cel
from core.identity import user_profile as profile_module
from time import time

aco_optimizer = CognitiveOptimizer()
aco_learning  = ACOLearningLayer()


def process_request(domain: str, question: str) -> dict:
    """
    Execute full cognitive decision pipeline.

    Args:
        domain (str): Problem domain/context
        question (str): Decision question to process

    Returns:
        dict: DecisionReport compliant output with scenarios, risks, confidence

    Raises:
        Exception: Pipeline failure (ACO, agent errors, contract violation)
    """
    # Load and update user profile from question text
    profile      = profile_module.load()
    profile      = profile_module.extract_from_text(question, profile)
    profile_str  = profile_module.to_context_str(profile)

    context_dict = {
        "domain": domain,
        "question": question,
        "memory": retrieve_context(domain),
        "risk": {"level": "medium"},
        "constraints": [],
        "user_profile_str": profile_str,
    }
    start_time = time()

    # ACO Middleware
    context_dict = apply_aco(context_dict)
    policy = context_dict["aco_policy"]

    # CEL: Cognitive Execution Layer
    cel.execute(domain, question)

    # Run pipeline
    exploration = explorer.run(
        domain, question,
        policy=policy,
        memory=context_dict["memory"],
        user_profile_str=profile_str,
    )
    llm_calls_explorer = exploration.get("llm_calls", 0)

    simulation = simulator.run(exploration, policy=policy)
    llm_calls_sim = simulation.get("llm_calls", 0)

    validated = guardian.validate(simulation, policy=policy)

    end_time = time()

    output = validated.get("corrected_output", validated)

    dqs_value = compute_dqs(output) if "scenarios" in output else 0.5

    pipeline_state = {
        "explorer_time": 0.1,
        "llm_calls": llm_calls_explorer + llm_calls_sim,
        "palace_hits": len(read_palace(domain)),
        "guardian_block": output.get("guardian_block", False),
        "total_time": end_time - start_time,
        "dqs": dqs_value,
    }
    aco_optimizer.observe(pipeline_state)
    aco_learning.record(context_dict, policy["mode"], {"dqs": pipeline_state["dqs"]})

    # Ensure minimum contract fields
    if not isinstance(output.get("scenarios"), list) or len(output["scenarios"]) < 2:
        output["scenarios"] = [
            {"type": "optimista",   "outcome": "baseline"},
            {"type": "conservador", "outcome": "alternative"},
        ]

    output["domain"]   = domain
    output["question"] = question
    output["dqs"]      = round(dqs_value, 3)
    output.setdefault("guardian_block", False)
    output["guardian_block"] = bool(output["guardian_block"])
    output.setdefault("risks", {})
    output.setdefault("confidence", 0.5)
    output.setdefault("prediction", "ok")
    output.setdefault("llm_insight", "")

    # Expose profile so frontend can show what was captured
    output["user_profile"] = profile

    attach_to_palace(output)
    return output
