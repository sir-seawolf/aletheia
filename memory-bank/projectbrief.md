# Project brief

## Goal

Build **Aletheia 3.0** — a unified cognitive operating system (not a chatbot).
One observer, one memory, one identity. Multiple cognitive modes as specialised
reasoning configurations that share the same memory and tools.

## What it is

- Metacognitive orchestration system
- Adaptive cognitive architecture with 11 specialised modes
- Shared-memory reasoning platform
- Cognitive economy engine (fatigue, energy, token budget)

## What it is NOT

- Isolated agents or multiple personalities
- Prompt wrappers
- A traditional AI assistant

## Current phase (as of 2026-05-13)

**Phase: Aletheia 3.0 Foundations** — architectural primitives implemented:

1. `CognitiveState` + `SessionStateRegistry` — unified runtime state
2. `CognitiveMode` base + 11 modes + `ModeRegistry` — mode system
3. `MemoryBus` — unified memory access layer
4. `RoutingIntelligence` — dynamic provider routing
5. `FatigueEngine` — adaptive fatigue tracking

Pipeline (v1.x) still active in parallel: orchestrator → explorer → simulator → guardian → palace.

## Definition of done for current phase

- [ ] All 11 cognitive modes integrated into the main pipeline (replacing agents/)
- [ ] MemoryBus used exclusively for memory access in all modes
- [ ] FatigueEngine and RoutingIntelligence verified end-to-end in a voice session
- [ ] RAG indexed and semantic search operational
- [ ] memory-bank fully populated and reflecting current architecture

## Non-goals

- Multi-user / multi-tenant support
- Cloud deployment (runs local-first)
- Real-time collaboration
