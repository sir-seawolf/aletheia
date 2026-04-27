# Sprint 3 - DecisionReport Finalización (Fase 3A/B/C)

## Plan Aprobado (prioridad: DecisionReport schema lock primero)

**Fase 1: DecisionReport Schema Lock (CRÍTICO)**
- [x] `core/schemas/decision_contract.py`: Crear schema v1.0 con validación estricta (pydantic), todos campos obligatorios/controlados, fallback mapping. ✅


**Fase 2: Simulator + llm_explain**
- [x] `agents/simulator.py`: Refactor para retornar SOLO DecisionReport completo (incluir llm_explanation NEW con Ollama). ✅
- [x] `ai/prompts.py`: Prompt para llm_explain/scenario_description. ✅ (usando _generate_llm_explanation)


**Fase 3: Guardian alignment**
- [ ] `agents/guardian.py`: Validar 100% contra DecisionReport schema (escenarios>=2 en riesgo alto, supuestos explícitos, etc.).

**Fase 4: UI**
- [ ] `aletheia-ui/src/App.js`: Consumir y mostrar DecisionReport fields (Snapshot, Escenarios, Riesgos, Insight, Confianza, etc.).

**Fase 5: Integraciones**
- [ ] `core/orchestrator.py`: Asegurar propagación completa de DecisionReport.
- [ ] Tests: /simulate retorna DecisionReport válido, UI lo renderiza.

**Dependencias**: ai/ollama_client.py, memory influence ya implementado.

**Next**: Empezar por schema lock.
