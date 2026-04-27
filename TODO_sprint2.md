# Sprint 2 - Memory Influence Layer

## Plan Steps (approved per user feedback)
1. ☐ Create `core/memory/influence_engine.py` - build_memory_influence, _compress_nodes, _build_bias_summary.
2. ☐ Update `memory/service.py` - Add `find_similar_decisions` delegating to decision_store.find_similar.
3. ☐ Update `agents/explorer.py` - Use find_similar_cases for facts.
4. ☐ Update `ai/prompts.py` - Add memory_weighted simulation prompt.
5. ☐ Update `agents/simulator.py` - Inject memory_influence into prompt.
6. ☐ Test: Run /simulate, verify prompt context has bias_summary/cases.

## Current Progress
- ✅ Step 1 complete (influence_engine.py created)
- ✅ Step 2 complete (service.py find_similar_decisions added)
- ✅ Step 3 complete (explorer.py uses find_similar_decisions for enhanced_memory)
- ✅ Step 4 complete (prompts.py simulation_prompt memory-weighted)

**Sprint 2 + MRE complete**

Test: Run multiple /simulate same question - check scenarios adapt via bias/regulation, log has age_days/weight/similarity.

Ready for Sprint 3.
