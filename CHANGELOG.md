# Changelog

## v0.2.0 — Cognitive Live MVP (current)

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
