from core.risk_engine import get_risk_level
from agents import explorer, simulator, guardian

def process_request(domain, question, memory_data):
    # 1. Riesgo
    risk = get_risk_level(domain)
    # 2. Exploración
    context = explorer.run(memory_data)
    # 3. Simulación
    result = simulator.run(context, question, risk)
    # 4. Validación
    result = guardian.validate(result, risk)
    return {
        "domain": domain,
        "risk": risk,
        "response": result
    }
