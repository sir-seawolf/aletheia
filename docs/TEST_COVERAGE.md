# Test Coverage v1.1

## Passing Tests (8/8)
- test_contract_lock.py: Contract enforcement
- test_full_pipeline.py: End-to-end
- test_memory_regression.py: Memory stability
- test_contract_integrity.py: API gates
- test_guardian_behavior.py: Guardian rules

## Pending (No tests)
- ACO v2/v3
- Cognition layers (ACL, PFC, SelfAware)
- Priority: High for ACO learning_layer

## Run
python -m pytest tests/system/ -v

