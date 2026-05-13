"""
KRONOS enricher — resolves clean merchant names, refined categories and tags
from raw BBVA transaction data (concept + observation).

All logic is deterministic (no LLM). Runs once when building financial_cache.
"""

import re

_ADEUDO_MENSUAL    = "Adeudo mensual tarjeta"
_RETIRADA_EFECTIVO = "Retirada efectivo"

# ── Merchant lookup: keyed by lowercase substring ─────────────────────────
# Value: (display_name, category, tags)
_MERCHANT_MAP: dict[str, tuple[str, str, list[str]]] = {
    # Streaming / subscriptions
    "netflix":          ("Netflix",           "suscripcion", ["mensual", "ocio"]),
    "spotify":          ("Spotify",           "suscripcion", ["mensual", "ocio"]),
    "amazon prime":     ("Amazon Prime",      "suscripcion", ["mensual", "ocio"]),
    "disney":           ("Disney+",           "suscripcion", ["mensual", "ocio"]),
    "hbo":              ("HBO/Max",            "suscripcion", ["mensual", "ocio"]),
    "youtube":          ("YouTube Premium",   "suscripcion", ["mensual", "ocio"]),
    "apple":            ("Apple",             "suscripcion", ["mensual"]),
    "xbox":             ("Xbox",              "suscripcion", ["mensual", "ocio"]),
    "playstation":      ("PlayStation",       "suscripcion", ["variable", "ocio"]),
    # Microsoft / Google
    "microsoft":        ("Microsoft",         "suscripcion", ["mensual"]),
    "google play":      ("Google Play",       "suscripcion", ["variable"]),
    "google one":       ("Google One",        "suscripcion", ["mensual"]),
    "google":           ("Google",            "suscripcion", ["variable"]),
    # Telecom / recibos
    "movistar":         ("Movistar",          "recibo",      ["mensual", "fijo"]),
    "telefonica":       ("Telefónica",        "recibo",      ["mensual", "fijo"]),
    "orange":           ("Orange",            "recibo",      ["mensual", "fijo"]),
    "vodafone":         ("Vodafone",          "recibo",      ["mensual", "fijo"]),
    "jazztel":          ("Jazztel",           "recibo",      ["mensual", "fijo"]),
    # Seguros
    "mapfre":           ("Mapfre",            "seguro",      ["anual", "fijo"]),
    "axa":              ("AXA",               "seguro",      ["anual", "fijo"]),
    "allianz":          ("Allianz",           "seguro",      ["anual", "fijo"]),
    "mutua":            ("Mutua",             "seguro",      ["mensual", "fijo"]),
    "adeslas":          ("Adeslas",           "seguro",      ["mensual", "fijo"]),
    "bbvaplanestarseguro": ("BBVA Estarseguro","seguro",     ["mensual", "fijo"]),
    "estarseguro":      ("BBVA Estarseguro",  "seguro",      ["mensual", "fijo"]),
    # Supermercados
    "mercadona":        ("Mercadona",         "supermercado",["variable", "esencial"]),
    "carrefour":        ("Carrefour",         "supermercado",["variable", "esencial"]),
    "lidl":             ("Lidl",              "supermercado",["variable", "esencial"]),
    "aldi":             ("Aldi",              "supermercado",["variable", "esencial"]),
    "eroski":           ("Eroski",            "supermercado",["variable", "esencial"]),
    "dia ":             ("Dia",               "supermercado",["variable", "esencial"]),
    "alcampo":          ("Alcampo",           "supermercado",["variable", "esencial"]),
    # Transporte / gasolina
    "repsol":           ("Repsol",            "transporte",  ["variable"]),
    "cepsa":            ("Cepsa",             "transporte",  ["variable"]),
    "galp":             ("Galp",              "transporte",  ["variable"]),
    "bp ":              ("BP",                "transporte",  ["variable"]),
    "gasolinera":       ("Gasolinera",        "transporte",  ["variable"]),
    "siscarburantes":   ("Siscarburantes",    "transporte",  ["variable"]),
    "renfe":            ("Renfe",             "transporte",  ["variable"]),
    "metro":            ("Metro",             "transporte",  ["variable"]),
    "cabify":           ("Cabify",            "transporte",  ["variable"]),
    "uber":             ("Uber",              "transporte",  ["variable"]),
    "blablacar":        ("BlaBlaCar",         "transporte",  ["variable"]),
    "autopista":        ("Autopista",         "transporte",  ["variable"]),
    "peaje":            ("Peaje",             "transporte",  ["variable"]),
    "castellana":       ("Castellana Autopistas","transporte",["variable"]),
    # Restaurantes
    "telepizza":        ("Telepizza",         "restaurante", ["variable"]),
    "mcdonalds":        ("McDonald's",        "restaurante", ["variable"]),
    "mcdonald":         ("McDonald's",        "restaurante", ["variable"]),
    "burger":           ("Burger King",       "restaurante", ["variable"]),
    "pizz":             ("Pizzería",          "restaurante", ["variable"]),
    "sushi":            ("Sushi",             "restaurante", ["variable"]),
    # Ocio / compras
    "amazon":           ("Amazon",            "ocio",        ["variable"]),
    "booking":          ("Booking.com",       "ocio",        ["variable"]),
    "airbnb":           ("Airbnb",            "ocio",        ["variable"]),
    "fnac":             ("Fnac",              "ocio",        ["variable"]),
    "corte ingles":     ("El Corte Inglés",   "ocio",        ["variable"]),
    "zara":             ("Zara",              "ocio",        ["variable"]),
    "primark":          ("Primark",           "ocio",        ["variable"]),
    "decathlon":        ("Decathlon",         "ocio",        ["variable"]),
    "ikea":             ("IKEA",              "ocio",        ["variable"]),
    "mediamarkt":       ("Media Markt",       "ocio",        ["variable"]),
    "loterias":         ("Loterías",          "ocio",        ["variable"]),
    "tulotero":         ("Tulotero",          "ocio",        ["variable"]),
    # Salud
    "farmacia":         ("Farmacia",          "salud",       ["variable"]),
    "dentista":         ("Dentista",          "salud",       ["variable"]),
    "hospital":         ("Hospital",          "salud",       ["variable"]),
    "medico":           ("Médico",            "salud",       ["variable"]),
    # Impuestos
    "hacienda":         ("Hacienda/AEAT",     "impuesto",    ["anual"]),
    "agencia tributaria":("Agencia Tributaria","impuesto",   ["anual"]),
    "ayuntamiento":     ("Ayuntamiento",      "impuesto",    ["anual"]),
    # Transferencias
    "bizum":            ("Bizum",             "transferencia",["variable"]),
    "paypal":           ("PayPal",            "transferencia",["variable"]),
    "transferencia":    ("Transferencia",     "transferencia",["variable"]),
    # Nómina
    "nomina":           ("Nómina",            "nomina",      ["mensual", "fijo", "ingreso"]),
    "nómina":           ("Nómina",            "nomina",      ["mensual", "fijo", "ingreso"]),
    "salary":           ("Salario",           "nomina",      ["mensual", "fijo", "ingreso"]),
    # Recibos fijos
    "adeudomensual":    (_ADEUDO_MENSUAL, "recibo",  ["mensual", "fijo"]),
    "adeudo mensual":   (_ADEUDO_MENSUAL, "recibo",  ["mensual", "fijo"]),
    "comunidad":        ("Comunidad propietarios","recibo",  ["mensual", "fijo"]),
    "hipoteca":         ("Hipoteca",          "recibo",      ["mensual", "fijo"]),
    "alquiler":         ("Alquiler",          "recibo",      ["mensual", "fijo"]),
    # Préstamo / crédito
    "disposiciondeprestamo": ("Disposición préstamo","transferencia",["especial"]),
    "prestamo":         ("Préstamo",           "transferencia",["especial"]),
    "credito":          ("Crédito",            "transferencia",["especial"]),
    # Traspasos y ahorro
    "traspaso":         ("Traspaso/Ahorro",    "transferencia",["movimiento"]),
    # Cajero / efectivo
    "cajero":           ("Cajero automático",    "efectivo",     ["variable"]),
    "efectivo":         (_RETIRADA_EFECTIVO,   "efectivo",     ["variable"]),
    "ret.efectivo":     (_RETIRADA_EFECTIVO,   "efectivo",     ["variable"]),
    "adebito":          (_RETIRADA_EFECTIVO,   "efectivo",     ["variable"]),
    # Apuntes varios
    "apunteporoperaciones": ("Apunte varios",  "otro",         ["variable"]),
    "apuntes":          ("Apunte varios",      "otro",         ["variable"]),
    # Alquiler / vivienda
    "alquiler":         ("Alquiler",           "recibo",       ["mensual", "fijo"]),
    "comunidad":        ("Comunidad propietarios","recibo",    ["mensual", "fijo"]),
    # Gasolinera específica (sin card number)
    "siscarburantes":   ("Siscarburantes",     "transporte",   ["variable"]),
    "rotonda":          ("Gasolinera Rotonda", "transporte",   ["variable"]),
    "cedipsa":          ("Cedipsa",            "transporte",   ["variable"]),
    # Restaurantes específicos Cuenca
    "bar ":             ("Bar",                "restaurante",  ["variable"]),
    "meson":            ("Mesón",              "restaurante",  ["variable"]),
    "estanco":          ("Estanco/Tabaco",     "ocio",         ["variable"]),
    # Deporte / salud
    "deportivo":        ("Centro deportivo",   "salud",        ["variable"]),
    "gimnasio":         ("Gimnasio",           "salud",        ["mensual"]),
    "fisio":            ("Fisioterapia",       "salud",        ["variable"]),
}

# Generic BBVA concatenated concept → readable name
_CONCEPT_MAP: dict[str, tuple[str, str, list[str]]] = {
    "PAGOCONTARJETAENGASOLINERAS":
        ("Gasolinera (tarjeta)",          "transporte",  ["variable"]),
    "PAGOCONTARJETAENRESTAURANTESYCAFETERIAS":
        ("Restaurante/Cafetería",         "restaurante", ["variable"]),
    "PAGOCONTARJETAENSUPERMERCADOS":
        ("Supermercado",                  "supermercado",["variable", "esencial"]),
    "PAGOCONTARJETAENAUTOPISTASYPEAJES":
        ("Autopista/Peaje",               "transporte",  ["variable"]),
    "PAGOCONTARJETADECOMPRASADISTANCIAYSUSCRIPCIONES":
        ("Compra online/Suscripción",     "suscripcion", ["variable"]),
    "PAGOCONTARJETAENAGENCIASDEVIAJE":
        ("Agencia de viaje",              "ocio",        ["variable"]),
    "PAGOCONTARJETAENCOMERCIOS":
        ("Comercio",                      "ocio",        ["variable"]),
    "PAGOCONTARJETAENSERVICIOSDIGITALES":
        ("Servicio digital",              "suscripcion", ["variable"]),
    "PAGOCONTARJETAENSALUD":
        ("Salud (tarjeta)",               "salud",       ["variable"]),
    "PAGOCONTARJETAENSEGUROSYFINANZAS":
        ("Seguros/Finanzas",              "seguro",      ["variable"]),
    "PAGOCONTARJETAENENTRETENIMIENTOYOCIO":
        ("Entretenimiento/Ocio",          "ocio",        ["variable"]),
    "CARGOPORCOMPRACONTARJETAENCOMERCIOS":
        ("Comercio (cargo tarjeta)",      "ocio",        ["variable"]),
    "VARIOSSERVICIOC.LOTERIAS":
        ("Loterías",                      "ocio",        ["variable"]),
    "ADEUDOMENSUALDETARJETA":
        (_ADEUDO_MENSUAL,                 "recibo",      ["mensual", "fijo"]),
    "ABONOPORDISPOSICIONDEPRESTAMO/CREDITO":
        ("Disposición préstamo/crédito",  "transferencia",["especial"]),
    "TRANSFERENCIAS":
        ("Transferencia",                 "transferencia",["variable"]),
    "BIZUM":
        ("Bizum",                         "transferencia",["variable"]),
}

_CARD_NR_RE = re.compile(r"^\d{14,19}")


def _clean_observation(obs: str) -> str:
    """Extract merchant name from BBVA observation line (card nr + merchant)."""
    if not obs:
        return ""
    clean = _CARD_NR_RE.sub("", obs).strip()
    # Remove trailing 2-letter country code
    clean = re.sub(r"\s+[A-Z]{2}\s*$", "", clean).strip()
    return clean


def _lookup(text: str) -> tuple[str, str, list[str]] | None:
    """Check _MERCHANT_MAP for the first matching key (longest wins)."""
    lower = text.lower()
    best: tuple[str, str, list[str]] | None = None
    best_len = 0
    for key, val in _MERCHANT_MAP.items():
        if key in lower and len(key) > best_len:
            best = val
            best_len = len(key)
    return best


def enrich(txn: dict) -> dict:
    """
    Return *txn* with added keys: merchant, category (refined), tags.
    Input keys used: concept, observation, amount, category (bank_parser default).
    """
    concept  = txn.get("concept", "")
    obs      = txn.get("observation", "")
    amount   = txn.get("amount", 0.0)

    merchant_raw = _clean_observation(obs) if obs else concept

    # 1. Try exact concept map (BBVA generic payment types)
    match = _CONCEPT_MAP.get(concept.upper().strip())
    if match:
        display, category, tags = match
        # Refine merchant name from observation if available
        obs_clean = _clean_observation(obs)
        if obs_clean:
            lookup = _lookup(obs_clean)
            if lookup:
                display, category, tags = lookup
            else:
                display = obs_clean.title() or display
        return {**txn, "merchant": display, "category": category, "tags": tags}

    # 2. Try merchant lookup on observation first, then concept
    for text in (merchant_raw, concept):
        lookup = _lookup(text)
        if lookup:
            display, category, tags = lookup
            return {**txn, "merchant": display, "category": category, "tags": tags}

    # 3. Fallback: use clean observation or concept as merchant name
    merchant = _clean_observation(obs).title() if obs else concept.title()
    category = txn.get("category", "otro")
    tags = ["ingreso"] if amount > 0 else ["variable"]
    return {**txn, "merchant": merchant, "category": category, "tags": tags}
