# ACO Implementation TODO

## Plan Breakdown (Approved)

### 1. [x] Create core/aco structure (engine.py, adaptive_router.py, learning_layer.py, middleware.py, memory.py, __init__.py)
### 2. [x] Integrate middleware in core/orchestrator.py
### 3. [x] Update agents/explorer.py, agents/simulator.py for policy injection
### 4. [ ] Extend core/context.py with policy field
### 5. [ ] Add tests/system/test_aco.py
### 6. [ ] Verify pipeline + palace attach
### 7. [ ] Update CHANGELOG.md
### 8. [ ] Test full: pytest + run.py /api/simulate

Progress: Agents updated for policy (optional kwarg). Linting mostly fixed. ACO v1-v4 functional (modes decide, observe, learn). Next: Context + tests.

