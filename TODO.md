# TODO - Memory Layer Implementation

## Pasos completados

- [x] 1. Rewrite `memory/models.py` → align to minimal schema (id int autoincrement, created_at datetime)
- [x] 2. Rewrite `memory/storage.py` → table `memory`, columns match models.py, init_db/save_memory/get_by_domain
- [x] 3. Create `memory/service.py` → retrieve_context(domain) & store_event(question, domain)
- [x] 4. Create `memory/__init__.py` → expose public API
- [x] 5. Update `core/orchestrator.py` → auto-retrieve memory, save event after execution
- [x] 6. Update `api/main.py` → keep backward compat, memory auto-retrieved
- [x] 7. Update `test_changes.py` → add memory layer tests
- [x] 8. Run tests and verify (✅ todos pasaron)

