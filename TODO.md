# TODO: Refactor arquitectura Aletheia → Outputs estructurados

## 🧱 1) core/ → El cerebro del sistema
- [x] **orchestrator.py** — Pipeline explícito con steps, Context class, sin llamadas directas a LLM ni DB
- [x] **risk_engine.py** — Devolver configuración estructurada (level, require_scenarios, allow_creativity, min_evidence)
- [x] **context.py** — Class Context explícito (domain, risk, memory, question, constraints)

## 🤖 2) agents/ → Especialización real
- [x] **explorer.py** — Output estructurado: facts, gaps, confidence
- [x] **simulator.py** — Output estructurado: scenarios, risks, assumptions
- [x] **guardian.py** — Output estructurado: valid, issues, corrected_output

## 🧠 3) memory/ → El futuro del sistema
- [x] **models.py** — MemoryItem con id, type, content, date, confidence, source, domain, tags
- [x] **storage.py** — SQLite simple: save(), get_all(), search()

## 🤖 4) ai/ → Interfaz con el modelo
- [x] **ollama_client.py** — generate(prompt, temperature=0.7)
- [x] **prompts.py** — Dividir por función: simulation_prompt(), exploration_prompt(), validation_prompt()

## 🌐 5) api/ → Puerta de entrada
- [x] **main.py** — Pydantic models, recibir request, validar input, llamar orchestrator

## ⚙️ 6) Config y ejecución
- [x] **config.py** — MODEL, USE_CLOUD, DOMAIN_RISK_MAP, RISK_RULES
- [x] **run.py** — Punto de entrada simple con uvicorn

## ✅ 7) Verificación
- [ ] Commit y push a GitHub

