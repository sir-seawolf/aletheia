# Progress

## What works

### Core pipeline
- Pipeline cognitivo end-to-end: API → ACO → CEL → explorer → simulator → guardian → contract_lock → memory
- LLMRouter con multi-provider: Ollama → Claude → OpenAI → DeepSeek → Groq → Mistral → Mock
- TURBO mode: specialist / race / panel con probe de latencia en tiempo real
- FastAPI + SQLite + Ollama integrados y verificados
- .gitignore: datos personales (PALACE/IDENTITY/, PALACE/CREACION/) excluidos

### PALACE (memoria episódica)
- classifier, reader, writer, search funcionales
- Bugs corregidos: regex `\b`, split `\n`, JSON multiline (2026-05-07)

### HESTIA (motor de metas financieras)
- `core/hestia/`: memory.py, observer.py, analyzer.py, engine.py
- SQLite hestia.db con 4 tablas; meta inicial "Clase media España 30k€/año"
- 6 endpoints en `/api/hestia/*`

### Voz offline (sprints 1–3)
- `core/voice/`: listener.py (faster-whisper), speaker.py (Piper TTS), session.py
- Modulación emocional via length_scale/noise_scale en Piper
- Modelos locales: whisper base (~150 MB), es_ES-davefx-medium (~65 MB)
- `python cli.py voice` y `python cli.py voices` operativos

### Memoria profunda (sprint 4)
- `core/memory/`: semantic_graph.py, emotional_tagger.py, working_memory.py, consolidator.py

### Proactividad + emociones + agencia + ecosistema (sprints 5–8)
- `core/cognition/`: proactive_engine.py, emotional_state.py
- `core/agency/`: action_catalog.py, intent_parser.py, action_executor.py (7 acciones con confirmación)
- `core/ecosystem/coordinator.py` — debate interno multi-brain

### Docs e ingesta
- PDF, DOCX, TXT, MD, CSV, URL, Google Drive online/local, OneDrive, Gmail
- artifact_store.py (SHA-256 + versionado), financial_extractor.py, bank_parser.py (11 categorías)
- DuckDuckGo search sin API key

### Chat conversacional
- `core/chat/session.py` — historial multi-turno (deque 20 turnos por session_id)
- `/api/chat` con routing: acción → conversacional → pipeline
- chatSessionId estable en frontend

### UI rediseñada
- Layout split: Sidebar (220px) + Main (flex) + ThinkingPanel (300px)
- CommandPalette.jsx (Ctrl+K), ChatView.jsx, DocBrowser.jsx, SettingsPage.jsx
- VoiceInput.jsx (Web Speech API + Whisper backend)
- ThinkingPanel.jsx con WebSocket y auto-reconnect
- BrainLoader.jsx reactivo al agente activo
- Status bar: provider, Ollama, memoria, docs, total financiero

### Launcher
- `start.py` — único punto de entrada: `--voice --demo --reset --status --stop`
- `launcher.bat` — port detection via `tools/find_port.py`, espera readiness antes de abrir browser
- `BROWSER=none` en `.env` — sin auto-open de CRA

### APIs en runtime.py
- `/api/status`, `/api/chat`, `/api/search`, `/api/docs/*`, `/api/artifacts/*`
- `/api/gmail/*`, `/api/settings/*`, `/api/hestia/*`, `/api/turbo/*`
- `/stream/{session_id}` — WebSocket eventos cognitivos en tiempo real

## Backlog / próximos pasos

- **RAG sobre documentos** — ChromaDB + embeddings Ollama (mayor impacto)
- **Google Calendar integration** — acceso a agenda desde voz/chat
- **Telegram bot** — acceso móvil
- **Calculadora fiscal IRPF/IVA** — sobre artifacts del bank_parser
- **Wake word "Aletheia"** — entrenar openWakeWord personalizado
- **Piper voz mejor calidad** — es_ES-sharvard-medium
- **TTS interrumpible** — threading para cortar habla mid-sentence

## Known issues

- guardian_block=False no verificado con Ollama real en todas las rutas (requiere Ollama corriendo)
- Sprints 4 y 5 (memoria profunda, proactividad) implementados pero integración con voz pendiente de validación end-to-end
