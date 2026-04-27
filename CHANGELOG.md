# Changelog

## v1.0.0 — FASE 1 Stabilized Kernel (2024)

### Added
- FASE 1 stabilization: contract_lock.enforce_contract() - single source of truth
- api_contract_gate: input validation only
- api/main.py: clean pipeline input → process → enforce_contract
- orchestrator.py: pure router explorer → simulator → guardian
- guardian.py: 6 rules centralized, guardian_trace added
- simulator.py: pure generation stub
- memory/service.py: save_decision pure persist
- Tests: test_every_output_passes_contract, updated full_pipeline

### Changed
- All changes minimal, order: contract → api → orchestrator → agents → memory → tests
- Zero roturas in core flow

### Status
- Contract enforced on all outputs
- Guardian decisions traced
- TODO.md 100% complete

## v0.2.0 — Cognitive Live MVP (previous)


### Added
- Session-aware cognitive event streaming architecture.
- React MVP UI in `aletheia-ui/` (single-screen cognitive console).
- Minimal frontend flow:
  - question input
  - simulation trigger
  - websocket live event panel
  - final output panel

### Changed
- `core/event_bus.py`
  - Migrated from a single global queue to per-session queues.
  - `emit_event(...)` now routes by `session_id`.
  - `get_event(session_id)` now reads events by session.
- `core/context.py`
  - Added `session_id` to context model.
  - `to_dict()` now includes `session_id`.
  - `from_request(..., session_id=...)` supported.
- `core/orchestrator.py`
  - Context creation now propagates `session_id`.
  - Step loop now emits structured error event (`stage=blocked`, `event_type=error`) before re-raising.
- `api/main.py`
  - WebSocket endpoint moved to: `/stream/{session_id}`.
  - Streaming loop now reads from `get_event(session_id)`.
  - Added polling throttle (`asyncio.sleep(0.05)`) on every loop iteration.

### Notes
- Backend API remains available at `http://127.0.0.1:8000`.
- Existing `/simulate`, `/health`, and `/` routes remain active.
- CRA scaffold warns deprecation of Create React App, but build is working correctly for MVP.

### Validation done
- Backend:
  - `/health` returns 200.
  - `/simulate` happy path returns 200.
  - `/simulate` validation errors return 422 for missing required fields.
- Frontend:
  - React production build succeeds (`npm run build` in `aletheia-ui`).
