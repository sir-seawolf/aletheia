# LLMRouter v1 Implementation TODO

## Plan Breakdown (Approved)

### Phase 1: Create New Files (Providers Structure)
- [x] core/llm/providers/ollama.py (refactor from ai/ollama_client.py)
- [x] core/llm/providers/mock.py
- [x] core/llm/providers/online.py (placeholder)
- [x] core/llm/cache.py (LLMCache class)
- [x] core/llm/selector.py (select_provider())
- [x] core/llm/prompts.py (move/refactor from ai/prompts.py, add _enrich)

### Phase 2: Refactor Core Router
- [x] core/llm/router.py (implement generate(), singleton)

### Phase 3: Update Agents & Integrations
- [x] agents/explorer.py (replace direct ollama → router.generate)
- [x] agents/simulator.py (fix llm_generate → router.generate)
- [x] core/llm/__init__.py (exports)
- [x] core/orchestrator.py (adapt enrich if needed)
- [ ] Deprecate ai/ollama_client.py & ai/prompts.py

### Phase 4: Testing & Validation
- [ ] Run pytest tests/system/
- [ ] Healthcheck: python core/bootstrap/healthcheck.py
- [ ] Full pipeline test: python run.py or cli.py
- [ ] Update CHANGELOG.md, TODO.md

### Phase 3: Update Agents & Integrations
- [ ] agents/explorer.py (replace direct ollama → router.generate)
- [ ] agents/simulator.py (fix llm_generate → router.generate)
- [ ] core/llm/__init__.py (exports)
- [ ] core/orchestrator.py (adapt enrich if needed)
- [ ] Deprecate ai/ollama_client.py & ai/prompts.py

### Phase 4: Testing & Validation
- [ ] Run pytest tests/system/
- [ ] Healthcheck: python core/bootstrap/healthcheck.py
- [ ] Full pipeline test: python run.py or cli.py
- [ ] Update CHANGELOG.md, TODO.md

**Current Progress: Starting Phase 1**

