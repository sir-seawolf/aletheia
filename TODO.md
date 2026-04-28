# Critical Bug Fixes - Stabilization Sprint

Status: Approved plan, implementing step-by-step.

## Steps:

- [x] 1. core/export.py: Fix '1from' → 'from pathlib import Path'
- [x] 2. core/llm/cache.py: Add 'from typing import Optional'
- [x] 3. memory/service.py: Add save_decision & retrieve_session_events; remove first duplicate store_session_event
- [x] 4. agents/explorer.py: Remove early return in _run(); add memory=None to run() and use memory or []
- [x] 5. core/orchestrator.py: Remove unused router=LLMRouter(); remove duplicate output= line; pass memory=context_dict['memory'] to explorer.run()
- [x] 6. Validate: Run pytest tests/system/; uvicorn api.main:app --reload; python cli.py
- [ ] 7. Fix cognitive_ecosystem.py bug; tests; launcher.bat improvements

Next: Implement step 1.
