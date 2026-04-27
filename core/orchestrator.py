"""Director del sistema. Router puro: explorer → simulator → guardian."""

from agents import explorer, simulator, guardian

def process_request(domain: str, question: str) -> dict:
    \"\"\"
    Pipeline puro sin lógica adicional.
    \"\"\"
    exploration = explorer.run(domain=domain, question=question)
    simulation = simulator.run(exploration=exploration)
    validated = guardian.validate(simulation=simulation)
    return validated[\"corrected_output\"]

