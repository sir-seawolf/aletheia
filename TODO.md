# TODO.md - Ejecución del Plan Refactor Cognitivo (Aprobado por Usuario)

## Estado Anterior (Completado)
- [x] Step 1: Create TODO.md 
- [x] Step 2: Timeout/error handling in orchestrator
- [x] Step 3: Test orchestrator sample
- [x] Step 4: No blocking on Ollama down
- [x] Step 5: Skip risk_engine timeout

## FASE 1 — CIERRE COGNITIVO (Prioridad Máxima - Usuario Feedback)
1. [x] **Unificar DecisionReport como contrato único** (simulator.py)
   - AI path → _build_decision_report_from_ai()
   - Siempre return DecisionReport.to_dict()
   - Add _calculate_overall_confidence()
   - Enhanced snapshot (facts_count, gaps_count, temporal_data)
2. [x] **Simulator híbrido real** (simulator.py)
   - Validar JSON structure
   - Add global 'insight' from LLM
   - Add 'scenario_count'
3. [x] **Guardian fuerte** (guardian.py)
   - ≥2 escenarios mandatory high-risk (block if not)
   - Contradiction/diversity check
   - Enforce min quality
   - New checks: confidence/insight length/contradiction
   - block, severity, recommendation, confidence_adjust

## FASE 2 — VALIDACIÓN
4. [ ] Tests de comportamiento (new test_simulator_hybrid.py)
   - High-risk → ≥2 scenarios
   - No data → low confidence + gaps
   - Profile diffs → varied output

## FASE 3 — MEMORIA INTELIGENTE (Post-Fase1)
5. [ ] Embeddings + semantic search

## FASE 4 — UI/PROD
6. [ ] UI enhancements
7. [ ] Docker/CI

## Progreso Actual: FASE 1 Step 1 (simulator.py refactor)

**Siguiente acción**: Editar agents/simulator.py

