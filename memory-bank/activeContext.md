# Active context

**Current focus:** Aletheia 3.0 foundations — sprint architectural primitives.

**Completado en sesión 2026-05-13 (fixes UI + launcher + session):**

- [x] `start.py` — banner v3.0; `_write_env_local(api_port)` escribe `REACT_APP_API_URL` en `.env.local` antes de `npm start`; `show_status()` ampliado con cognitive layer (trazas, divergencias, replays, degradación, TraceLearner, shadow mode)
- [x] `App.js` — `API_URL` lee `process.env.REACT_APP_API_URL` con fallback; `FatigueChip` en Navbar (color rojo/amarillo/verde según nivel); `status` inicial incluye `fatigue: null`; `ThinkingPanel` recibe `cogSessionId={chatSessionId}` (estable) separado de `sessionId` (por simulación)
- [x] `ThinkingPanel.jsx` — acepta `cogSessionId` prop; `CogStateWidget` usa `cogSessionId || sessionId`
- [x] `runtime.py /api/simulate` — `TraceBuilder` abierto al inicio, `_commit_sim_trace()` cierra y persiste en los 3 paths (action, conversacional, pipeline); `schedule_shadow()` lanzado al finalizar
- [x] `runtime.py /api/status` — devuelve `fatigue`, `traces_today`, `shadow_enabled`, `qualified_modes`, `degraded_modes`

**Completado en sesión 2026-05-13 (Frontend cognitivo):**

- [x] `CognitiveDashboard.jsx` — 4 secciones: CognitiveState meters, Mode Intelligence (modos/providers rankeados), Recent Traces (con replay inline), System Health (divergencias, degradación, replay stats)
- [x] `ThinkingPanel.jsx` — tabs "Eventos" / "Estado"; CogStateWidget con bars de energía/fatiga/coherencia + routing source badge + métricas de última traza
- [x] `Sidebar.jsx` — nueva entrada "◈ Cognitivo"
- [x] `App.js` — vista `cognitive` conectada + `domain` pasado a ThinkingPanel

**Completado en sesión 2026-05-13 (Cognitive Replay):**

- [x] `core/tracing/replay.py` — ReplayConfig, ReplayResult, CognitiveReplayer (single + batch), ReplayStore (SQLite)
- [x] runtime.py — 5 endpoints: `POST /api/traces/{id}/replay`, `POST /api/traces/{id}/replay/batch`, `GET /api/traces/{id}/replays`, `GET /api/replay/history`, `GET /api/replay/stats`
- [x] `system_init.py` — migración tabla `cognitive_replays` en startup
- [x] `core/tracing/__init__.py` — exports actualizados (DivergenceAnalyzer, CognitiveReplayer, replay_store)

**Completado en sesión 2026-05-13 (Adaptive Learning Loop):**

- [x] `core/cognition/insights.py` — ModeInsight + ProviderInsight (rank formula 4 ejes) + InsightCache (TTL 300s, thread-safe)
- [x] `core/cognition/trace_learner.py` — TraceLearner: SQL aggregation, recomendaciones mode/blend/provider, fallback transparente
- [x] `core/cognition/degradation.py` — StrategyDegradation: penalización (+0.10), recuperación (-0.08), auto-recovery (3 buenos), SQLite
- [x] `core/modes/observer.py` — 4 prioridades: learned_blend → learned_mode → blend_keyword → keyword_route
- [x] `core/routing/intelligence.py` — Tier 3.5: learned_provider preference sin romper jerarquía de seguridad
- [x] runtime.py — 5 endpoints: `/api/learning/insights`, `/api/learning/degradation`, `POST /api/learning/recompute`, `POST /api/learning/degradation/reset`, `/api/learning/recommend`
- [x] `system_init.py` — migración `strategy_degradation` en startup + limpieza de imports no usados

**Completado en sesión 2026-05-13 (Divergence Analysis + Blended Cognition):**

- [x] `core/tracing/divergence.py` — DivergenceScore (6 dim.), DivergenceReport, DivergenceAnalyzer; tabla `trace_divergences` SQLite
- [x] `core/tracing/store.py` — `analyzed_divergences()`, `divergence_stats()`, migración idempotente de `trace_divergences`
- [x] `core/modes/blend.py` — ModeBlend, BlendedModeExecutor (weighted_prompt + sequential), 6 presets
- [x] `core/modes/base.py` — `ModeResult.next_blend` field
- [x] `core/cognitive_state.py` — `can_afford_mode()` method
- [x] `core/modes/observer.py` — `_detect_blend()` con 6 patrones + keywords ampliados
- [x] `core/modes/registry.py` — `blend_and_activate()`, `route_and_activate()` prioriza blend
- [x] runtime.py — `/api/traces/divergences/analyzed`, `/api/traces/divergences/stats`, `POST /api/traces/analyze`, `/api/modes/status`, `/api/modes/blends`, `POST /api/modes/blend/test`

**Completado en sesión 2026-05-13 (Traceability Layer):**

- [x] `core/tracing/trace.py` — CognitiveTrace (frozen dataclass) + TraceBuilder (accumulator mutable)
- [x] `core/tracing/store.py` — TraceStore con SQLite (`cognitive_traces` table), queries: recent/get/summary/divergences
- [x] `core/tracing/context.py` — ContextVar async-safe + helpers: trace_routing, trace_mode, trace_fatigue, trace_memory
- [x] `core/tracing/shadow.py` — ShadowRunner: asyncio.create_task, sin bloqueo, toggle via `shadow_mode` pref o `ALETHEIA_SHADOW=1`
- [x] Integración en LLMRouter, FatigueEngine, ModeRegistry, MemoryBus — todos escriben a la traza activa
- [x] `/api/traces` (GET), `/api/traces/summary`, `/api/traces/divergences`, `/api/traces/{trace_id}` — 4 endpoints
- [x] `/api/chat` — crea TraceBuilder al inicio, llama `_commit_trace()` en los 3 paths de return, lanza shadow async

**Completado en sesión 2026-05-13 (arquitectura 3.0):**

- [x] `core/cognitive_state.py` — CognitiveState dataclass (energy, coherence, focus, token_budget, memory_pressure, fatigue, confidence, latency_tolerance)
- [x] `core/session_state.py` — SessionStateRegistry (per-session, thread-safe, global fallback)
- [x] `core/modes/base.py` — CognitiveMode ABC + ModeID enum + ModeResult
- [x] `core/modes/` — 11 modos implementados: OBSERVER, ANALYTICAL, STRATEGIC, KRONOS, CREATIVE, REFLECTIVE, GUARDIAN, EXECUTIVE, MEMORY_CURATOR, RESEARCHER, WORLD_MODEL
- [x] `core/modes/registry.py` — ModeRegistry singleton con `route_and_activate()`
- [x] `core/memory/bus.py` — MemoryBus singleton (SQLite + PALACE + semantic_graph + working_memory)
- [x] `core/routing/intelligence.py` — RoutingIntelligence (deterministic→local→free→premium, privacy check)
- [x] `core/fatigue/engine.py` — FatigueEngine con 9 event types, adaptations table, compress_context()
- [x] `core/llm/router.py` v1.2 — RoutingIntelligence + FatigueEngine integrados en generate()
- [x] `memory-bank/` — systemPatterns, techContext, projectbrief actualizados

**Arquitectura cognitiva activa (v1.2):**

```text
[Request + session_id]
  → get_state(session_id)                       ← CognitiveState
  → ModeRegistry.route_and_activate()
      → ObserverMode: keyword routing → ModeID
      → TargetMode._execute(context, state)
          → MemoryBus.retrieve/search()         ← unified memory
          → LLMRouter.generate()
              → RoutingIntelligence.decide()    ← tier selection
              → _call_configured(provider_hint)
              → FatigueEngine.record_llm_call() ← fatigue accounting
```

**Pipeline v1.x (sigue activo en paralelo):**

```text
orchestrator.process_request()
  → apply_aco → CEL → explorer → simulator → guardian → palace
```

Los modos 3.0 y el pipeline 1.x coexisten. La migración completa de agents/ a modes/ es el próximo paso.

**Completado en sesión 2026-05-17 (estabilización):**

- [x] `start.py` — fix UnicodeEncodeError en Windows (cp1252 → utf-8 reconfigure)
- [x] `core/schemas/decision_contract.py` — pydantic V2: `schema_extra` → `json_schema_extra`
- [x] `core/bootstrap/runtime.py` — `ModeRegistry.route_and_activate()` conectado al endpoint `/api/chat` via flag `use_v3_modes: true`; helper `_extract_reply` normaliza output de los 11 modos; fallback transparente a v1 si v3 falla
- [x] `core/palace/reader.py` — mapeo domain→área (`finanzas`→`VIDA`, `tecnico`→`TECNOLOGIA`, etc.); fallback a todas las áreas para dominios desconocidos; tag `_area` en cada entry
- [x] `core/palace/search.py` — typo `"tecnoogia"` → `"tecnologia"` corregido
- [x] RAG — 25/25 artifacts indexados, 450 chunks en ChromaDB; búsqueda semántica operativa (scores ~0.58)

**Completado en sesión 2026-05-18:**

- `semantic_graph.find_concepts()` — bug silencioso corregido; MemoryBus.search() operativo
- Toggle `use_v3_modes` — Settings → Sistema; persiste en preferences.json; /api/chat lo lee
- ACO v3 MetaCortex — EMA policy_stats por sesión; ObserverMode prioridades 0/1; feedback desde runtime
- FatigueEngine en voz — session_id único por sesión de voz; propagado a todos los helpers
- Google Calendar + Telegram en UI — Settings "Calendario" y "Telegram"; sin edición manual de JSON
- SetupDashboard — vista "Inicio"; 8 sistemas con estado; badge en Sidebar; /api/setup/status
- UseCasesPage — vista "Capacidades"; 9 casos con velocidad/disponibilidad; ejemplos clicables
- ConsolidationEngine — sueño cognitivo; raw_buffer + motor con run/stop/schedule; UI en CognitiveDashboard
- Modo diferido — toggle UI; MemoryBus.store() encola en raw_buffer cuando activo

**Completado en sesión 2026-05-19 — Sistema de Fichas de Proyecto:**

- `core/projects/__init__.py` + `manager.py` + `analyzer.py` — nuevo módulo PROJECTS
- `ProjectManager` — CRUD SQLite (`memory/data/projects.db`), tabla `project_cards`
- 9 tipos de proyecto: `life_decision`, `career`, `home_improvement`, `purchase`, `financial_goal`, `health_wellness`, `education`, `business`, `other`
- Dimensiones capturadas: tiempo, económico (coste/beneficio/ROI/ahorro previo), psicológico, físico, relacional
- `compute_score()` — puntuación global -10..+10 ponderada (fin 40%, psy 30%, phys 15%, rel 15%)
- `get_recommendation()` — proceed / defer / review / discard
- `analyze_with_llm()` — análisis narrativo asíncrono con LLMRouter
- 9 endpoints `/api/projects/*` en runtime.py (CRUD + reminders + balance + types + analyze)
- `ProjectsPage.jsx` — vista completa: lista con filtros, tarjetas, formulario multi-tab (básico/dimensiones/pros-contras), panel de detalle, balance de portafolio, análisis LLM inline
- Sidebar + App.js actualizados — entrada "⚖️ Proyectos"

**Completado en sesión 2026-05-19 — Detección de patrones cognitivos (paso 6 del sueño):**

- `core/cognition/pattern_detector.py` — PatternDetector singleton; 6 heurísticas SQL puras sobre `cognitive_traces` + `memory_nodes`; tabla `cognitive_patterns` en aletheia.db; `detect(since_hours)`, `get_patterns()`, `mark_read()`, `mark_all_read()`, `unread_count()`
- Patrones detectados: `recurring_topic`, `dominant_mode`, `new_concept`, `cross_domain_link`, `high_fatigue_session`, `low_confidence_zone`
- `system_init.py` — migración idempotente de `cognitive_patterns` en startup
- `consolidation_engine.py` — paso 6 añadido: `pattern_detector.detect(since_hours=48)` tras compress; `patterns_found` en stats
- `runtime.py` — 5 endpoints: `GET /api/consolidation/patterns`, `GET .../unread_count`, `POST .../mark_all_read`, `POST .../{id}/mark_read`, `POST .../detect`
- `CognitiveDashboard.jsx` — `PatternsSubSection` dentro de SleepSection Card; lista de patrones con icono, badge "nuevo", barra de relevancia; botones "Detectar ahora" y "Marcar todo leído"

**Completado en sesión 2026-05-19 — Migración agents/ → core/pipeline/:**

- `core/pipeline/__init__.py` + `explorer.py` + `simulator.py` + `guardian.py` — lógica idéntica, nueva ubicación canónica
- `core/orchestrator.py` — `from agents import` → `from core.pipeline import`
- `core/modes/guardian.py` — `from agents.guardian import` → `from core.pipeline.guardian import`; variable `domain` sin usar eliminada
- `tests/system/test_full_pipeline.py` — mocks actualizados a `core.pipeline.*`; import directo eliminado (unused)
- `tests/test_guardian_behavior.py`, `test_changes.py`, `test_explorer_profile.py`, `test_simulator_profile_fallback.py` — imports actualizados
- `agents/` — directorio eliminado por completo (incluidos `simulator_helpers.py` y `_build_simulator_helpers.py` que eran código muerto)

**Completado en sesión 2026-05-19 — Wake word con openWakeWord:**

- `core/voice/listener.py` — `WakeWordDetector` refactorizado: backend `oww_custom` (openWakeWord + modelo personalizado) con fallback a `whisper` (Whisper-tiny, comportamiento anterior); selección automática en `start()`; propiedad `backend` expuesta; chunks de 80ms en lugar de 2s
- `core/voice/wake_trainer.py` — entrenador completo: genera clips TTS con Piper/espeak/gTTS, normaliza a 16kHz, entrena con openWakeWord, guarda `PALACE/voice_models/oww/aletheia.onnx`; instrucciones de Colab si falla el entrenamiento automático
- `start.py` — flag `--train-wake-word` añadido

**Uso del wake word:**

```bash
pip install openwakeword torch torchaudio librosa soundfile
python start.py --train-wake-word    # genera aletheia.onnx (~5-15 min)
python start.py --voice --always-on  # usa openWakeWord automáticamente
```

**Backlog adicional:**

- Pruebas end-to-end del sistema completo
