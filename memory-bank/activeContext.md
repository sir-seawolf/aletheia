# Active context

**Current focus**: Preparación para subida a GitHub. Código limpio, sin datos personales. Pipeline cognitivo funcional end-to-end.

**In progress**:

- [x] Conexiones verificadas (SQLite, Ollama, FastAPI, PALACE)
- [x] Launcher.bat corregido (encoding, tests removidos del arranque, kill de puertos)
- [x] Frontend compilando (recharts instalado, App.css reparado)
- [x] Pipeline devuelve domain/question correctos
- [x] LLMRouter corregido para llamar Ollama directamente
- [x] .pip-installed ya implementado en launcher.bat (caché de instalación)
- [x] .gitignore actualizado — PALACE/IDENTITY/, PALACE/CREACION/, dumps excluidos
- [ ] Verificar guardian_block = False con Ollama real (requiere Ollama corriendo)

**Decisions (recent)**:

- LLMRouter.generate() bypassea el Universe Stack (devolvía "From memory/palace") y llama Ollama directamente con fallback a mock
- guardian_strict se activa solo en FULL_PIPELINE mode (no en FAST_PATH)
- Tests removidos del flujo de arranque del launcher (solo en opción [3])
- PALACE/IDENTITY/ y PALACE/CREACION/ excluidos de git (datos personales de usuario real)

**Open questions**:

- ¿El guardian bloqueará con Ollama real? (insight debería ser >50 chars con respuesta real)
