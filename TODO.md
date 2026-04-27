# FASE 1 Stabilization TODO

## Progress Tracker

- [x] 1. Add enforce_contract() to `core/contracts/contract_lock.py`
- [x] 2. Remove output validation from `core/contracts/api_contract_gate.py`
- [x] 3. Update `api/main.py` to use enforce_contract()`
- [x] 4. Simplify `core/orchestrator.py` to pure router (explorer → simulator → guardian)
- [x] 5. Clean `agents/guardian.py` (no events, add guardian_trace)
- [x] 6. Ensure `agents/simulator.py` pure generation
- [x] 7. Add `save_decision(report)` to `memory/service.py` (pure persist)
- [x] 8. Add `test_every_output_passes_contract()` to `tests/system/test_contract_integrity.py`
- [x] 9. Update `tests/system/test_full_pipeline.py` for new flow
- [x] 10. Run pytest + API test

**FASE 1 100% ✅ Ready for FASE 2**

