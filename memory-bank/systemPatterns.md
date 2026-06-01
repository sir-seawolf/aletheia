# System patterns

## High-level layout

```text
core/
  cognitive_state.py       ← CognitiveState dataclass (energy, fatigue, coherence, …)
  session_state.py         ← SessionStateRegistry (per-session CognitiveState)
  orchestrator.py          ← Main cognitive pipeline entry point
  event_bus.py             ← Pub/sub cognitive event bus
  context.py               ← Request context builder

  modes/                   ← 11 cognitive modes (Aletheia 3.0)
    base.py                ← CognitiveMode ABC + ModeID enum + ModeResult
    observer.py            ← Routing, supervision, continuity
    analytical.py          ← Logic, decomposition, validation
    strategic.py           ← Long-term planning, trade-offs
    kronos.py              ← Financial reasoning (wraps core/kronos/)
    creative.py            ← Ideation, synthesis
    reflective.py          ← Contradiction detection, metacognition
    guardian.py            ← Security, risk, permission validation
    executive.py           ← Action execution (wraps core/agency/)
    memory_curator.py      ← Memory consolidation, compression
    researcher.py          ← Web/RAG retrieval
    world_model.py         ← Systems thinking, causal simulation
    registry.py            ← ModeRegistry singleton (route_and_activate)

  memory/
    bus.py                 ← MemoryBus singleton (unified access to all backends)
    working_memory.py      ← Intra-session working memory
    semantic_graph.py      ← SQLite concept graph
    consolidator.py        ← PALACE → semantic graph pipeline

  routing/
    intelligence.py        ← RoutingIntelligence (deterministic→local→free→premium)

  fatigue/
    engine.py              ← FatigueEngine (tracks cost, returns adaptations)

  llm/
    router.py              ← LLMRouter (v1.2: RoutingIntelligence + FatigueEngine integrated)
    providers/             ← ollama, claude, openai, deepseek, groq, mistral, mock

  aco/                     ← Adaptive Cognitive Optimizer (v1 active, v2/v3 stubs)
  cel/                     ← Cognitive Execution Layer
  kronos/                  ← Financial mode logic
  hestia/                  ← Financial goals engine
  agency/                  ← Intent parser + action executor
  palace/                  ← PALACE episodic memory search/read/write
  docs/                    ← Document ingestion (PDF/DOCX/Gmail/Drive/RAG)
  bootstrap/               ← FastAPI runtime + healthcheck
  voice/                   ← Listener (Whisper) + Speaker (Piper) + Session

agents/
  explorer.py              ← Hypothesis/fact exploration agent
  simulator.py             ← Scenario simulation agent
  guardian.py              ← Pipeline-level validation agent

memory/
  service.py               ← SQLite episodic storage
  models.py                ← MemoryNode, UserProfile Pydantic models

PALACE/                    ← User episodic data (CREACION/PROFESION/PSIQUE/ROL/TECNOLOGIA/VIDA)
aletheia-ui/               ← React frontend (split layout, CommandPalette, ThinkingPanel)
```

## Data flow (v1.2)

```text
[Request] → SessionStateRegistry.get_state(session_id)
         → ModeRegistry.route_and_activate(context, state)
             → ObserverMode._route() → target ModeID
             → TargetMode._execute(context, state)
                 → MemoryBus.retrieve(domain)     ← unified memory
                 → LLMRouter.generate(task, prompt)
                     → RoutingIntelligence.decide() → RouteDecision
                     → _call_configured(provider_hint)
                     → FatigueEngine.record_llm_call(tier, state)
         → Orchestrator stores result → PALACE + SQLite
```

## Key patterns

- **Cognitive modes**: all extend `CognitiveMode`. Call `mode.activate(context, state)` (never `_execute` directly).
- **Memory access**: always via `memory_bus` (never import `read_palace` or `retrieve_context` directly from modes).
- **Fatigue**: `fatigue_engine.record(event_type, state)` after every costly operation.
- **State**: `get_state(session_id)` from `core.session_state`; never construct `CognitiveState()` ad hoc.
- **Routing**: `routing_intelligence.decide(task, context, state)` before every LLM call in custom code.
- **Events**: `emit_event(build_event(...))` for all pipeline state changes; consumed by ThinkingPanel WebSocket.

## Patterns to avoid

- Do NOT import `read_palace`, `retrieve_context`, or `working_memory.session` directly from mode code — use `MemoryBus`.
- Do NOT call `CognitiveState()` outside `SessionStateRegistry` — use `get_state(session_id)`.
- Do NOT use LLMs for classification, filtering, scoring, routing, or templating — `RoutingIntelligence` marks these as `skip_llm=True`.
- Do NOT add more Universe/Civilization/Genome layers to `LLMRouter.__init__` until they are actually wired into `generate()`.
