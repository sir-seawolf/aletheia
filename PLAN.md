# FASE 1 STABILIZATION PLAN

## Information Gathered

**Files analyzed via tools:**
- `core/contracts/contract_lock.py`: normalize_report(), validate_final_report(), freeze_contract_version() exist. Missing enforce_contract().
- `core/contracts/api_contract_gate.py`: validate_request (input), validate_response (Pydantic + final_report + memory import).
- `api/main.py`: /simulate → gate input → process_request → gate output.
- `core/orchestrator.py`: Bloated process_request (500+ LOC): memory, events, fallbacks, feedback, traces, decision_store.
- `agents/guardian.py`: validate() → 6 rules → corrected_output with guardian_* → good, but events.
- `agents/simulator.py`: Generates scenarios (truncated read).
- `memory/service.py`: store_event mixed.
- `memory/models.py`: DecisionMemoryNode ready (expected_outcome etc.).
- Tests: Good coverage for contract/ pipeline.

## Detailed Update Plan

### 1. `core/contracts/contract_lock.py`
Add:
```python
def enforce_contract(report: dict) -> dict:
    report = normalize_report(report)
    validate_final_report(report)
    report["contract_version"] = freeze_contract_version()
    return report
```

### 2. `core/contracts/api_contract_gate.py`
- Remove `validate_response`.
- Remove memory imports.
- Keep `validate_request`.

### 3. `api/main.py`
Replace pipeline:
```
validated_input = APIContractGate.validate_request(req.dict())
result = process_request(**validated_input)
final = enforce_contract(result)
return final
```

### 4. `core/orchestrator.py`
**Radical simplify** process_request(domain, question):
```python
from agents import explorer, simulator, guardian

def process_request(domain: str, question: str):
    exploration = explorer.run(domain, question)
    simulation = simulator.run(exploration)
    validated = guardian.validate(simulation)
    return validated['corrected_output']
```
Delete: memory, events, context, risk, feedback, traces, fallbacks (pure router).

### 5. `agents/guardian.py`
- Remove emit_event.
- Add to result: `"guardian_trace": {&#x27;rules_triggered&#x27;: issues, &#x27;severity&#x27;: severity}`

### 6. `agents/simulator.py`
Ensure pure generation, no validation.

### 7. `memory/service.py`
Add/rename:
```python
def save_decision(report: dict):
    # minimal persist report as-is
```

### 8. `memory/models.py`: No change.

### 9. `tests/system/test_contract_integrity.py`
Add:
```python
def test_every_output_passes_contract():
    result = process_request(&#x27;test&#x27;, &#x27;test?&#x27;)
    enforce_contract(result)
```

### 10. `tests/system/test_full_pipeline.py`
Update mocks for new pure flow.

## Dependent Files
- agents/explorer.py (sig if needed).

## Followup steps
- Edit 1-10 sequentially.
- `pytest tests/system/`
- Test API: `curl -X POST http://localhost:8000/simulate -d '{"domain":"test","question":"test?"}'`
- Update TODO.md with progress.

Total changes: Minimal, zero breaks.

