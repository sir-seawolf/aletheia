# Plan de mejoras - Feedback usuario

## Archivos a modificar

### 1. `core/orchestrator.py`
- Agregar contratos de salida: `EXPLORATION_SCHEMA`, `SIMULATION_SCHEMA`
- Documentar estructuras esperadas entre pasos del pipeline

### 2. `agents/simulator.py`
- Integrar Ollama en `_build_scenario_description()` para generar descripciones reales
- Mantener fallback al texto estructurado si Ollama falla
- Usar nuevo prompt especializado en `ai/prompts.py`

### 3. `core/context.py`
- Agregar método `summary()` para debugging rápido en 1 línea

### 4. `agents/guardian.py`
- Validar escenarios < 2 cuando riesgo es alto (mensaje: "Falta comparación de escenarios en riesgo alto")
- Validar ausencia de supuestos (mensaje: "No hay supuestos explícitos")
- "Tensar" el sistema con validaciones más estrictas

### 5. `api/main.py`
- Agregar endpoint raíz `GET /` que retorne info del sistema

### 6. `ai/prompts.py`
- Agregar `scenario_description_prompt()` para generar descripciones de escenarios con Ollama

## Dependencias
- `ai/ollama_client.py` ya está disponible
- `config.py` define modelo y temperatura

