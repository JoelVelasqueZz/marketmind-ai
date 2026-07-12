# Track 5 — Inteligencia de Mercado y Recomendaciones Informadas por Noticias

[![CI](https://github.com/JoelVelasqueZz/marketmind-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/JoelVelasqueZz/marketmind-ai/actions/workflows/ci.yml)

Sistema de dos agentes IA financieros (Hackathon Agentic Scale, TAWS/ESPOL):

- **Analista de Coyuntura de Mercados IA** — genera señales explicables de impacto a partir de noticias + precios.
- **Asesor Financiero e Inversiones IA** — arma briefings por watchlist con acciones de investigación sugeridas para revisión humana.

Los agentes nunca ejecutan ni sugieren órdenes de compra/venta: solo generan señales, briefings, alertas y tareas para que una persona decida.

**Demo en vivo:** https://marketmind-ai-three.vercel.app (frontend) · https://track5-backend.onrender.com/docs (backend, Swagger)

Plan completo, contexto del hackathon y decisiones de arquitectura: [`DOCS/PLAN.md`](DOCS/PLAN.md).

## Stack

- **Backend:** FastAPI + SQLModel (SQLite) + LangGraph (orquesta los dos agentes) + Gemini API (motor principal, con Claude como alterno) vía una capa `LLMClient` con `MODE=mock|gemini|claude`.
- **Frontend:** Vite + React + TypeScript + Tailwind, portado del mockup de diseño `MarketMind AI` (ver `DOCS/marketmind_dashboard_mockup/`).
- **Datos:** mock curado en `data/` (noticias, precios históricos, watchlists, fuentes), detrás de interfaces `NewsProvider`/`PriceProvider` que permiten enchufar datos en vivo después sin tocar el resto del código.

## Correr en local

### Backend

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; usa .venv\Scripts\activate en cmd/PowerShell
pip install -r requirements.txt
cp .env.example .env            # LLM_MODE=mock por defecto: no necesitas API key para probar
uvicorn backend.main:app --reload --port 8000
```

Docs interactivas: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # VITE_API_URL=http://localhost:8000
npm run dev
```

Abrir http://localhost:5173

### Activar Gemini real (opcional)

En `.env` del backend: `LLM_MODE=gemini`, `GOOGLE_API_KEY=<tu key>`. Las mismas rutas (`/api/signals/generate`, `/api/briefing/generate`) pasan de usar el modo mock determinista a usar Gemini de verdad, sin cambiar código.

## Estructura

Ver el árbol completo y el contrato de endpoints en [`DOCS/PLAN.md`](DOCS/PLAN.md).

## Tests

```bash
pytest
```

## Despliegue

Ver checklist en `DOCS/PLAN.md` → sección Despliegue (Render para el backend vía `Dockerfile`, Vercel/Netlify para el frontend).

## Alcance mínimo cubierto (criterios de aceptación del track)

- **HU1 — Radar:** `GET /api/news` con filtros por tipo/activo/antigüedad, fuente y fecha visibles → página **News Radar**.
- **HU2 — Señal explicable:** `POST /api/signals/generate` (Analista) → página **AI Analysis**.
- **HU3 — Briefing con revisión humana:** `POST /api/briefing/generate` (Asesor) + `POST /api/signals/{id}/review` → página **Briefings**. Nunca crea órdenes de compra/venta, solo tareas/alertas.
