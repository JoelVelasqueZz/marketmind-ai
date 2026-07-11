# Documento Técnico — MarketMind AI (Track 5)

## 1. Track asignado

**Track 5 — Inteligencia de Mercado y Recomendaciones Informadas por Noticias.**

Problema que resuelve: convierte noticias y datos verificables de mercado en señales explicables sobre renta variable, instrumentos de crédito, criptoactivos y otros activos, para ayudar a priorizar el análisis **sin ejecutar operaciones ni prometer rendimientos**.

Agentes involucrados:
- **Analista de Coyuntura de Mercados IA** — clasifica el impacto de una noticia (positivo/negativo/neutral/incierto), lo compara contra el movimiento de precio real/mock del instrumento y explica la señal con evidencia y fuentes.
- **Asesor Financiero e Inversiones IA** — consume las señales del Analista y arma un briefing ejecutivo por watchlist con acciones de investigación sugeridas, para revisión y aprobación humana.

## 2. Tipo de negocio al que aplica

Diseñado para **mesas de análisis e investigación financiera** que necesitan triage rápido de noticias antes de que un humano decida: bancas de inversión, gestoras de patrimonio (wealth management) y RIAs, brokers/casas de bolsa con equipos de research, fintechs de inversión que ofrecen contenido informativo a sus usuarios, y equipos de riesgo/compliance que necesitan trazabilidad de por qué se generó una alerta.

El producto **no es** una plataforma de trading ni un asesor automatizado que ejecuta operaciones — es una herramienta de **priorización y explicabilidad** que reduce el tiempo que un analista humano tarda en decidir qué investigar primero, dejando la decisión final (y su justificación) siempre en manos de una persona.

## 3. Diagrama de arquitectura

```mermaid
flowchart TB
    subgraph Cliente["Canal: Web App (React SPA)"]
        UI1[News Radar — HU1]
        UI2[AI Analysis — HU2]
        UI3[Briefings — HU3]
    end

    subgraph Backend["Backend: FastAPI"]
        API[Routers REST /api/*]
        SVC[Services: radar / signals / briefing]
        DB[(SQLite / SQLModel\nSignal + review state, Task/Alert)]
    end

    subgraph Agentes["Orquestación de agentes: LangGraph (StateGraph)"]
        A1[Analista de Coyuntura\nde Mercados IA]
        A2[Asesor Financiero\ne Inversiones IA]
        A1 -->|señal explicable| A2
    end

    subgraph LLM["Capa LLM (provider-agnóstica)"]
        LLMC[LLMClient\nMODE=mock|gemini|claude]
        GEMINI[Gemini API\n(motor principal)]
        CLAUDE[Claude API\n(alterno)]
        LLMC --> GEMINI
        LLMC --> CLAUDE
    end

    subgraph Datos["Integraciones externas / datos"]
        NP[NewsProvider\nMock hoy → NewsAPI/RSS en vivo]
        PP[PriceProvider\nMock hoy → yfinance/CoinGecko en vivo]
    end

    UI1 -->|GET /api/news| API
    UI2 -->|POST /api/signals/generate| API
    UI3 -->|POST /api/briefing/generate\nPOST /api/signals/:id/review| API

    API --> SVC
    SVC --> A1
    SVC --> A2
    SVC --> DB
    A1 --> LLMC
    A2 --> LLMC
    SVC --> NP
    SVC --> PP
```

**Por qué LangGraph:** modela explícitamente el flujo `Analista → Asesor` como un grafo de estados con nodos puros y testeables por separado (ver `tests/test_analyst_node.py`, `test_advisor_node.py`, `test_agent.py`), en vez de encadenar llamadas sueltas al LLM. Esto es lo que el organizador del hackathon describe como "nivel intermedio" de arquitectura agéntica verificable.

**Por qué la capa `LLMClient` es provider-agnóstica:** permite construir y demostrar el flujo completo sin necesidad de una API key (`MODE=mock`, respuestas deterministas basadas en las mismas reglas de negocio), y activar Gemini real cambiando una sola variable de entorno (`LLM_MODE=gemini`). Claude queda disponible como alterno con el mismo contrato.

## 4. Mitigación de riesgos / antialucinación

- El Analista **solo** recibe como contexto la noticia y la comparación de precio reales/mock provistas — el prompt (`backend/agents/prompts.py`) prohíbe explícitamente inventar cifras, fuentes o eventos fuera de ese contexto.
- Toda señal incluye **evidencia citada**, **fuentes** y un **disclaimer** explícito de que no constituye asesoría personalizada ni garantiza resultados (criterio de aceptación de HU2).
- El campo `suggested_action` (Analista) y `research_action` (Asesor) están restringidos por diseño y por tests (`tests/test_analyst_node.py::test_signal_never_suggests_trade_execution`, `tests/test_advisor_node.py::test_advisor_never_suggests_trade_execution`) a ser siempre una acción de **investigación o revisión humana**, nunca una orden de compra/venta.
- Toda señal queda persistida con `review_status=pending` hasta que un humano la marque como `revisada`, `escalada` o `descartada`, guardando su justificación (HU3) — el sistema nunca actúa de forma autónoma sobre una señal.

## 5. Cómo se integraría a un sistema empresarial existente

El sistema está diseñado con puntos de extensión explícitos para no requerir reescritura al integrarse a infraestructura real:

- **Datos de mercado y noticias:** `NewsProvider` y `PriceProvider` (`backend/providers/`) son interfaces (`Protocol`) con una implementación Mock hoy. Reemplazarlas por fuentes reales (Bloomberg/Refinitiv/NewsAPI para noticias; un feed de mercado con licencia, yfinance o CoinGecko para precios) es una nueva clase que implementa el mismo contrato — routers y servicios no cambian.
- **Autenticación y control de acceso:** el backend FastAPI se integra de forma estándar detrás de un API Gateway con SSO/OAuth corporativo (Azure AD, Okta) para restringir por rol (analista junior vs. lead vs. compliance) quién puede generar señales, revisar o escalar.
- **Trazabilidad y auditoría (compliance):** cada `Signal` y `TaskAlert` queda persistida con timestamp, fuente, evidencia y justificación humana — ese mismo modelo (`backend/models.py`) puede escribirse a un data warehouse corporativo (o exportarse vía un endpoint adicional) para cumplir requisitos regulatorios locales de trazabilidad de recomendaciones.
- **Notificaciones y flujo de trabajo:** los `TaskAlert` que hoy se listan en la UI pueden publicarse como eventos (webhook) hacia herramientas ya usadas por el equipo — Slack/Teams para alertas en tiempo real, Jira/ServiceNow para asignar el research como ticket formal.
- **Despliegue:** el backend es un contenedor Docker autocontenido (`Dockerfile`) desplegable en cualquier plataforma corporativa (Kubernetes, ECS, Azure Container Apps) sin cambios; el frontend es un build estático (Vite) servible desde cualquier CDN interno.
- **Cambio de proveedor LLM:** si la empresa ya tiene un contrato con un proveedor de LLM distinto (Azure OpenAI, Vertex AI, Claude vía Bedrock), solo se agrega un nuevo modo en `LLMClient` (`backend/agents/llm.py`) — el resto del sistema (grafo, prompts, schemas de salida) no se toca.

## 6. Evidencia de pruebas

Ver `tests/` (pytest): tests de nodos del grafo con LLM mockeado (`test_analyst_node.py`, `test_advisor_node.py`), smoke test del pipeline completo (`test_agent.py`) y tests de los endpoints (`test_api.py`), incluyendo verificación explícita de que ninguna salida del sistema sugiere una orden de compra/venta. Correr con `pytest` desde la raíz del repo.
