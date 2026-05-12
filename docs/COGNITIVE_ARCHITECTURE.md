# Cognitive Architecture Overview

## Pipeline ASCII Diagram
```
INPUT (question/domain)
  ↓
ACL (autonomous_layer - bypass decision)
  ↓
ACO Middleware (policy injection)
  ↓
CEL (prefrontal_controller)
  ↓
Explorer → Simulator → Guardian
  ↓
LLM Router + Palace
  ↓
SelfAware Loop + Learning
  ↓
Contract Lock → OUTPUT (DecisionReport)
```

## Module Table
| Module                  | Status      | Capa      | Dependencias                  |
|-------------------------|-------------|-----------|-------------------------------|
| pipeline base (orchestrator) | PRODUCCIÓN | Core     | agents, contracts            |
| ACO v1 middleware       | PRODUCCIÓN | Opt      | adaptive_router, learning_layer |
| ACO v2 engine           | DESIGNED   | Opt v2   | memory                       |
| ACL (autonomous_layer)  | IMPLEMENTED| Pre-LLM  | palace, memory               |
| PFC (prefrontal)        | IMPLEMENTED| CEL      | palace, memory               |
| SelfAwareLoop           | PLACEHOLDER| Learning | None                         |
| LLM Router              | PRODUCCIÓN | LLM      | providers, cache, palace     |

## System Invariants (Golden Rules - NEVER CHANGE)
- DecisionReport contract REQUIRED_FIELDS immutable
- Guardian block on high risk
- MAX_EVOLUTION_RATE = 0.1 per cycle
- FREEZE_CONTRACT_CORE = True
- NO_SELF_OVERRIDE = True (no runtime self-mod)

