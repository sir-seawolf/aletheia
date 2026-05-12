## v1.1.0 - Cognitive Execution Layer (2024)

### Added
- **CEL (core/cel/)**: executor.py fuses ACO + LLMRouter
  - cognition.py: policy fusion
  - routing.py: adaptive generate
  - memory_bridge.py: unified memory/palace
  - cost_model.py: cognitive cost
  - learning_loop.py: auto-opt
- orchestrator.py: ACO → CEL → explorer (augmented input)

### Fixed
- ACO files syntax (adaptive_router, learning_layer, middleware): unescaped quotes/arrows

### Updated
- launcher.bat v1.1: CEL demos [3] Status+Demo, [4] Quick Test
- README.md: v1.1 FASE 2, CEL capa diagram
- estado_actual.md: CEL operational
- TODO.md: Complete

**Demo:** launcher.bat → 4
**Full:** launcher.bat → 1/2 (DEMO/REAL CEL active)

Ruta: Palace + Memory + CEL (ACO+Router) + Pipeline + Lock ✅

