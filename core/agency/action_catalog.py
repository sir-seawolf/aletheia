"""
Action catalog — defines every action Aletheia can take autonomously.

Each action has:
  id          — unique key used by executor
  name        — human-readable label (spoken in confirmations)
  risk        — "low" | "medium" | "high"  (only low allowed in Sprint 7)
  triggers    — list of keyword substrings that activate this action
  needs_arg   — whether the action requires an extracted argument from the utterance

Sprint 7 scope: read-only + PALACE write actions only.
Destructive actions (delete, git push, external APIs) reserved for Sprint 7b.
"""

from dataclasses import dataclass, field


@dataclass
class ActionDef:
    id: str
    name: str
    risk: str
    triggers: list[str]
    needs_arg: bool = False
    arg_hint: str = ""          # shown in confirmation if needs_arg


CATALOG: list[ActionDef] = [
    ActionDef(
        id="memory_query",
        name="consulta de memoria",
        risk="low",
        triggers=[
            "que recuerdas", "qué recuerdas",
            "sabes sobre", "tienes informacion", "tienes información",
            "que sabes de", "qué sabes de",
            "busca en tu memoria", "busca en memoria",
        ],
        needs_arg=True,
        arg_hint="tema a buscar",
    ),
    ActionDef(
        id="create_note",
        name="crear nota en memoria",
        risk="low",
        triggers=[
            "crea una nota", "crea nota",
            "guarda esto", "guarda que",
            "anota", "registra esto", "registra que",
            "añade a tu memoria", "agrega a tu memoria",
        ],
        needs_arg=True,
        arg_hint="contenido de la nota",
    ),
    ActionDef(
        id="system_status",
        name="estado del sistema",
        risk="low",
        triggers=[
            "como estas", "cómo estás",
            "estado del sistema", "estado de aletheia",
            "cuantos registros", "cuántos registros",
            "cuanta memoria", "cuánta memoria tienes",
            "dame un resumen de ti",
        ],
    ),
    ActionDef(
        id="emotional_report",
        name="informe emocional",
        risk="low",
        triggers=[
            "como te sientes", "cómo te sientes",
            "cual es tu estado", "cuál es tu estado",
            "que sientes", "qué sientes",
            "como te encuentras", "cómo te encuentras",
            "estado emocional",
        ],
    ),
    ActionDef(
        id="read_file",
        name="leer archivo",
        risk="low",
        triggers=[
            "lee el archivo", "leer el archivo",
            "muestrame el archivo", "muéstrame el archivo",
            "abre el archivo", "muestra el contenido de",
        ],
        needs_arg=True,
        arg_hint="ruta del archivo",
    ),
    ActionDef(
        id="internal_debate",
        name="debate cognitivo interno",
        risk="low",
        triggers=[
            "debate interno sobre", "debate sobre",
            "analiza desde todas las perspectivas",
            "que dicen tus cerebros", "qué dicen tus cerebros",
            "que piensan tus perspectivas", "qué piensan tus perspectivas",
            "debate contigo mismo", "debatete sobre",
            "multiples perspectivas sobre", "múltiples perspectivas sobre",
        ],
        needs_arg=True,
        arg_hint="tema del debate",
    ),
    ActionDef(
        id="civilization_status",
        name="estado de la civilizacion cognitiva",
        risk="low",
        triggers=[
            "cuantos debates has tenido", "cuántos debates has tenido",
            "historial de debates", "resumen de tu civilizacion",
            "resumen de tu civilización", "como va tu ecosistema",
            "cómo va tu ecosistema",
        ],
    ),
    ActionDef(
        id="ingest_doc",
        name="leer e ingestar documento",
        risk="low",
        triggers=[
            "analiza el documento", "analiza el archivo",
            "lee e incorpora", "ingesta el archivo", "ingesta el documento",
            "procesa el documento", "procesa el archivo",
            "incorpora el archivo", "incorpora el documento",
            "carga el documento", "carga el archivo",
        ],
        needs_arg=True,
        arg_hint="ruta o nombre del archivo",
    ),
    ActionDef(
        id="drive_search",
        name="buscar en drives locales",
        risk="low",
        triggers=[
            "busca en drive", "busca en mi drive",
            "busca en onedrive", "busca en mis documentos",
            "encuentra en drive", "encuentra en onedrive",
            "busca el documento", "busca el archivo en drive",
        ],
        needs_arg=True,
        arg_hint="término de búsqueda",
    ),
    ActionDef(
        id="drive_browse",
        name="explorar drives locales",
        risk="low",
        triggers=[
            "muestra mi drive", "muestra mis drives",
            "que hay en drive", "qué hay en drive",
            "explora onedrive", "lista mis carpetas",
            "que carpetas tienes", "qué carpetas tienes",
        ],
    ),
    ActionDef(
        id="gmail_scan",
        name="escanear Gmail para facturas",
        risk="low",
        triggers=[
            "escanea el correo", "escanea mi correo",
            "escanea el ejercicio fiscal", "escanea gmail",
            "revisa el correo", "busca facturas en el correo",
            "actualiza mis facturas", "importa facturas de gmail",
            "escanea el año fiscal",
        ],
        needs_arg=True,
        arg_hint="año fiscal (ej: 2024) o rango de fechas",
    ),
    ActionDef(
        id="financial_summary",
        name="resumen financiero",
        risk="low",
        triggers=[
            "cuanto gasté", "cuánto gasté",
            "resumen de gastos", "resumen financiero",
            "cuanto he gastado", "cuánto he gastado",
            "mis facturas", "total de facturas",
            "gastos del año", "gastos del ejercicio",
        ],
        needs_arg=True,
        arg_hint="año (ej: 2024) o vacío para todos",
    ),
    ActionDef(
        id="artifact_stats",
        name="estadísticas de artefactos",
        risk="low",
        triggers=[
            "cuantos artefactos", "cuántos artefactos",
            "que documentos tienes", "qué documentos tienes",
            "resumen del palacio", "que has almacenado",
            "qué has almacenado",
        ],
    ),
    ActionDef(
        id="web_search",
        name="búsqueda web",
        risk="low",
        triggers=[
            "busca en internet", "busca en la web", "busca en google",
            "busca online", "busca información sobre",
            "qué dice internet", "noticias sobre",
            "cuánto vale", "precio de", "cotización de",
        ],
        needs_arg=True,
        arg_hint="término a buscar",
    ),
    ActionDef(
        id="url_ingest",
        name="leer página web",
        risk="low",
        triggers=[
            "lee esta página", "lee esta url", "lee esta web",
            "analiza esta página", "analiza esta url",
            "ingesta esta página", "abre este enlace",
        ],
        needs_arg=True,
        arg_hint="URL de la página",
    ),
    ActionDef(
        id="bank_statement",
        name="analizar extracto bancario",
        risk="low",
        triggers=[
            "analiza el extracto", "analiza mi extracto",
            "procesa el extracto bancario", "importa el extracto",
            "carga el extracto", "lee el extracto bancario",
        ],
        needs_arg=True,
        arg_hint="ruta del archivo CSV/XLSX",
    ),
]

# Fast lookup by id
BY_ID: dict[str, ActionDef] = {a.id: a for a in CATALOG}
