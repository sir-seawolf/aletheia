"""El corazón del sistema. Genera escenarios, explica supuestos, compara opciones."""

import json
from typing import Dict, Any, List, Optional
from core.context import Context
from core.event_bus import build_event, emit_event
from ai.ollama_client import generate
from ai.prompts import simulation_prompt
from core.models import DecisionReport

