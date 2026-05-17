# Progress

## What works

### Core pipeline (v1.x — active)

- Pipeline cognitivo end-to-end: API → ACO → CEL → explorer → simulator → guardian → contract_lock → memory
- LLMRouter v1.2 con multi-provider: Ollama → Claude → OpenAI → DeepSeek → Groq → Mistral → Mock
- RoutingIntelligence integrado: selección dinámica de tier (local/free/premium) por fatiga, latencia, privacidad
- FatigueEngine integrado: registra cada LLM call y error de pipeline en CognitiveState de sesión
- TURBO mode: specialist / race / panel con probe de latencia en tiempo real
- FastAPI + SQLite + Ollama integrados y verificados

### Aletheia 3.0 foundations (2026-05-13)

- `CognitiveState` — 8 campos vitales, derived properties (preferred_depth, preferred_model_tier, is_fatigued, is_critical)
- `SessionStateRegistry` — estado cognitivo por session_id, thread-safe, fallback global
- `CognitiveMode` base — ABC con activate(), can_activate(), fatigue accounting automático
- 11 modos cognitivos — OBSERVER, ANALYTICAL, STRATEGIC, KRONOS, CREATIVE, REFLECTIVE, GUARDIAN, EXECUTIVE, MEMORY_CURATOR, RESEARCHER, WORLD_MODEL
- `ModeRegistry` — singleton, `route_and_activate()` usa OBSERVER para routing inteligente
- `MemoryBus` — capa unificada: SQLite episódico + PALACE + semantic_graph + working_memory + deduplicación
- `RoutingIntelligence` — prioridad: deterministic→local→free→premium; privacy check; complejidad por tarea
- `FatigueEngine` — 9 event types, compounding, 5 niveles de adaptación, compress_context(), should_postpone()

### PALACE (memoria episódica)

- classifier, reader, writer, search funcionales
- Consolidador PALACE → semantic_graph integrado en MemoryCuratorMode

### HESTIA (motor de metas financieras)

- `core/hestia/`: memory.py, observer.py, analyzer.py, engine.py
- SQLite hestia.db con 4 tablas; meta inicial "Clase media España 30k€/año"
- 6 endpoints en `/api/hestia/*`

### Voz offline

- `core/voice/`: listener.py (faster-whisper + silero-VAD gate), speaker.py (Piper TTS, interrumpible), session.py
- Voz `es_ES-sharvard-medium` (femenina)
- Timeout Ollama 45s para modo voz
- TTS interrumpible con ENTER

### KRONOS (modo financiero)

- `core/kronos/`: analyzer.py, context_builder.py, financial_cache.py, persona.py, detector.py, enricher.py
- quick_analysis() para voz (2-4 frases), full_analysis() para informe completo
- Integrado como `KronosMode` en el sistema de modos 3.0

### Memoria profunda

- `core/memory/`: semantic_graph.py, emotional_tagger.py, working_memory.py, consolidator.py
- `MemoryBus` agrega todos los backends

### Docs e ingesta

- PDF, DOCX, TXT, MD, CSV, URL, Google Drive online/local, OneDrive, Gmail
- artifact_store.py (SHA-256 + versionado), financial_extractor.py, bank_parser.py (11 categorías)
- DuckDuckGo search sin API key

### UI

- Layout split: Sidebar + Main + ThinkingPanel (WebSocket con auto-reconnect)
- CommandPalette.jsx (Ctrl+K), ChatView.jsx, DocBrowser.jsx, SettingsPage.jsx
- VoiceInput.jsx, BrainLoader.jsx reactivo al agente activo

### Launcher

- `start.py` — único punto de entrada con flags --voice --demo --reset --status --stop

## Backlog / próximos pasos

- **Toggle v3 modes en UI** — exponer `use_v3_modes` en Settings o ThinkingPanel
- **Google Calendar** — completar OAuth en browser
- **Telegram** — token en `PALACE/config/telegram.json`
- **ACO v3 MetaCortex** — implementar meta_cortex.py (actualmente vacío)

## What works (actualizado 2026-05-17 — sesión 2)

- **AnalyticalMode** — absorbe lógica de `agents/explorer`: keyword memory search, extracción LLM con fallback JSON/regex/texto, gap detection, confidence scoring. Output enriquecido: `{analysis, steps, facts, gaps, confidence}`.
- **StrategicMode** — absorbe lógica de `agents/simulator`: generación de escenarios LLM con fallback JSON/regex/genérico, insight estratégico, output: `{plan, scenarios, risks, assumptions, insight}`.
- **agents/** — marcados `Legacy v1 compat`; pipeline v1 intacto.
- **WakeWordDetector** — `core/voice/listener.py`; hilo daemon: VAD gate + whisper tiny; detecta "Aletheia" y variantes; `start(callback)` / `stop()`.
- **`run_voice_session_always_on()`** — sesión siempre-activa en `core/voice/session.py`; fallback a push-to-talk si sounddevice no disponible.
- **`start.py --always-on`** — nuevo flag; combinar con `--voice`; llama `cli.py voice --always-on`.

## What works (actualizado 2026-05-17)

- **ModeRegistry → /api/chat** — routing 3.0 activo con flag `use_v3_modes: true`; `_extract_reply` normaliza salida de los 11 modos; fallback a v1 transparente
- **PALACE reader** — mapeo domain→área correcto; fallback a todas las áreas para dominios desconocidos; datos PALACE ahora fluyen a los modos cognitivos
- **RAG** — 25/25 artifacts indexados, 450 chunks ChromaDB; búsqueda semántica operativa
- **start.py** — UnicodeEncodeError corregido en Windows; `--status` funciona sin crash

## Known issues

- guardian_block=False no verificado con Ollama real en todas las rutas
- MemoryBus.search() depende de `semantic_graph.find_concepts()` — verificar que existe esa función
- Sprint 4+5 (memoria profunda, proactividad): integración con voz pendiente end-to-end
