# Active context

**Current focus:** Todos los sprints completados y consolidados. Sistema listo para uso y pruebas reales.

**Completado en esta sesion (2026-05-05 / 2026-05-06):**

- [x] Sprint 1 — Voz base offline (faster-whisper + Piper TTS + push-to-talk)
- [x] Sprint 2 — Naturalidad: streaming por frases + pausas naturales
- [x] Sprint 3 — Modulacion emocional via length_scale/noise_scale en Piper
- [x] Sprint 4 — Memoria profunda: semantic_graph, emotional_tagger, working_memory, consolidator
- [x] Sprint 5 — Proactividad: briefing de arranque + deteccion de patrones
- [x] Sprint 6 — Modelo emocional persistente (PALACE/emotional_state.json)
- [x] Sprint 7 — Agencia autonoma: 7 acciones con confirmacion de voz
- [x] Sprint 8 — Civilizacion cognitiva: debate interno multi-brain + persistencia
- [x] Consolidacion: 5 bugs corregidos (valence logic, coordinator brains, consolidator domain, SQLite context managers, intent parser guard)

**Arquitectura de voz activa:**

```text
[ENTER] -> record_until_silence -> transcribe (faster-whisper)
        -> intent_parser.detect() -> accion? -> confirm -> execute
                                  -> pipeline? -> ecosystem_debate (si compleja)
                                              -> process_request (CEL + ACO)
        -> speak(response, emotion=estado_emocional)
        -> pattern_check -> sugerencia proactiva
        -> update_from_result -> emotional_state persistido
```

**Modulos nuevos creados:**

- core/voice/ — listener.py, speaker.py, session.py
- core/memory/ — emotional_tagger.py, working_memory.py, semantic_graph.py, consolidator.py
- core/cognition/ — proactive_engine.py, emotional_state.py
- core/agency/ — action_catalog.py, intent_parser.py, action_executor.py
- core/ecosystem/ — coordinator.py

**Comandos para arrancar:**

```batch
# launcher.bat -> [1] DEMO o [2] REAL -> [2] Voz
# o directamente:
python cli.py voice
python cli.py voices   # diagnostico de voces disponibles
```

**Dependencias de voz instaladas:**

```text
faster-whisper, sounddevice, soundfile, numpy, pyttsx3, piper-tts
```

**Estado de modelos locales:**

- faster-whisper base: PALACE/voice_models/whisper/ (~150 MB)
- Piper es_ES-davefx-medium: PALACE/voice_models/piper/ (~65 MB)

**Open questions / proximas mejoras:**

- Wake word personalizado "Aletheia" (requiere entrenar openWakeWord)
- Piper modelo de mayor calidad (es_ES-sharvard-medium)
- Agencia Sprint 7b: acciones destructivas con doble confirmacion (git, APIs)
- Interrupcion de TTS mientras habla (requiere threading)
