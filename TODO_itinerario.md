# Itinerario — Expansión LLM (gratis), Imagen y Selección Dinámica Online

**Status:** 🆕 NUEVO — propuesto y priorizado  
**Objetivo:** mejorar velocidad, fiabilidad y calidad de respuestas cuando haya red, con políticas predefinidas por tipo de tarea; ampliar catálogo de proveedores (incluyendo opciones gratuitas), y añadir capacidad de imagen/multimodal.

---

## 0) Contexto y criterios de diseño

- Mantener **compatibilidad** con arquitectura actual (`LLMRouter`, `RoutingIntelligence`, providers en `core/llm/providers/`).
- Preservar prioridad de seguridad/privacidad (local-first cuando aplique).
- Selección dinámica basada en métricas reales y premisas configurables.
- Evitar romper contratos actuales (`core/contracts/*` y flujos de API).

---

## 1) Fase Discovery — Proveedores y capacidades (texto + imagen)

### 1.1 Proveedores LLM gratuitos/low-cost a evaluar
- [ ] Inventariar proveedores cloud ya soportados y su estado real (`OpenAI`, `DeepSeek`, `Groq`, `Mistral`, etc.).
- [ ] Añadir shortlist de proveedores “free tier” y/o económicos (incluyendo opciones chinas cuando sea viable por API pública y estabilidad).
- [ ] Definir matriz por proveedor/modelo:
  - [ ] Latencia media
  - [ ] Tasa de éxito
  - [ ] Calidad percibida por tipo de tarea
  - [ ] Límite de cuota/rate limit
  - [ ] Coste estimado por 1K tokens
  - [ ] Soporte imagen/multimodal
  - [ ] Requisitos de clave/API y región

### 1.2 Imagen / multimodal
- [ ] Identificar providers/modelos compatibles con input de imagen.
- [ ] Definir casos de uso iniciales:
  - [ ] “Describe imagen”
  - [ ] “Extrae texto (OCR básico asistido por LLM)”
  - [ ] “Clasificación visual simple”
- [ ] Elegir estrategia de fallback si imagen no disponible (texto-only).

---

## 2) Fase Métricas Online — Benchmark continuo y actualización de listado

### 2.1 Registro de métricas por proveedor/modelo
- [ ] Extender métricas para guardar por `provider:model`:
  - [ ] `latency_ms_p50/p95`
  - [ ] `success_rate_24h`
  - [ ] `timeout_rate`
  - [ ] `error_rate`
  - [ ] `estimated_cost`
  - [ ] `quality_score` (heurístico)
- [ ] Persistencia local (SQLite/memory) con ventana temporal.

### 2.2 Función “actualizar listado”
- [ ] Crear función para refrescar catálogo de modelos/proveedores disponibles al detectar red.
- [ ] Añadir política de refresco:
  - [ ] Manual (botón)
  - [ ] Automática (TTL configurable, p. ej. cada 30-60 min)
- [ ] Marcar estado de disponibilidad:
  - [ ] online / degradado / no disponible

### 2.3 Endpoint(s) de soporte
- [ ] Exponer endpoint para forzar refresh de catálogo y benchmark corto.
- [ ] Exponer endpoint de ranking actual por política.
- [ ] Exponer endpoint para capacidades multimodales por proveedor.

---

## 3) Fase Routing por premisas predefinidas (rápido / fiable / calidad / tema)

### 3.1 Premisas (políticas) base
- [ ] Definir políticas seleccionables:
  - [ ] `fastest` (mínima latencia)
  - [ ] `most_reliable` (máxima tasa de éxito)
  - [ ] `best_quality` (mejor score de calidad)
  - [ ] `best_for_topic:<topic>` (routing temático)
  - [ ] `balanced` (combinación ponderada)
- [ ] Añadir pesos configurables por política.

### 3.2 Clasificación por tema de consulta
- [ ] Etiquetar tarea entrante (code, reasoning, creative, summary, vision, etc.).
- [ ] Mantener clasificador determinista/simple (sin sobrecargar con LLM cuando no haga falta).
- [ ] Mapear temas a proveedores recomendados (tabla editable).

### 3.3 Integración en router
- [ ] Integrar política seleccionada en `RoutingIntelligence`.
- [ ] Aplicar fallback secuencial inteligente (p. ej. fastest→reliable).
- [ ] Mantener guardas de privacidad y contrato.

---

## 4) Fase Imagen/Multimodal — Implementación inicial

- [ ] Definir interfaz común para llamada multimodal en providers compatibles.
- [ ] Soportar payload de imagen (URL/base64) en capa API interna.
- [ ] Añadir normalización de respuesta multimodal al formato actual de salida.
- [ ] Añadir fallback explícito cuando provider no soporte imagen.

---

## 5) UX / Configuración (usuario final)

- [ ] Añadir selector visible de política:
  - [ ] “Más rápido”
  - [ ] “Más fiable”
  - [ ] “Más calidad”
  - [ ] “Mejor para este tema”
- [ ] Mostrar ranking de providers en tiempo real (top N).
- [ ] Mostrar “por qué se eligió este provider” (explicabilidad breve).
- [ ] Añadir control para “actualizar listado ahora”.
- [ ] Mostrar etiqueta multimodal cuando esté disponible.

---

## 6) Archivos candidatos (implementación técnica)

### Backend
- [ ] `core/llm/router.py` — aplicar política de selección dinámica + fallback
- [ ] `core/routing/intelligence.py` — score multicriterio y ranking por premisa
- [ ] `core/llm/providers/online.py` — discovery/health/check de modelos online
- [ ] `core/bootstrap/runtime.py` — endpoints refresh/ranking/capabilities
- [ ] `core/metrics/*` — persistencia y cálculo de métricas por provider/model

### Frontend
- [ ] `aletheia-ui/src/App.js` y/o Settings — selector de política y refresh catálogo
- [ ] Componentes de estado/ranking (si aplica en panel actual)

### Config
- [ ] `PALACE/config/preferences.json` (vía API) — guardar política y pesos

---

## 7) Testing y validación

- [ ] Unit tests scoring/ranking de políticas.
- [ ] Tests de fallback ante timeout/error.
- [ ] Tests de refresh de catálogo con/ sin red.
- [ ] Tests de regresión para no romper rutas actuales de LLM.
- [ ] Pruebas manuales UX con escenarios:
  - [ ] red estable
  - [ ] red degradada
  - [ ] provider caído
  - [ ] consulta con imagen

---

## 8) Entregables por sprint (propuesto)

### Sprint A (rápido valor)
- [ ] Política `fastest` + `most_reliable`
- [ ] Endpoint refresh catálogo
- [ ] Ranking básico en UI

### Sprint B
- [ ] `best_quality` + `best_for_topic`
- [ ] Métricas persistentes 24h/7d
- [ ] Explicabilidad de selección

### Sprint C
- [ ] Imagen/multimodal v1
- [ ] Fallback multimodal robusto
- [ ] QA completo + documentación final

---

## 9) Definición de “hecho” (DoD)

- [ ] Usuario puede elegir política de selección en UI.
- [ ] Sistema actualiza listado y ranking al estar online.
- [ ] Selección mejora objetivamente según métrica objetivo (latencia/fiabilidad/calidad).
- [ ] Existe fallback robusto sin romper contrato de salida.
- [ ] Soporte imagen funcional en al menos 1 provider estable.
- [ ] Tests críticos en verde.
