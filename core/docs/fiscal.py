"""
Calculadora fiscal española — IRPF e IVA.

Cubre:
  - IRPF: tramos 2024/2025, mínimo personal, rendimiento del trabajo,
    deducción autónomo (cuotas SS), retención estimada
  - IVA: tipos (21/10/4%), declaración trimestral (modelo 303)
  - Modelo 130: pago fraccionado trimestral IRPF autónomos
  - Resumen fiscal anual desde datos del artifact_store

Referencia normativa: Ley 35/2006 IRPF, RD 439/2007, ejercicio fiscal 2024.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

# ── IRPF 2024 — tramos escala general ──────────────────────────────────────

_TRAMOS_GENERAL: list[tuple[float, float]] = [
    (12_450,  0.19),
    (20_200,  0.24),
    (35_200,  0.30),
    (60_000,  0.37),
    (300_000, 0.45),
    (float("inf"), 0.47),
]

# Mínimo personal y familiar (Art. 57-61 LIRPF)
_MINIMO_PERSONAL        = 5_550.0
_MINIMO_TRABAJO_MAX     = 2_000.0   # deducción rendimiento trabajo (Art. 20)
_MINIMO_TRABAJO_UMBRAL  = 14_047.5  # a partir de aquí se reduce la deducción

# IVA tipos
IVA_GENERAL     = 0.21
IVA_REDUCIDO    = 0.10
IVA_SUPERRED    = 0.04

# Retención mínima autónomo en nómina/factura
RETENCION_AUTONOMO_GENERAL = 0.15   # general (>2 años)
RETENCION_AUTONOMO_INICIO  = 0.07   # primeros 2 años de actividad


# ── IRPF ───────────────────────────────────────────────────────────────────

@dataclass
class IRPFResult:
    renta_bruta: float
    base_liquidable: float
    minimo_personal: float
    deduccion_trabajo: float
    cuota_integra: float
    cuota_liquida: float     # cuota_integra - deducción mínimo personal
    tipo_efectivo: float     # %
    tramos: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tipo_efectivo_pct"] = round(self.tipo_efectivo * 100, 2)
        return d


def _deduccion_trabajo(renta_bruta: float) -> float:
    """Art. 20 LIRPF — deducción por obtención de rendimientos del trabajo."""
    if renta_bruta <= 13_115:
        return _MINIMO_TRABAJO_MAX
    if renta_bruta <= _MINIMO_TRABAJO_UMBRAL:
        return max(0, _MINIMO_TRABAJO_MAX - 1.15625 * (renta_bruta - 13_115))
    return 0.0


def calcular_irpf(
    renta_bruta: float,
    autonomo: bool = False,
    cuotas_ss: float = 0.0,
    otros_gastos_deducibles: float = 0.0,
    hijos: int = 0,
    edad: int = 40,
) -> IRPFResult:
    """
    Calcula IRPF para ejercicio 2024.

    Args:
        renta_bruta:             Ingresos brutos anuales (€)
        autonomo:                True si es trabajador por cuenta propia
        cuotas_ss:               Cuotas Seguridad Social pagadas (deducibles)
        otros_gastos_deducibles: Gastos adicionales deducibles (local, material, etc.)
        hijos:                   Número de hijos (mínimo familiar simplificado)
        edad:                    Edad del contribuyente
    """
    # Rendimiento neto
    deduccion_trabajo = 0.0
    if not autonomo:
        deduccion_trabajo = _deduccion_trabajo(renta_bruta)

    rendimiento_neto = renta_bruta - cuotas_ss - otros_gastos_deducibles - deduccion_trabajo

    # Mínimo personal y familiar
    minimo = _MINIMO_PERSONAL
    if edad >= 75:
        minimo += 1_400
    elif edad >= 65:
        minimo += 1_150
    minimo += hijos * 2_400   # simplificado: primer y segundo hijo

    base_liquidable = max(0.0, rendimiento_neto - minimo)

    # Cuota íntegra — tramos
    tramos_detalle: list[dict] = []
    cuota = 0.0
    limite_anterior = 0.0
    for limite, tipo in _TRAMOS_GENERAL:
        if base_liquidable <= limite_anterior:
            break
        tramo_base = min(base_liquidable, limite) - limite_anterior
        tramo_cuota = tramo_base * tipo
        tramos_detalle.append({
            "desde": round(limite_anterior, 2),
            "hasta": round(min(base_liquidable, limite), 2),
            "tipo":  round(tipo * 100, 1),
            "cuota": round(tramo_cuota, 2),
        })
        cuota += tramo_cuota
        limite_anterior = limite

    # Cuota líquida (deducción del mínimo personal sobre la base)
    cuota_minimo = _aplicar_tramos(minimo)
    cuota_liquida = max(0.0, cuota - cuota_minimo)

    tipo_efectivo = cuota_liquida / renta_bruta if renta_bruta > 0 else 0.0

    return IRPFResult(
        renta_bruta=round(renta_bruta, 2),
        base_liquidable=round(base_liquidable, 2),
        minimo_personal=round(minimo, 2),
        deduccion_trabajo=round(deduccion_trabajo, 2),
        cuota_integra=round(cuota, 2),
        cuota_liquida=round(cuota_liquida, 2),
        tipo_efectivo=round(tipo_efectivo, 4),
        tramos=tramos_detalle,
    )


def _aplicar_tramos(base: float) -> float:
    """Aplica la escala de tramos a una base (para calcular deducción mínimo personal)."""
    cuota = 0.0
    prev = 0.0
    for limite, tipo in _TRAMOS_GENERAL:
        if base <= prev:
            break
        tramo = min(base, limite) - prev
        cuota += tramo * tipo
        prev = limite
    return cuota


# ── Modelo 130 — pago fraccionado autónomos ────────────────────────────────

@dataclass
class Modelo130Result:
    trimestre: int
    year: int
    ingresos_acumulados: float
    gastos_acumulados: float
    rendimiento_neto: float
    base_pago: float           # 20% del rendimiento neto
    pagos_anteriores: float
    a_ingresar: float          # base_pago - pagos_anteriores (mín 0)

    def to_dict(self) -> dict:
        return asdict(self)


def calcular_modelo_130(
    ingresos_acumulados: float,
    gastos_acumulados: float,
    pagos_anteriores: float = 0.0,
    trimestre: int = 1,
    year: int = 2024,
) -> Modelo130Result:
    """
    Modelo 130 — pago fraccionado IRPF autónomos (actividades económicas).
    El 20% del rendimiento neto acumulado menos pagos ya efectuados.
    """
    rendimiento = max(0.0, ingresos_acumulados - gastos_acumulados)
    base_pago   = rendimiento * 0.20
    a_ingresar  = max(0.0, base_pago - pagos_anteriores)

    return Modelo130Result(
        trimestre=trimestre,
        year=year,
        ingresos_acumulados=round(ingresos_acumulados, 2),
        gastos_acumulados=round(gastos_acumulados, 2),
        rendimiento_neto=round(rendimiento, 2),
        base_pago=round(base_pago, 2),
        pagos_anteriores=round(pagos_anteriores, 2),
        a_ingresar=round(a_ingresar, 2),
    )


# ── IVA / Modelo 303 ───────────────────────────────────────────────────────

@dataclass
class IVAResult:
    trimestre: int
    year: int
    iva_repercutido: float    # IVA cobrado a clientes
    iva_soportado: float      # IVA pagado a proveedores
    cuota_a_ingresar: float   # repercutido - soportado (puede ser negativo → a compensar)
    a_ingresar: float         # max(0, cuota_a_ingresar)
    a_compensar: float        # max(0, -cuota_a_ingresar)
    desglose_repercutido: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def calcular_iva(
    base_imponible_21: float = 0.0,
    base_imponible_10: float = 0.0,
    base_imponible_4:  float = 0.0,
    iva_soportado: float = 0.0,
    trimestre: int = 1,
    year: int = 2024,
) -> IVAResult:
    """
    Modelo 303 — declaración trimestral de IVA.

    Args:
        base_imponible_21: Base gravada al 21% (ingresos sin IVA a tipo general)
        base_imponible_10: Base gravada al 10% (ingresos sin IVA a tipo reducido)
        base_imponible_4:  Base gravada al 4%  (ingresos sin IVA a tipo superreducido)
        iva_soportado:     IVA total soportado en compras/gastos del trimestre
    """
    iva_21 = round(base_imponible_21 * IVA_GENERAL, 2)
    iva_10 = round(base_imponible_10 * IVA_REDUCIDO, 2)
    iva_4  = round(base_imponible_4  * IVA_SUPERRED, 2)
    iva_repercutido = iva_21 + iva_10 + iva_4

    cuota = iva_repercutido - iva_soportado
    a_ingresar  = round(max(0.0, cuota), 2)
    a_compensar = round(max(0.0, -cuota), 2)

    return IVAResult(
        trimestre=trimestre,
        year=year,
        iva_repercutido=round(iva_repercutido, 2),
        iva_soportado=round(iva_soportado, 2),
        cuota_a_ingresar=round(cuota, 2),
        a_ingresar=a_ingresar,
        a_compensar=a_compensar,
        desglose_repercutido={"21%": iva_21, "10%": iva_10, "4%": iva_4},
    )


def precio_con_iva(base: float, tipo: str = "general") -> dict[str, float]:
    """Devuelve base, IVA y total para un importe dado."""
    rates = {"general": IVA_GENERAL, "reducido": IVA_REDUCIDO, "superreducido": IVA_SUPERRED}
    rate = rates.get(tipo, IVA_GENERAL)
    iva = round(base * rate, 2)
    return {"base": round(base, 2), "iva": iva, "total": round(base + iva, 2), "tipo": tipo, "porcentaje": rate * 100}


def desglosar_iva(total_con_iva: float, tipo: str = "general") -> dict[str, float]:
    """Extrae base e IVA de un total que ya incluye IVA."""
    rates = {"general": IVA_GENERAL, "reducido": IVA_REDUCIDO, "superreducido": IVA_SUPERRED}
    rate = rates.get(tipo, IVA_GENERAL)
    base = round(total_con_iva / (1 + rate), 2)
    iva  = round(total_con_iva - base, 2)
    return {"total": round(total_con_iva, 2), "base": base, "iva": iva, "tipo": tipo, "porcentaje": rate * 100}


# ── Resumen fiscal desde artifact_store ───────────────────────────────────

def resumen_fiscal(year: int = 2024) -> dict[str, Any]:
    """
    Genera un resumen fiscal completo a partir de los artefactos almacenados.
    Útil para autónomos con facturas emitidas y recibidas en PALACE.
    """
    from core.docs.artifact_store import financial_summary, query

    fin = financial_summary(year=year)
    ingresos_brutos = 0.0
    iva_repercutido = 0.0
    iva_soportado   = fin.get("total_vat", 0.0)  # IVA de facturas recibidas
    gastos_totales  = fin.get("total", 0.0)

    # Facturas emitidas (ingreso propio)
    emitidas = query(domain="finanzas", artifact_type="invoice",
                     date_from=f"{year}-01-01", date_to=f"{year}-12-31")
    for e in emitidas:
        fin_data = e.get("financial") or {}
        amount = float(fin_data.get("amount") or 0)
        vat    = float(fin_data.get("vat") or 0)
        ingresos_brutos += amount
        iva_repercutido += vat

    # Estimación IRPF autónomo básica
    irpf = calcular_irpf(
        renta_bruta=ingresos_brutos,
        autonomo=True,
        otros_gastos_deducibles=gastos_totales,
    )

    # IVA trimestral estimado (suma anual → dividido en 4 trimestres)
    iva_result = calcular_iva(
        base_imponible_21=ingresos_brutos,
        iva_soportado=iva_soportado,
        trimestre=4,
        year=year,
    )

    return {
        "year":             year,
        "ingresos_brutos":  round(ingresos_brutos, 2),
        "gastos_deducibles": round(gastos_totales, 2),
        "iva_repercutido":  round(iva_repercutido, 2),
        "iva_soportado":    round(iva_soportado, 2),
        "irpf":             irpf.to_dict(),
        "iva_anual":        iva_result.to_dict(),
        "advertencia": (
            "Estimación orientativa basada en documentos importados. "
            "Consulta con un gestor para la declaración oficial."
        ),
    }


# ── Formateo legible ───────────────────────────────────────────────────────

def format_irpf(r: IRPFResult) -> str:
    lines = [
        f"IRPF estimado {r.renta_bruta:,.0f} € brutos:",
        f"  Base liquidable:  {r.base_liquidable:,.2f} €",
        f"  Cuota íntegra:    {r.cuota_integra:,.2f} €",
        f"  Cuota a pagar:    {r.cuota_liquida:,.2f} €",
        f"  Tipo efectivo:    {r.tipo_efectivo * 100:.1f}%",
    ]
    if r.tramos:
        lines.append("  Tramos:")
        for t in r.tramos:
            lines.append(f"    {t['desde']:>8,.0f}–{t['hasta']:>8,.0f} € × {t['tipo']}% = {t['cuota']:,.2f} €")
    return "\n".join(lines)


def format_iva(r: IVAResult) -> str:
    signo = "A INGRESAR" if r.a_ingresar > 0 else "A COMPENSAR"
    importe = r.a_ingresar if r.a_ingresar > 0 else r.a_compensar
    return (
        f"IVA T{r.trimestre}/{r.year}:\n"
        f"  IVA repercutido (cobrado):  {r.iva_repercutido:,.2f} €\n"
        f"  IVA soportado (pagado):     {r.iva_soportado:,.2f} €\n"
        f"  Resultado ({signo}):        {importe:,.2f} €"
    )


def format_modelo130(r: Modelo130Result) -> str:
    return (
        f"Modelo 130 — T{r.trimestre}/{r.year}:\n"
        f"  Ingresos acumulados: {r.ingresos_acumulados:,.2f} €\n"
        f"  Gastos acumulados:   {r.gastos_acumulados:,.2f} €\n"
        f"  Rendimiento neto:    {r.rendimiento_neto:,.2f} €\n"
        f"  20% a ingresar:      {r.base_pago:,.2f} €\n"
        f"  Pagos previos:       {r.pagos_anteriores:,.2f} €\n"
        f"  A INGRESAR:          {r.a_ingresar:,.2f} €"
    )
