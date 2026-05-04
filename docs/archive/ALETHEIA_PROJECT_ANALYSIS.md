# Aletheia Project Analysis - Comprehensive Overview for AI Context

## 📁 Directory Tree Structure
```
d:/Proyectos/aletheia-core/aletheia/
├── .gitignore
├── CHANGELOG.md
├── cli.py                          # Main CLI entrypoint (start/status/test/reset)
├── config.py
├── DESCRIPTION.md                  # Detailed system description
├── launcher.bat                    # Windows one-click launcher
├── PLAN.md                         # Implementation plans
├── README.md                       # Quick start guide
├── requirements.txt                # Python deps (fastapi, pydantic, etc.)
├── RESUMEN_FUNCIONAL.md            # Functional summary
├── run.py                          # Legacy entry (redirects to CLI)
├── TODO*.md                        # Various TODOs (launcher, stabilization, etc.)
├── agents/                         # Core agents
│   ├── explorer.py                 # Fact extraction, gaps, confidence
│   ├── guardian.py                 # Validation rules
│   ├── simulator.py                # Scenario generation
│   └── simulator_helpers.py
├── ai/                             # LLM prompts/client
│   ├── ollama_client.py
│   └── prompts.py
├── aletheia-ui/                    # React frontend
│   ├── src/components/             # Dashboard, Decisions UI
│   └── package.json
├── api/                            # FastAPI backend
│   ├── main.py                     # /simulate, /health endpoints
│   └── models.py
├── config/                         # Modes (DEV/TEST/PROD)
│   └── modes.py
├── core/                           # Main logic (500+ files/modules)
│   ├── orchestrator.py             # Pipeline router: ACO → CEL → agents
│   ├── aco/                        # Ant Colony Optimization middleware
│   ├── cel/                        # Cognitive Execution Layer
│   ├── contracts/                  # Contract enforcement
│   ├── llm/                        # LLM router, providers (ollama/mock/online)
│   ├── memory/                     # Influence/regulation engines
│   ├── palace/                     # Knowledge palace (reader/writer)
│   └── metrics/                    # DQS, drift detection
├── feedback/                       # Feedback loops
├── memory/                         # SQLite storage/service/models
└── tests/                          # System/integration tests
```

**Total: ~200 files.** Python-heavy backend (agents/core/llm), React UI, SQLite persistence.

## 🔍 Project Analysis

### 🎯 Purpose
Aletheia is a **local-first cognitive decision-making kernel** simulating human-like reasoning:
- **Input**: Domain + question (e.g., \"finanzas\", \"¿Dejo el trabajo?\")
- **Process**: Explorer (facts/gaps) → Simulator (scenarios/risks) → Guardian (validation) → Contract Lock
- **Output**: Structured `DecisionReport` (scenarios, risks, confidence, prediction, locked contract)
- **Key Features**:
  - LLM-powered (Ollama local-first: llama3/phi3)
  - Memory graph (SQLite nodes/refs/events)
  - ACO (Ant Colony Optimization) policy adaptation
  - CEL (Cognitive Execution Layer) fusion
  - Contract enforcement (unbreakable schemas)
  - Modes: DEV/TEST/PROD
  - Metrics: DQS (Decision Quality Score), drift detection

**Status**: **v1.1 PRODUCTION READY** (CEL complete, tests 8/8 pass via CLI).

### 🏗️ Architecture Layers (5 Core)
1. **Contracts** (`core/contracts/`): Input/output gates, `enforce_contract()` - **NEVER breaks**.
2. **Orchestrator** (`core/orchestrator.py`): Pure router `process_request(domain, question)`.
3. **Agents** (`agents/`): Explorer/Simulator/Guardian with policy injection.
4. **ACO+CEL** (`core/aco/`, `core/cel/`): Optimization + cognitive fusion → LLM prompts.
5. **Memory/Palace/Metrics** (`memory/`, `core/palace/`, `core/metrics/`): Persistence, knowledge, quality.

**Full Pipeline**:
```
CLI/API → Bootstrap (init memory/LLM) → /simulate → Gate In → Orchestrator (ACO→CEL→Agents) → Gate Out (enforce_contract) → Memory.save → JSON Response
```

### 🚀 Usage
```
# One-click (Windows)
launcher.bat  # Auto deps/servers/UI

# Manual
pip install -r requirements.txt
python cli.py reset
python cli.py test   # ✅ 8/8 PASS
python cli.py start  # API:8000/docs  UI:3000

# Test API
curl -X POST http://localhost:8000/simulate -d '{"domain":"test","question":"test?"}'
```

**Health**: `cli.py status` or `/health`.

## 📋 Main Code Files & Key Components

### Entry Points
| File | Role | Key Functions |
|------|------|---------------|
| `cli.py` | CLI launcher | `start()`, `status()`, `test()`, `reset()` |
| `api/main.py` | FastAPI | `simulate()`, `/health`, `/metrics` |
| `run.py` | Legacy → CLI | |
| `launcher.bat` | Windows automation | |

### Core Pipeline
| File/Module | Key Classes/Functions |
|-------------|----------------------|
| `core/orchestrator.py` | `process_request(domain, question)` - ACO/CEL/agents |
| `agents/explorer.py` | `run(domain, question)` - facts/confidence |
| `agents/simulator.py` | `run(exploration)` - scenarios/risks |
| `agents/guardian.py` | `validate(simulation)` - rules/block |
| `core/contracts/contract_lock.py` | `enforce_contract()`, `normalize_report()` |
| `core/aco/middleware.py` | `apply_aco()` - policy |
| `core/cel/executor.py` | CEL fusion |

### LLM & Prompts
- `core/llm/router.py`: `LLMRouter().generate()`
- `ai/ollama_client.py`: `generate(prompt)`
- `ai/prompts.py`: `exploration_prompt()`, `simulation_prompt()`

### Data/Persistence
- `memory/service.py`: `save_decision()`, `retrieve_context()`
- `memory/storage.py`: SQLite init
- `core/palace/*`: Knowledge RAG (reader/search/writer)

### UI (React)
- `aletheia-ui/src/App.js`: Dashboard
- Components: `DecisionInput.jsx`, `DqsChart.jsx`, etc.

### Config/Deps
- `config/modes.py`: DEV/TEST/PROD dicts
- `requirements.txt`: fastapi, pydantic, uvicorn, pytest, requests

### Tests (Critical)
- `tests/system/test_full_pipeline.py`, `test_contract_lock.py`, etc. - End-to-end integrity.

## 📈 Key Insights from Code Search
- **Imports**: Heavy use of `typing.Dict/Any`, `pydantic.BaseModel`, `core.models.DecisionReport`.
- **Classes**: `Context`, `CognitiveOptimizer`, `LLMRouter`, `DecisionMemoryNode`.
- **Functions**: `run()`, `validate()`, `generate()`, `healthcheck()`, `process_request()`.
- **Patterns**: Agentic flow, policy injection, contract validation, LLM prompting.

## ⚠️ Status & Next
- **Production-ready**: Stable API/UI, full tests.
- **Pending**: UI enhancements, more tests, Pydantic V2.

**This document serves as complete context for any AI working on Aletheia. Use `cli.py test` to verify.**

