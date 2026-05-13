# Tech context

## Stack

- **Language / runtime**: Python 3.11+
- **API framework**: FastAPI + uvicorn
- **Frontend**: React 18 (CRA), Tailwind, WebSocket (ThinkingPanel)
- **LLM providers**: Ollama (local), Claude (Anthropic), OpenAI, DeepSeek, Groq, Mistral, Mock
- **STT**: faster-whisper (base model, ~150 MB, PALACE/voice_models/whisper/)
- **TTS**: Piper (`es_ES-sharvard-medium`, ~77 MB, PALACE/voice_models/piper/)
- **VAD**: silero-vad (auto-downloaded, ~2 MB)
- **Memory / DB**: SQLite (memory/data/), ChromaDB (PALACE/rag/) for vector search
- **Package manager**: pip + requirements.txt

## Environment

- **Required env vars**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY` (all optional — system falls back to Ollama)
- **Ollama**: must be running on `localhost:11434`; default model `llama3.2:3b`
- **Config file**: `PALACE/config/preferences.json` — overrides provider/model per agent

## Build & test

```bash
python start.py                  # full stack (API + UI)
python start.py --voice          # voice session
python start.py --status         # health check
pytest tests/                    # unit/integration tests
python cli.py cel --domain X     # CEL quick test
```

## Key architectural constraints (v1.2)

- **CognitiveState** is per-session; always access via `get_state(session_id)` from `core.session_state`.
- **MemoryBus** is the only authorised entry point for memory in cognitive modes.
- **RoutingIntelligence** must be consulted before every LLM call in new code.
- **FatigueEngine** must record every LLM call and pipeline error.
- **Modes** must extend `CognitiveMode` and be registered in `ModeRegistry`.
- PALACE/IDENTITY/ and PALACE/CREACION/ are gitignored (personal data).
- RAG requires `POST /api/rag/reindex` to be called once after deps install.
- Google Calendar requires OAuth browser flow; Telegram requires token in `PALACE/config/telegram.json`.
