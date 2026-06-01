# Roadmap — Aletheia hacia una IA conversacional avanzada

**Iniciado:** 2026-05-05  
**Visión:** Aletheia como IA cognitiva con voz natural offline, memoria profunda, proactividad y agencia. Más allá de Jarvis: genuinamente cognitiva, con estados internos, identidad emergente, y capacidad de actuar en el mundo.

---

## Estado de sprints

| Sprint | Nombre               | Estado      | Completado |
|--------|----------------------|-------------|------------|
| 1      | Voz base offline     | ✅ Completo | 2026-05-05 |
| 2      | Naturalidad de voz   | ✅ Completo | 2026-05-05 |
| 3      | Modulacion de voz    | ✅ Completo | 2026-05-05 |
| 4      | Memoria profunda     | ✅ Completo | 2026-05-06 |
| 5      | Inteligencia proact. | ✅ Completo | 2026-05-06 |
| 6      | Modelo emocional     | ✅ Completo | 2026-05-06 |
| 7      | Agencia autónoma     | ✅ Completo | 2026-05-06 |
| 8      | Civilización cogn.   | ✅ Completo | 2026-05-06 |

---

## Sprint 1 — Voz base offline

**Meta:** Aletheia escucha y responde. 100% sin internet.  
**Estado:** ✅ Completo — 2026-05-05

**Logros:**

- `core/voice/` creado con listener, speaker, session
- faster-whisper funcional, transcripción en español perfecta
- pyttsx3 con Helena Desktop como TTS inicial (robótico pero funcional)
- Bucle push-to-talk end-to-end verificado por el usuario
- `python cli.py voice` y `python cli.py voices` operativos

### Stack tecnológico
| Capa | Tecnología | Notas |
|------|-----------|-------|
| Wake word | `openWakeWord` | Gratuito, offline, modelos entrenables |
| STT | `faster-whisper` (modelo `small` o `medium`) | CTranslate2, rápido, preciso en español |
| TTS | `Kokoro-82M` (primero) / `Coqui XTTS v2` (si se necesita clonación de voz) | Kokoro: natural y ligero. Coqui: clona voz con 6s de audio |
| Audio I/O | `sounddevice` + `PyAudio` | Captura y reproducción |

### Archivos a crear
- `core/voice/__init__.py`
- `core/voice/listener.py` — captura audio, wake word, STT
- `core/voice/speaker.py` — TTS con streaming parcial
- `core/voice/session.py` — sesión de voz conectada al pipeline CEL
- `core/voice/models/` — modelos descargados localmente (en .gitignore)

### Integración
- CLI: `python cli.py --voice`
- `cli.py` recibe el flag `--voice` y arranca `VoiceSession`
- `VoiceSession` usa el mismo pipeline CEL que las llamadas por texto
- Modelos de voz en `PALACE/voice_models/` (excluidos de git)

### Dependencias pip a añadir
```
faster-whisper
openWakeWord
kokoro  # o coqui-tts
sounddevice
PyAudio
```

### Criterio de éxito
- [ ] "Aletheia" como wake word la activa
- [ ] Transcribe correctamente frases en español
- [ ] Responde con voz sintetizada natural
- [ ] Funciona sin conexión a internet
- [ ] Latencia STT+CEL+TTS < 5 segundos en local

---

## Sprint 2 — Naturalidad de voz

**Meta:** No suena a robot. La conversación fluye.  
**Estado:** 🔄 En progreso — 2026-05-05

### Completado en Sprint 2 (2026-05-05)

- ✅ Piper TTS `es_ES-davefx-medium` como motor primario (ONNX neural, Python 3.14 compatible)
- ✅ Filtro de respuestas mock — ya no lee strings internos de debug
- ✅ `_clean_for_voice()` — elimina markdown, limita a 350 chars con corte en frase completa
- ✅ Fallback pyttsx3 mejorado con selección automática de voz española

### Pendiente de Sprint 2

- **Manejo de interrupciones:** Si el usuario habla mientras Aletheia habla, ella para
- **Pausas naturales:** Respetar comas, puntos, elipsis en la prosodia
- **Backchannels opcionales:** "Entendido", "Claro", "Mm-hmm" en momentos apropiados

### Archivos afectados
- `core/voice/speaker.py` — añadir streaming y control de interrupción
- `core/voice/session.py` — manejo de turn-taking y interrupciones
- `core/voice/prosody.py` (nuevo) — análisis de puntuación para pausa/velocidad

---

## Sprint 3 — Modulación de voz

**Meta:** Aletheia tiene una voz única, consistente, y emocionalmente expresiva.  
**Estado:** 🔲 Pendiente (requiere Sprint 2)

### Componentes
- **RVC v2** (Retrieval-based Voice Conversion): toma el audio del TTS y lo convierte a la voz de Aletheia
- **Perfiles de voz:** urgente, reflexiva, entusiasta, cautelosa
- **Estado emocional → prosodia:** `core/cognition/self_awareness.py` expone estado → `speaker.py` lo aplica
- **Voice training:** posibilidad de entrenar RVC con samples propios para voz personalizada

### Archivos a crear/modificar
- `core/voice/modulator.py` — integración RVC v2
- `core/voice/profiles.py` — perfiles de voz por estado emocional
- `core/voice/speaker.py` — añadir pipeline: TTS raw → RVC → audio final

---

## Sprint 4 — Memoria profunda

**Meta:** Aletheia recuerda como un humano: qué pasó, cómo se sentía, qué importaba.  
**Estado:** 🔲 Pendiente

### Capas de memoria a implementar

| Tipo | Implementación | Estado actual |
|------|---------------|---------------|
| Episódica | PALACE (ya existe) | ✅ Funcional |
| Semántica | Grafo de conocimiento (NetworkX + SQLite) | ❌ Por hacer |
| De trabajo | Contexto de sesión enriquecido | Parcial |
| Emocional | Etiquetado valence/arousal en memorias | ❌ Por hacer |
| Procedural | Rutinas aprendidas del usuario | ❌ Por hacer |

### Archivos a crear
- `core/memory/semantic_graph.py` — grafo de conocimiento
- `core/memory/emotional_tagger.py` — etiqueta memorias con valence/arousal
- `core/memory/consolidator.py` — mueve recuerdos episódicos → semánticos

---

## Sprint 5 — Inteligencia proactiva

**Meta:** Aletheia actúa sin que se lo pidas.  
**Estado:** 🔲 Pendiente (requiere Sprint 4)

### Capacidades
- Scheduler integrado al pipeline cognitivo
- Briefings automáticos al arrancar: estado de proyectos activos, tareas pendientes
- Detección de patrones de uso del usuario
- `core/cognition/autonomous_layer.py` (ya existe) conectado a voz y acciones

---

## Sprint 6 — Modelo emocional

**Meta:** Aletheia tiene estados internos que colorean cómo recuerda, responde y suena.  
**Estado:** 🔲 Pendiente (requiere Sprint 3 + Sprint 4)

### Diseño
- Eje valence/arousal persistente entre sesiones (guardado en SQLite)
- Emociones se forman por: resultados de decisiones, feedback del usuario, logros
- Influyen en: qué memorias recupera primero, tono de voz, nivel de detalle en respuestas
- Conectado a `core/memory/influence_engine.py` y `core/guardian/`

---

## Sprint 7 — Agencia autónoma

**Meta:** Aletheia hace cosas en el mundo, con supervisión del guardián.  
**Estado:** 🔲 Pendiente (requiere Sprint 5 + Sprint 6)

### Capacidades
- Ejecución de comandos/scripts (aprobados por guardián)
- Gestión de archivos y código
- Integración con APIs externas: GitHub, calendario, email
- Voz como interfaz de comandos reales

---

## Sprint 8 — Civilización cognitiva

**Meta:** Múltiples instancias de Aletheia coordinadas.  
**Estado:** 🔲 Futuro (requiere Sprint 7)

- `core/ecosystem/cognitive_ecosystem.py` cobra vida real
- Instancias especializadas con voz propia
- Coordinación, competencia por recursos cognitivos, emergencia colectiva

---

## Decisiones de diseño clave

- **Todo offline primero:** ningún sprint debe requerir internet para funcionar
- **Voz integrada al pipeline CEL, no paralela:** misma lógica cognitiva para texto y voz
- **Modelos locales en PALACE/voice_models/:** excluidos de git
- **Estado emocional es persistente:** survives entre sesiones via SQLite
- **Guardián siempre activo:** agencia autónoma siempre supervisada

---

## Cómo retomar trabajo tras un reset

1. Leer este archivo (`memory-bank/roadmap.md`)
2. Leer `memory-bank/activeContext.md` para el foco actual
3. Buscar el sprint activo (🔄 En progreso) y sus archivos
4. Revisar criterios de éxito del sprint para saber qué falta
