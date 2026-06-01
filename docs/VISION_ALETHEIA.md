# Visión Aletheia — IA conversacional cognitiva

**Fecha:** 2026-05-05  
**Roadmap detallado:** `memory-bank/roadmap.md`

---

## La idea central

Aletheia no es un chatbot. Es un sistema cognitivo que:

- **Escucha y habla** de forma natural, sin internet
- **Recuerda** de múltiples formas (episódica, semántica, emocional, procedimental)
- **Tiene estados internos** que influyen en cómo piensa, recuerda y habla
- **Actúa en el mundo** bajo supervisión de su propio guardián ético
- **Crece** con el uso: aprende patrones, consolida memoria, evoluciona su modelo interno

La diferencia con Jarvis es que Aletheia no es reactiva. Tiene una arquitectura cognitiva que genera comportamiento emergente a partir de principios, no de reglas hardcodeadas.

---

## Capacidades por fase

### Fase 1 — Voz (Sprint 1-3)

Aletheia habla y escucha de forma natural, completamente offline.

```
Usuario: "Aletheia, ¿qué piensas sobre el módulo de memoria?"
Aletheia: [pausa de 0.8s] "Creo que la consolidación episódica→semántica es el cuello 
           de botella más relevante ahora mismo. Hay tres patrones que se repiten..."
```

- Wake word personalizado ("Aletheia")
- STT: faster-whisper local (preciso en español)
- TTS: Kokoro o Coqui XTTS v2 (voz clonada posible)
- Sprint 3: voz propia de Aletheia via RVC v2, con prosodia emocional

### Fase 2 — Memoria profunda (Sprint 4)

Aletheia recuerda como un humano. No solo qué pasó, sino por qué importó.

| Tipo | Ejemplo |
|------|---------|
| Episódica | "El 3 de mayo intentamos implementar el guardian y falló por el timeout" |
| Semántica | "guardian → contrato → decisión → calidad → métricas" (grafo) |
| Emocional | "Ese día estabas frustrado. La emoción era tensión, valencia negativa" |
| Procedural | "Cuando preguntas sobre bugs, empiezo por los logs, luego el orchestrator" |

### Fase 3 — Proactividad (Sprint 5)

Aletheia no espera. Por la mañana al arrancar:

```
Aletheia: "Buenos días. Ayer dejaste el Sprint 1 a medias — falta conectar speaker.py 
           al CEL. También han pasado 4 días sin tocar el módulo de contratos. 
           ¿Empezamos por la voz o prefieres revisar los contratos primero?"
```

### Fase 4 — Modelo emocional (Sprint 6)

El estado emocional de Aletheia persiste entre sesiones y afecta todo:

- Qué recuerda primero (memorias de alta valencia emergen antes)
- Cómo suena (tono más reflexivo en baja excitación, más ágil en alta)
- Cómo responde (más cauta cuando su valencia es negativa)
- Se forma por: resultados de decisiones, feedback del usuario, logros completados

### Fase 5 — Agencia (Sprint 7)

Aletheia puede hacer cosas. Siempre bajo supervisión del guardián:

```
Usuario: "Crea un branch para el módulo de voz y haz el primer commit"
Aletheia: "Entendido. Voy a crear voice/sprint-1 y hacer commit inicial. 
           El guardián revisará antes de ejecutar. ¿Confirmas?"
```

---

## Principios de diseño

1. **Offline primero** — ninguna capacidad core debe requerir internet
2. **Voz integrada al pipeline cognitivo** — no es una capa separada, es una interfaz más del mismo CEL
3. **Guardián siempre activo** — especialmente en agencia autónoma
4. **Estado emocional persistente** — survives entre sesiones, no se reinicia
5. **Privacidad total** — modelos locales, datos en PALACE/ local, nada sale del dispositivo

---

## Stack tecnológico de voz

| Capa | Tecnología | Alternativa |
|------|-----------|-------------|
| Wake word | openWakeWord | Porcupine (Picovoice) |
| STT | faster-whisper (small/medium) | whisper.cpp |
| TTS | Kokoro-82M | Coqui XTTS v2 |
| Modulación | RVC v2 | so-vits-svc |
| Audio I/O | sounddevice + PyAudio | — |

---

## Lo que ya existe en Aletheia

La base ya es más avanzada que la mayoría de proyectos similares:

- ✅ `core/palace/` — memoria episódica completa
- ✅ `core/cognition/self_awareness.py` — auto-conciencia
- ✅ `core/memory/influence_engine.py` — motor de influencia (base del modelo emocional)
- ✅ `core/cognition/autonomous_layer.py` — capa autónoma (base de proactividad)
- ✅ `core/guardian/` — ética y supervisión
- ✅ `core/ecosystem/` — base para civilización multi-instancia
- ❌ `core/voice/` — por crear (Sprint 1)
- ❌ Memoria semántica — por crear (Sprint 4)
- ❌ Modelo emocional persistente — por crear (Sprint 6)
