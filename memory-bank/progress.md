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

- **Conectar ModeRegistry al endpoint `/api/chat`** — activar routing 3.0 en producción
- **Migrar agents/ a modes/**: explorer → ANALYTICAL, simulator → STRATEGIC, guardian → GUARDIAN
- **RAG** — ejecutar `POST /api/rag/reindex` (deps OK: chromadb + nomic-embed-text)
- **Google Calendar** — completar OAuth en browser
- **Telegram** — token en `PALACE/config/telegram.json`
- **Wake word "Aletheia"** — entrenar openWakeWord
- **ACO v3 MetaCortex** — implementar meta_cortex.py (actualmente vacío)

## Known issues

- guardian_block=False no verificado con Ollama real en todas las rutas
- Modos 3.0 aún no integrados en el pipeline de producción (coexisten con v1.x)
- MemoryBus.search() depende de `semantic_graph.find_concepts()` — verificar que existe esa función
- Sprint 4+5 (memoria profunda, proactividad): integración con voz pendiente end-to-end
