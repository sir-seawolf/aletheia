import re

_FINANCIAL = {
    "gasto", "gastos", "ahorro", "ahorrar", "dinero", "presupuesto", "deuda", "deudas",
    "inversión", "invertir", "ingresos", "ingreso", "hipoteca", "finanzas", "financiero",
    "banco", "sueldo", "salario", "cuenta", "tarjeta", "préstamo", "préstamos",
    "factura", "facturas", "impuesto", "impuestos", "cobro", "pago", "pagos",
    "compra", "compras", "gasto", "economía", "patrimonio", "liquidez", "ahorro",
}

_BEHAVIORAL = {
    "patrón", "patrones", "hábito", "hábitos", "rutina", "rutinas", "ciclo", "ciclos",
    "tendencia", "tendencias", "comportamiento", "costumbre", "costumbres", "repetitivo",
}

_ENERGY = {
    "energía", "productividad", "cansancio", "burnout", "rendimiento", "agotado",
    "saturación", "descanso", "fatiga", "sobrecarga", "eficiencia",
}

_VITAL = {
    "autonomía", "libertad", "propósito", "equilibrio", "sentido", "dirección",
    "independencia", "vida", "tiempo", "coherencia", "progreso", "satisfacción",
}

_ANALYSIS = {
    "analiza", "analizar", "análisis", "resumen", "evolución",
    "situación", "informe", "diagnóstico", "dime", "cuéntame", "explícame",
    "evalúa", "evaluar", "muéstrame", "muestra",
}

# Possessives / personal context — signal the user is asking about their own data
_PERSONAL = {"mis", "mi", "me", "mío", "mía", "tengo", "he", "estoy", "estamos"}

# Interrogatives that paired with a financial term = KRONOS query
_INTERROGATIVE = {
    "cómo", "como", "cuánto", "cuanto", "cuántos", "cuantos",
    "cuánta", "cuanta", "qué", "que", "cuál", "cual", "cuándo", "cuando",
}


def is_kronos_query(text: str) -> bool:
    """Return True if the query belongs to KRONOS's domain."""
    words = set(re.findall(r"[a-záéíóúüñ]+", text.lower()))

    has_financial  = bool(words & _FINANCIAL)
    has_analysis   = bool(words & _ANALYSIS)
    has_behavioral = bool(words & _BEHAVIORAL)
    has_energy     = bool(words & _ENERGY)
    has_vital      = bool(words & _VITAL)
    has_personal   = bool(words & _PERSONAL)
    has_question   = bool(words & _INTERROGATIVE)

    # Explicit analysis request on any domain
    if has_analysis and (has_financial or has_behavioral or has_energy or has_vital):
        return True
    # Financial question in personal context ("mis gastos", "cuánto tengo")
    if has_financial and (has_personal or has_question):
        return True
    # Dense financial (2+ terms) — clearly about money
    if len(words & _FINANCIAL) >= 2:
        return True
    # Behavioral / energy / vital analysis
    if has_analysis and (has_behavioral or has_energy or has_vital):
        return True

    return False
