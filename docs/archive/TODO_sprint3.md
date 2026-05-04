# Sprint 3 - DecisionReport Finalización (Fase 3A/B/C)

## Plan Aprobado (prioridad: DecisionReport schema lock primero)

**Fase 1: DecisionReport Schema Lock (CRÍTICO)**
- [x] `core/schemas/decision_contract.py`: Crear schema v1.0 con validación estricta (pydantic), todos campos obligatorios/controlados, fallback mapping. ✅


**Fase 2: Simulator + llm_explain**
- [x] `agents/simulator.py`: Refactor para retornar SOLO DecisionReport completo (incluir llm_explanation NEW con Ollama). ✅
- [x] `ai/prompts.py`: Prompt para llm_explain/scenario_description. ✅ (usando _generate_llm_explanation)


**Fase 3: Guardian alignment**
- [x] `agents/guardian.py`: Validar 100% contra DecisionReport schema.

**Fase 4: UI**
- [x] `aletheia-ui/src/App.js`: Consumir y mostrar DecisionReport fields.

**Fase 5: Integraciones**
- [x] `core/orchestrator.py`: Propagación OK.
- [x] Tests updated.

**Sprint 3 ✅ Complete**

**Dependencias**: ai/ollama_client.py, memory influence ya implementado.

**Next**: Empezar por schema lock.
