# Sprint 1 - Learning Loop (MemoryService update_outcome + Node extension + Orchestrator loop)

## Plan Steps (approved)
Breakdown of approved Sprint 1:

1. ✅ Create `core/learning/rules.py` - Simple profile adjustment rule based on error.
2. ✅ Update `memory/models.py` - Add `prediction_error`, `confidence_before/after` to `DecisionMemoryNode`.
3. ✅ Update `memory/service.py` - Add `update_outcome()` delegating to decision_store.
4. ✅ Update `core/models.py` - Add `node_id: Optional[str] = None` to `DecisionReport` (linter note ignored).
5. ✅ Update `core/orchestrator.py` - Extract expected_outcome from simulate, call service.update_outcome, return node_id.
6. ✅ Test: Run /simulate, verify decision_log.json updates (manual: POST to /simulate, check memory/data/decision_log.json has expected_outcome, confidence_before, node_id in response).
7. ✅ Sprint 1 complete - Learning loop implemented.

**Ready for Sprint 2 - Memory Influence Layer**

Files updated:
- core/learning/rules.py (new)
- memory/models.py
- memory/service.py 
- core/models.py
- core/orchestrator.py

Linter notes (Pylance imports) ignored, logic sound.
