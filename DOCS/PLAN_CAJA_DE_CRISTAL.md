# Plan — Caja de Cristal: el expediente de ejecución de cada señal

> **Tesis del feature:** la caja negra de la IA no se abre — se rodea, se verifica y se mide. Cada señal
> guarda la **traza de ejecución escrita por el orquestador** (no por el modelo): qué datos entraron, qué
> regla decidió cada bifurcación con qué valores, qué modelo respondió en cuántos ms, y qué llamada nunca
> se hizo. Cualquier señal de ayer se **rebobina** paso a paso, como la caja negra de un avión.
>
> Vocabulario disciplinado (importante para el Q&A): decir **"replay de la grabación"**, nunca
> "re-ejecutar" (el LLM no es determinista — la grabación es la única fuente de verdad de lo que pasó).
> Decir **"trazabilidad operativa"**, no "auditoría legal". Decir **"caja de vidrio alrededor de la caja
> negra"**, nunca "resolvimos la caja negra".

Este plan fue verificado adversarialmente contra el repo (spikes ejecutados con las versiones pineadas,
datos de demo comprobados contra `data/`). Las fases completas suman **~4–5 días** — y la final
presencial es el **18 de julio (Biblioteca ESPOL, Edificio 7A)**, así que la sección 0 define el recorte
real para mañana. Las fases completas quedan como plan post-final / roadmap del pitch.

---

## 0. La realidad del calendario: qué hacer HOY (17-jul) para MAÑANA (18-jul)

Las reglas de Fase 1 dicen que tras el cierre no se incorporan funcionalidades nuevas y que el tiempo
presencial es para optimización técnica, corrección de errores, despliegue y pitch. **Primera acción de
hoy: preguntar a los organizadores qué se permite construir/mostrar en la final.** Según la respuesta:

### Escenario A — no se puede codear funcionalidad nueva (el seguro; asumir este por defecto)
Todo el valor va al **pitch**, y alcanza, porque la sustancia ya existe en el código entregado:
- **La diapositiva de la escalera** (sección 4): 5 de los 7 peldaños ya existen en el código de la
  Fase 1 entregada (acotar, anclar, tipar, medir-embrión, y la arista condicional que decide gasto).
- **Demo de lo existente, narrada con el lenguaje del feature**: generar el briefing de Credit & Macro
  en vivo y narrar la arista real: *"HYG quedó neutral con confianza 0.33 — menor que 0.50 — y el grafo
  decidió NO gastar la llamada del Asesor: quedó en monitoreo"* (verificado: HYG/n007 rutea a Monitor
  con los datos actuales). La regla existe, es código entregado, solo no tiene visor todavía.
- **Este documento como roadmap** con mockup del TraceDrawer (una imagen basta) + Q&A ensayado.

### Escenario B — se permite codear y el equipo tiene la tarde/noche de hoy (~6-8 h)
Recorte quirúrgico — solo lo que cabe y degrada con gracia:
1. **Fase 0 mínima** (TraceRecorder + captura en el camino del briefing y en HU2, sin telemetría de
   reintentos) — ~3 h.
2. **Fase 1** (columna + ALTER en Neon + endpoint + `has_trace`) — ~1.5 h.
3. **TraceDrawer estático**: timeline vertical de eventos con los dos carriles, SIN grafo SVG animado,
   SIN replay con botones (solo render de la traza persistida) — ~2-3 h.
4. Pre-generar las señales de los beats DESPUÉS de deployar (para que tengan traza).
   
   Fases 2 (SVG/replay), 3 (vivo) y 4 (contrafactual) van a la diapositiva de roadmap. **No intentar el
   SSE en vivo para mañana**: un solo intento frente al jurado con infraestructura de horas de vida es
   la definición de riesgo evitable.

En ambos escenarios: los beats de demo que dependen de features no construidos se **narran sobre el
roadmap, nunca se prometen como existentes**.

---

## 1. Qué está verificado (spikes reales, no supuestos)

- `langgraph==0.2.60` soporta `graph.stream(stream_mode='updates')` — probado.
- **Un objeto mutable en la clave `trace` de `AgentState` viaja POR REFERENCIA** a los nodos y a
  `route_after_analyst` (spike ejecutado: 4 eventos acumulados en el objeto original, sin
  copia/serialización porque no hay checkpointer). El diseño TraceRecorder-por-estado funciona.
- SSE end-to-end (thread + `queue.Queue` + `StreamingResponse` + heartbeat como comentario) funciona con
  `fastapi==0.115.6`/`uvicorn==0.32.1` — spike ejecutado, eventos incrementales sin buffering. Headers:
  `Cache-Control: no-cache`, `X-Accel-Buffering: no`. No hay que tocar `vite.config.ts` (no hay proxy).
- `Dockerfile` corre 1 worker → registro en memoria seguro en prod.
- `AnalystLLMOutput.reasoning` se genera y se descarta en `analyst_node.py` — capturarlo es gratis.
- `create_all` **NO agrega columnas** a tablas existentes (probado) → migración manual obligatoria.
- Datos de demo verificados: ECU2035/n026 → +2.35% → positive 0.71; HYG/n007 → −0.15% → neutral 0.33 →
  Monitor; AAPL→Monitor y MSFT/NVDA→Advisor en el briefing de Tech Megacaps con DB fresca.
- 39 tests en verde; `run_pipeline` no se toca.

**Hallazgo crítico que el diseño resuelve:** dos de los tres caminos de generación no pasan por el grafo
(`generate_signal` llama `run_analyst` directo en [signals.py:51](../backend/services/signals.py); la
rama de reuso del briefing tampoco ejecuta `graph.invoke`). Por eso se instrumenta **el pipeline**, no
`graph.invoke` — y por eso el beat de la arista se demuestra vía briefing, no vía HU2.

---

## 2. Diseño central: `TraceRecorder`, una sola fuente de eventos

`backend/agents/trace.py` — colector que los tres caminos alimentan; sirve para persistir y transmitir:

```python
class TraceRecorder:
    def __init__(self, llm_mode, model, path, on_event=None): ...
    def event(self, type: str, **data) -> None: ...   # append + callback (vivo)
    def to_json(self) -> dict: ...                    # {"v": 1, "runs": [...]}
```

### Contrato de la traza (`v:1`)
- **`runs[]`** (lista, no un run único): cada corrida que tocó la señal anexa un run — la generación
  original, y luego p. ej. un reuso parcial del briefing. Resuelve la sub-rama "señal sin tarea" de
  [briefing.py](../backend/services/briefing.py), que SÍ llama al Asesor (LLM real).
- `run`: `{llm_mode, model, path, started_at, truncated: false}` con
  `path ∈ "analysis" | "briefing" | "briefing-reuse"`.
- `events[]`: `{t_ms, type, ...}`:
  - `node_start` / `node_end` (`node`, `duration_ms`, `output_digest`)
  - `edge_decision` (`edge`, `rule` — string literal, `inputs`, `threshold`, `target`, `llm_cost`)
  - `llm_call` (`provider`, `model`, `latency_ms`, `attempts`)
  - `reuse` (`signal_id`, `scope: "full" | "signal-only"`, `llm_calls`) — en `signal-only` se registran
    además el `edge_decision` y el `llm_call` del Asesor si ocurre. **El badge "$0" solo aplica a
    `scope: "full"`.**
  - `gate` (reservado, shape fijado YA para no romper `v:1` después:
    `{check, claimed_value, source_value, verdict: "pass" | "fail"}`)
- **Cache-hit de HU2** (`generate_signal` sin `force`): NO escribe traza; la UI muestra la grabación
  original con cabecera *"Grabación de la generación original — {started_at}"*.
- **Regla de compatibilidad:** tipos de evento y campos nuevos son aditivos y NO suben `v`; el visor
  ignora tipos que no conoce. `v` solo sube ante cambios incompatibles.
- **Truncado estructural, nunca de bytes:** `reasoning` cap ~1.500 chars con "…", tope ~100 eventos
  (descarte por el medio), `truncated: true` en el run + aviso en el visor. Test unitario del recorte.
- **Determinismo para tests:** en mock, la SECUENCIA (types/nodes/edges/targets/digests) es determinista;
  el snapshot normaliza/excluye `t_ms`, `latency_ms`, `started_at`.

### Flujo
- Por el grafo: clave `trace` en `AgentState` (verificado por referencia); `route_after_analyst`
  registra su propia decisión (el evento nace donde se decide).
- `run_analyst(news, price_comparison, llm=None, trace=None)` para HU2.
- Telemetría LLM: `_with_retry` gana contador de intentos; `generate_structured` registra
  `{provider, model, latency_ms, attempts}` (cambio chico en `llm.py`).
- **UI con dos carriles etiquetados** (defensa contra la circularidad): "Registrado por el orquestador"
  vs "Declarado por el modelo".

---

## 3. Fases completas (post-final / si hay más tiempo del esperado)

### Fase 0 — Unificar la captura en los 3 caminos (~0.5–1 día)
`trace.py` + firmas + registro en nodos/arista/reuso + telemetría `llm.py`.
**Criterio de salida:** señal por CUALQUIER camino produce traza coherente; snapshot de secuencia en
mock (neutral→monitor y positive→advisor, patrón `FakeLLM` de `tests/test_graph_routing.py`).

### Fase 1 — Persistencia + API (~0.5 día)
- `Signal.execution_trace` (JSON nullable) + **`has_trace: bool` en `SignalOut`** (no engorda listados;
  la UI decide mostrar el botón sin llamada extra).
- Migración manual en Neon ANTES del deploy (las TRES columnas nuevas de la rama):
  ```sql
  ALTER TABLE signal ADD COLUMN execution_trace JSON;
  ALTER TABLE signal ADD COLUMN attribution JSON;
  ALTER TABLE taskalert ADD COLUMN executive_summary JSON;
  ```
- `GET /api/signals/{signal_id}/trace` → **404 con detail "Señal anterior a la trazabilidad"** para
  trace NULL (señales legacy), con test.
- Tests: trace por los 3 caminos; `force=true` crea señal nueva con traza propia sin tocar la anterior;
  404 legacy.

### Fase 2 — TraceDrawer + grafo SVG + replay (~1–1.5 días; es la estimación más apretada)
- `TraceDrawer.tsx` (slide-over ~400px, dos carriles) + `PipelineGraph.tsx` (SVG a mano, 5 nodos fijos +
  entrada "Reuso"; sin librerías). Replay con timer (pasos comprimidos a máx ~800 ms) + ◀ ▶.
- Botón "Ver ejecución" (deshabilitado con tooltip si `has_trace=false`).
- Recorte declarado si se atrasa: replay solo auto-play, sin botones paso a paso.

### Fase 3 — En vivo (~0.5–1 día) — flourish, nunca prerequisito de la demo
- **Dos endpoints** (el beat 1 lo exige): `GET /api/signals/generate/stream` y
  `GET /api/briefing/stream?watchlist=...` (eventos `item_start`/`item_end` por instrumento).
- El worker thread **crea su propia `Session(engine)`** — el endpoint SSE NO usa
  `Depends(get_session)` (la session del request no es thread-safe ni sobrevive al generator).
- `queue.get(timeout=1s)` → heartbeat + detección de desconexión.
- **Semántica de reconexión:** el run se registra con `run_id`; reconectar re-adjunta al run en curso
  (nunca relanza la generación — evita señales duplicadas y doble gasto en pleno pitch). Consumir con
  `fetch` + ReadableStream (sin auto-retry de EventSource).
- Registro en memoria: evicción al completar +5 min, tope ~50 runs (LRU), estado terminal
  `done`/`error` para que el polling se detenga.
- Fallback de polling cada 1 s (indistinguible con nodos de 2–6 s). Probar en Render real antes del
  pitch. Tests: `test_sse_stream_mock` (orden de eventos + terminal), no-duplicación en reconexión.

### Fase 4 — "¿Qué pesó más?": atribución contrafactual (~0.5 día)
- 2 re-ejecuciones controladas (`sin_movimiento`: `change_pct=0`; `sin_titular`: headline/summary
  neutralizados) → `Signal.attribution` (JSON cache) + `POST /api/signals/{id}/attribution`.
- **Migración propia**: `ALTER TABLE signal ADD COLUMN attribution JSON;` en Neon antes del deploy.
- Ejemplo correcto en mock: ECU2035 `positive 0.71 → neutral 0.30` al quitar el movimiento (la fórmula
  mock da 0.30, no 0.42). **Limitación conocida: en mock el probe `sin_titular` es un no-op** (el mock
  solo mira `change_pct`) — o se extiende el mock (~5 líneas: headline neutralizado reduce confidence) o
  el probe de titular se demuestra solo con LLM real.
- La atribución **persiste `llm_mode`/`model`** y el panel compara contra el `run.llm_mode` de la traza:
  si difieren, avisa "sondeo con proveedor distinto al original" (o re-sondea).
- Etiqueta honesta: "sondeo empírico (2 re-ejecuciones controladas)". Test: `test_attribution_mock`.

### Fase 5 — Endurecimiento pre-demo
Los **tres** ALTER aplicados (signal.execution_trace, signal.attribution, taskalert.executive_summary) ·
señales de beats pre-generadas DESPUÉS del deploy de trazabilidad · SSE probado en Render real (si se
construye Fase 3) · ensayo cronometrado · suite completa en verde.

---

## 4. Cómo venderla: la escalera de transparencia

### La diapositiva única
Caja negra al centro, siete anillos — con etiqueta honesta de estado:

1. **Acotar** — el LLM solo clasifica/redacta; datos, precio, ruteo y publicación son código ✅ entregado
2. **Anclar** — contexto whitelisteado ✅ entregado
3. **Tipar** — 4 clases, confianza acotada, Pydantic ✅ entregado
4. **Verificar** — cada cifra contra el dataset (Compliance Gate) 🗺 roadmap
5. **Medir** — track record/calibración ✅ embrión entregado · Centinela 🗺 roadmap
6. **Sondear** — contrafactuales 🗺 roadmap (Fase 4)
7. **Registrar** — el expediente de ejecución 🗺 este plan (Fases 0–3)

### Guion de demo (beats corregidos y verificados contra los datos)
1. **"Un clic, dos rutas"** — briefing Tech Megacaps con DB fresca: AAPL→Monitor, MSFT/NVDA→Advisor.
   *Escenario A: se narra sobre la generación normal. Con Fase 3: visor en vivo (requiere el endpoint
   `/api/briefing/stream`). Plan B siempre: replay de trazas persistidas.*
2. **"El titular alarmista que no engaña al grafo"** — vía briefing **Credit & Macro**: HYG/n007
   ("Global bond yields surge…") suena a pánico pero HYG se movió −0.15% → `neutral · 0.33 < 0.50 →
   Monitor`, badge "$0". *(NO usar TLT/HU2 para este beat: el camino HU2 no rutea — verificado.)*
3. **"Rebobinar una decisión de ayer"** — replay de la traza persistida de ECU2035 (pre-generada tras el
   deploy). Requiere Fases 0–2.
4. **Clímax — "¿Qué pesó más?"** — contrafactual en vivo (Fase 4): sin el movimiento de precio, la señal
   cae `positive 0.71 → neutral 0.30`. *En mock solo el probe de precio es demostrable.*

### Logística del pitch (rellenar cuando los organizadores confirmen el formato)
- **Timing parametrizado** (ej. para 5 min): gancho 30s · escalera 60s · beats 45s c/u · cierre 30s.
- **Roles**: driver (clics), speaker (narración), y dueño asignado de cada respuesta del Q&A.
- **Checklist de venue (Biblioteca ESPOL)**: probar red del venue con la app desplegada · hotspot de
  respaldo · app precargada y backend caliente · **video pregrabado del flujo como último recurso** ·
  el plan B primario del vivo es SIEMPRE el replay de trazas persistidas (no depende de Gemini ni de la
  red del LLM). *Nota: cambiar `LLM_MODE` en Render requiere redeploy de minutos — el mock NO es un
  fallback accionable a mitad del pitch.*

### Frases de pitch
- *"Cuando una IA financiera dice 'confía en mí', la respuesta correcta es 'muéstrame'. No explicamos la
  decisión con más texto del mismo modelo del que se duda: mostramos la ejecución real — qué agente
  corrió, qué regla se evaluó, y qué llamada nunca se hizo."*
- *"Esta arista no es un dibujo: es la regla 'neutral con confianza 0.33, menor que 0.50' evaluándose en
  vivo — acaban de ver al grafo decidir que este titular alarmista no merecía gastar ni un token."*
- *"La caja negra no se abre — se rodea. Y cuando quieres saber qué pesó en una decisión, se lo
  preguntamos al experimento, no al modelo: quitamos el precio, y la señal cae."*

### Q&A preparado (respuestas ensayadas, un dueño por pregunta)
| Ataque | Respuesta |
|---|---|
| "El LLM sigue siendo caja negra por dentro" | Cierto — nadie abre los pesos (interpretabilidad mecanicista es frontera de investigación). Reducimos la superficie opaca al mínimo teórico y registramos el 100% del resto: caja de vidrio alrededor de la caja negra. |
| "¿Esto no es LangSmith reinventado?" | LangSmith es observabilidad para desarrolladores en un SaaS externo. Esto es evidencia para el **revisor regulado**: dentro del producto, en español, acoplada al flujo de revisión que ya existe. |
| "¿Pueden reproducir la ejecución?" | Reproducimos la **grabación**, no el vuelo — caja negra de avión. Precisamente porque el modelo no es determinista, la grabación del orquestador es la única fuente de verdad. |
| "La confianza es autoreporte del modelo" | Por eso no la tratamos como verdad: es compuerta de costo/atención (lo peor que pasa es que una señal vaya a monitoreo — nunca se pierde), el track record mide su calibración, y el contrafactual la sondea. |
| "¿Valor legal de auditoría?" | **Trazabilidad operativa**: el sustrato de una pista de auditoría, no su forma jurídica. Identidad del revisor y append-only son fase 2 declarada del roadmap. |

---

## 5. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| **La final es mañana** | Sección 0: escenario A por defecto; escenario B solo con confirmación de organizadores y recorte quirúrgico |
| `create_all` no agrega columnas | ALTER manual por CADA columna nueva (execution_trace Y attribution), checklist Fase 5 |
| SSE en Render free / reconexión | Heartbeat 15s · re-adjuntar por run_id (nunca relanzar) · fetch sin auto-retry · polling fallback · probar en Render real |
| Gemini lento/caído en vivo | Plan B primario = replay de trazas persistidas (cero dependencia de Gemini); video pregrabado como último recurso; el mock NO es conmutables en vivo (requiere redeploy) |
| Session de DB en el thread SSE | El worker crea su propia `Session(engine)`; el endpoint no usa `Depends(get_session)` |
| Beat irrealizable por camino equivocado | Beats fijados sobre caminos verificados (HYG vía briefing, no TLT vía HU2) |
| Sobre-prometer | Vocabulario disciplinado + escalera con etiquetas ✅/🗺 + Q&A con dueños |
