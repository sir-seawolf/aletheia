# TODO — Cognitive Event Bus + Live Stream + UI MVP

- [x] Revisar estado actual del backend y pipeline existente

- [x] Migrar event bus a sesiones en `core/event_bus.py`
  - [x] mantener modelo `CognitiveEvent` (timestamp, session_id, agent, stage, event_type, payload, confidence)
  - [x] reemplazar cola global por streams por sesión
  - [x] `emit_event(event)` enruta por `session_id`
  - [x] `get_event(session_id)` consume por sesión

- [x] Propagar `session_id` en contexto/orquestación
  - [x] `core/context.py` incluye `session_id` en constructor y serialización
  - [x] `Context.from_request(..., session_id=...)`
  - [x] `core/orchestrator.py` crea contexto con sesión activa

- [x] Robustecer errores de pipeline
  - [x] emitir evento estructurado `stage=blocked`, `event_type=error` cuando falla un step
  - [x] conservar propagación de excepción para visibilidad operativa

- [x] Exponer stream realtime por sesión en `api/main.py`
  - [x] endpoint WebSocket `GET ws://127.0.0.1:8000/stream/{session_id}`
  - [x] loop async con `get_event(session_id)`
  - [x] throttling de polling (`asyncio.sleep(0.05)`) en cada iteración

- [x] UI MVP (pantalla única cognitiva) en `aletheia-ui`
  - [x] scaffold React
  - [x] `App.js` con input, botón de simular, stream de eventos, panel de resultado
  - [x] conexión a `POST /simulate`
  - [x] conexión a `ws://127.0.0.1:8000/stream/{session_id}`
  - [x] estilos base en `App.css`
  - [x] build de producción OK (`npm run build`)

- [ ] Testing exhaustivo pendiente (acordado continuar después de documentación)
  - [ ] Backend: `/` + edge cases adicionales `/simulate` + validación real de WS por sesión
  - [ ] Frontend: flujo E2E visual completo (input → stream live → resultado)
