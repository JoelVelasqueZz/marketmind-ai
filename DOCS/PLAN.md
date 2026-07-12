# Plan — Track 5: Inteligencia de Mercado y Recomendaciones Informadas por Noticias

## Contexto

Hackathon Agentic Scale (TAWS/ESPOL). **Deadline: domingo 12 de julio 2026, 23:59** (hoy 11 julio → quedan ~30h). Hay que construir un sistema de **dos agentes IA financieros** (Track 5) que convierta noticias + datos de mercado en **señales explicables** sobre renta variable, crédito, criptoactivos y otros activos, **sin ejecutar operaciones ni prometer rendimientos**. El MVP debe cumplir las **3 Historias de Usuario** del PDF del track (cada una con sus criterios de aceptación):

- **HU1 – Radar de noticias y activos:** noticias recientes de ≥2 fuentes (o feed de prueba) con **fuente y fecha**; cada noticia ligada a instrumentos (acciones/crédito/cripto/otros); **filtros** por tipo de instrumento, activo y antigüedad.
- **HU2 – Señal explicable de impacto:** clasifica impacto en **positivo/negativo/neutral/incierto** + **nivel de confianza**; compara el evento contra movimiento de precio/histórico; explica con **evidencia y fuentes** + **disclaimer** (no es asesoría personalizada, no garantiza resultados).
- **HU3 – Briefing con revisión humana:** resumen por watchlist/instrumento (noticia + movimiento + acción de investigación sugerida); marcar cada señal como **revisada / escalada / descartada** guardando la **justificación**; **no compra/vende**: crea **alertas o tareas** para revisión humana.

### Entregables obligatorios (guía de la organización — no solo código)

1. **Video** (YouTube o nube, 3 min).
2. **ZIP del código**.
3. **Documento técnico** — debe incluir explícitamente: diagrama de arquitectura (agentes, canales, integraciones externas), track asignado, tipo de negocio al que aplica, cómo se integraría a un sistema empresarial existente. Es un entregable propio (`docs/DOCUMENTO_TECNICO.md`), separado del README de desarrollo.
4. **Link del repositorio** — debe quedar **público** y accesible durante toda la evaluación.
5. **Link de despliegue** — demo **funcionando en vivo**, no solo local. Esto se agrega como fase temprana del build (ver más abajo), no como última tarea.

### Criterios de evaluación (para priorizar esfuerzo)

1. **Viabilidad técnica / arquitectura agéntica** — lógica separada de la interfaz, manejo de continuidad de conversación, confiabilidad verificable (no prototipo frágil).
2. **Impacto / ajuste al track** — qué tan bien resuelve el problema real, viabilidad como producto comercial, contexto financiero/regulatorio local.
3. **Mitigación de riesgos / antialucinación** — el agente no debe inventar datos financieros; necesita mecanismos para respaldar respuestas (citas a fuentes, comparación con datos reales/mock, disclaimers).
4. **Demo y experiencia de usuario** — clara, fluida, refleja capacidades reales (no solo apariencia).
5. **Evidencia de pruebas** — mínimo README con casos probados manualmente; ideal: `tests/` con pytest, incluyendo tests de los nodos del grafo de estados (LangGraph) y mocks de la API del LLM.

**Decisiones tomadas con el usuario y su equipo:**

- Stack: **FastAPI (backend) + React (frontend)**.
- Datos: **mock** curado (100% confiable para la demo), detrás de una interfaz que permite añadir datos live después.
- **LLM: Gemini API como motor principal** — el equipo tiene acceso gratuito vía Google AI Pro para estudiantes (1000 créditos/mes) y califica al premio "Best Use of Google Gemini". La capa `LLMClient` se mantiene **provider-agnóstica** (`MODE=mock|gemini|claude`) para poder cambiar de proveedor con una sola variable de entorno si hace falta.
- **Orquestación de agentes: LangGraph.** El organizador la menciona explícitamente como ejemplo de "nivel intermedio" de testing, y demuestra arquitectura agéntica real (grafo de estados con nodos, no solo llamadas sueltas al LLM) — pesa directamente en el criterio de evaluación #1.
- **Frontend: se reutiliza el mockup HTML "MarketMind AI"** que ya construyó un compañero (`DOCS/marketmind_dashboard_mockup/...`), portando esas páginas a componentes React reales conectados a la API. Su `DESIGN.md` (paleta navy "Deep Tech", Inter + JetBrains Mono, tokens de color/tipografía/espaciado) es la fuente de verdad visual. Queda como stretch de Fase 4 pulir con las skills de diseño/animación que mencionó el usuario (`frontend-design`, "UI IX Pro Max", skill de animaciones de emilkowalski) — **no se instalan ni se usan todavía**, solo quedan anotadas como opción de pulido si sobra tiempo.
- **Despliegue: gratuito, recomendado por mí, fácil de migrar** — ver sección Despliegue. Se monta desde Fase 0 para tener el link de demo vivo cuanto antes, no al final.

**Regla de oro de diseño:** los agentes **nunca** tienen una herramienta de "ejecutar operación". El Asesor solo emite alertas/tareas → cumple el requisito regulatorio del Track por construcción.

## Arquitectura

```
Frontend (React SPA, Vite + TS + Tailwind — porteado de MarketMind AI)
   Tabs: Radar (HU1) · Señales/AI Analysis (HU2) · Briefing (HU3)
        │  HTTP JSON
        ▼
Backend (FastAPI + Uvicorn)
   Routers → Services → LangGraph (StateGraph: analyst_node → advisor_node) → LLM client → Gemini API | Mock LLM
                            │
                            ├─ NewsProvider  (Mock | live: NewsAPI/RSS)   ← interfaz
                            ├─ PriceProvider (Mock | live: yfinance/CoinGecko) ← interfaz
                            └─ SQLite (SQLModel): Signal + review state, Task/Alert
```

- **Agente 1 — Analista de Coyuntura de Mercados IA** (`agents/analyst_node.py`): nodo LangGraph que toma noticias (fuente/fecha/instrumentos) + histórico de precios y produce la **señal de impacto explicable** (HU2), salida estructurada (Pydantic): `impact`, `confidence`, `evidence[]`, `sources[]`, `price_comparison`, `disclaimer`.
- **Agente 2 — Asesor Financiero e Inversiones IA** (`agents/advisor_node.py`): nodo LangGraph que consume las señales del Analista y arma el **briefing por watchlist/instrumento** (HU3): noticia + movimiento asociado + **acción de investigación** sugerida. Genera **tareas/alertas**; jamás órdenes de compra/venta.
- **Grafo** (`agents/graph.py`): `StateGraph` con estado compartido tipado (TypedDict: news, prices, signals, briefing). Flujo completo `analyst_node → advisor_node` se usa para armar el briefing (HU3). El nodo `analyst_node` también se invoca de forma independiente para `/api/signals/generate` (HU2), sin pasar por el advisor. Los nodos son funciones puras testeables por separado (facilita el nivel intermedio de testing pedido).

## Stack técnico

- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLModel + SQLite, `langgraph`, `langchain-google-genai` (o `google-genai` SDK directo envuelto por `LLMClient`).
- **LLM:** Gemini (modelo configurable vía `LLM_MODEL`, default `gemini-flash-latest` — alias que siempre apunta al modelo flash vigente, evita romperse cuando Google retira una versión específica como pasó con `gemini-2.5-flash`). Salida estructurada vía schema Pydantic (`response_schema` de Gemini o parsing forzado). `LLMClient` con `MODE=mock|gemini|claude` — el modo mock permite construir y demostrar sin gastar créditos.
- **Frontend:** Vite + React + TypeScript + Tailwind, componentes portados del mockup MarketMind AI (`code.html` de cada página) usando los tokens de `DESIGN.md`.
- **Datos mock (`data/`):** `mock_news.json` (~25 noticias realistas, ≥2 fuentes nombradas p.ej. Reuters/Bloomberg, fechadas relativas a hoy, con instrumentos/sector/tema), `mock_prices.json` (histórico ~30 días para AAPL, MSFT, NVDA, TSLA, BTC, ETH, y un ETF de crédito p.ej. HYG/TLT), `watchlists.json`, `sources.json`.
- **Testing:** `tests/` con `pytest` — `test_analyst_node.py`, `test_advisor_node.py` (nodos del grafo con `LLMClient` en modo mock, sin red), `test_agent.py` (smoke: el grafo completo responde algo coherente), `test_api.py` (endpoints con TestClient de FastAPI).

## Despliegue

Objetivo: link de demo vivo **desde temprano**, con migración sencilla si un compañero consigue hosting de pago.

- **Backend:** Render (free tier) vía **Dockerfile** — un solo Dockerfile portable que también corre igual en Railway/Fly.io/cualquier otro si hace falta migrar (nadie tiene que reescribir nada, solo apuntar el nuevo servicio al mismo Dockerfile). SQLite como archivo en el disco del servicio (suficiente para demo; se documenta la limitación de que Render free reinicia el disco en redeploys).
- **Frontend:** Vercel o Netlify (free tier) — build estático de Vite apuntando a la URL pública del backend vía variable de entorno `VITE_API_URL`.
- **CORS:** backend configurado para aceptar el origin de producción del frontend desde Fase 0.

## Estructura de carpetas

```
track5/
  README.md                 .env.example            requirements.txt          Dockerfile
  docs/  DOCUMENTO_TECNICO.md   (diagrama arquitectura + track + negocio + integración empresarial)
  data/  mock_news.json  mock_prices.json  watchlists.json  sources.json
  backend/
    main.py            # FastAPI app, CORS, monta routers
    config.py  db.py   models.py  schemas.py
    providers/  news_provider.py   price_provider.py   # interfaz + Mock (+ live opcional)
    agents/     llm.py  prompts.py  graph.py  analyst_node.py  advisor_node.py
    services/   radar.py  signals.py  briefing.py
    routers/    news.py  signals.py  briefing.py  tasks.py
  tests/
    test_analyst_node.py  test_advisor_node.py  test_agent.py  test_api.py
  frontend/
    index.html  vite.config.ts  tailwind.config.js
    src/  main.tsx  App.tsx  api.ts  types.ts
          components/ Filters.tsx NewsCard.tsx SignalCard.tsx BriefingBoard.tsx ReviewControls.tsx Disclaimer.tsx
          pages/ Dashboard.tsx Radar.tsx Signals.tsx Briefing.tsx Watchlist.tsx
```

## Endpoints (contrato)

- `GET /api/instruments` — instrumentos + tipos (para poblar filtros).
- `GET /api/news?type=&asset=&max_age_days=&sector=&topic=` — **HU1**: noticias con fuente, fecha e instrumentos ligados; filtros aplicados server-side.
- `GET /api/signals?asset=` / `POST /api/signals/generate` — **HU2**: invoca `analyst_node` (solo), genera/persiste señales explicables.
- `GET /api/briefing?watchlist=` / `POST /api/briefing/generate` — **HU3**: invoca el grafo completo (`analyst_node → advisor_node`), briefing por watchlist.
- `POST /api/signals/{id}/review` `{status: revisada|escalada|descartada, justification}` — **HU3**: estado + justificación.
- `GET /api/tasks` · `POST /api/tasks` — alertas/tareas de investigación (nunca órdenes).

## Orden de implementación (MVP primero — slices verticales, deploy temprano)

**Qué construir primero:** el *walking skeleton* end-to-end (scaffold vacío desplegado) para asegurar el link de demo desde ya, y luego HU1 (mock news → Analista etiqueta/relaciona → API con filtros → UI Radar) como primer slice funcional real.

- **Fase 0 — Scaffold + deploy skeleton (~1.5h):** repo, `requirements.txt`, `Dockerfile`, `.env.example`, datos mock, SQLite/SQLModel, `LLMClient` con **modo mock**, esqueleto LangGraph (grafo con nodos vacíos), FastAPI + Vite/React con CORS. **Desplegar ya** en Render + Vercel (aunque sea un "hello world" conectado). Confirmar que el link de despliegue funciona de punta a punta antes de seguir.
- **Fase 1 — HU1 Radar (~2-3h):** `NewsProvider` mock + `/api/news` con filtros + página **Radar** (portada del mockup MarketMind AI, feed, filtros por tipo/activo/antigüedad, muestra fuente+fecha+instrumentos). Redeploy. **Primer slice demostrable.**
- **Fase 2 — HU2 Señales (~2-3h):** `PriceProvider` mock + `analyst_node` (LangGraph) produce señal estructurada vía Gemini (impacto+confianza+evidencia+fuentes+comparación de precio+disclaimer) + `/api/signals` + página **AI Analysis** (indicador de confianza circular, evidencia, comparación de precio, banner de disclaimer, como en el mockup). Redeploy.
- **Fase 3 — HU3 Briefing + revisión (~2-3h):** `advisor_node` (LangGraph) arma briefing por watchlist + persistencia de estado (revisada/escalada/descartada + justificación) + tabla de tareas/alertas + página **Briefings** (tablero con botones de acción, textarea de justificación, panel de tareas; disclaimer global — como en el mockup). Verifica el "no ejecuta compras/ventas": solo crea tareas. Redeploy.
- **Fase 4 — Tests + Documento técnico (~1.5-2h):** `tests/` con pytest (nodos del grafo con LLM mockeado, smoke test del agente, tests de endpoints); `docs/DOCUMENTO_TECNICO.md` con diagrama de arquitectura (mermaid), track asignado, tipo de negocio, integración a sistema empresarial existente; README de desarrollo con instrucciones de correr local + demo desplegada.
- **Fase 5 — Pulido + video + entrega (~2-3h):** disclaimers en todas las vistas, manejo de errores, calidad de datos semilla, guión de demo que mapea cada criterio de aceptación a un clic, grabar video de 3 min, empaquetar ZIP, verificar que repo quede público. Opcional/stretch si sobra tiempo: pulir UI con skill de diseño/animación, activar `PriceProvider`/`NewsProvider` live.

Total enfocado ~11-14h, dentro de las ~30h disponibles con buffer para imprevistos de despliegue y grabación del video.

## Verificación (end-to-end)

1. `pip install -r requirements.txt`; `uvicorn backend.main:app --reload` (arranca en modo LLM **mock**, sin key).
2. `cd frontend && npm install && npm run dev`; abrir la SPA.
3. Recorrer las páginas con datos mock:
   - **Radar:** filtrar por tipo/activo/antigüedad; confirmar fuente+fecha+instrumentos en cada noticia (HU1 ✔).
   - **AI Analysis / Señales:** ver clasificación positivo/negativo/neutral/incierto + confianza + evidencia/fuentes + comparación de precio + disclaimer (HU2 ✔).
   - **Briefings:** resumen por watchlist; marcar una señal como revisada/escalada/descartada con justificación (persiste tras recargar); crear una tarea/alerta; confirmar que **no existe** ninguna acción de compra/venta (HU3 ✔).
4. Cambiar `LLM_MODE=gemini` + `GOOGLE_API_KEY` → las mismas vistas ahora usan análisis reales de Gemini vía LangGraph.
5. Abrir el **link de despliegue** público y repetir el recorrido — debe verse igual que en local.
6. `pytest` corre verde; README/documento técnico completos; repo público; ZIP armado; video de 3 min listo.
