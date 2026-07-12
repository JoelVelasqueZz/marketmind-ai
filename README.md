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

### Activar un LLM real (opcional)

Cambiar de proveedor es una sola variable de entorno (`LLM_MODE`) en `.env` del backend — las mismas rutas (`/api/signals/generate`, `/api/briefing/generate`) pasan de usar el modo mock determinista a usar el proveedor real, sin tocar código:

- **Gemini** (motor principal): `LLM_MODE=gemini`, `GOOGLE_API_KEY=<tu key>`.
- **Claude** (alterno): `LLM_MODE=claude`, `ANTHROPIC_API_KEY=<tu key>`.
- **DeepSeek** (alterno gratuito, si se agota la cuota de Gemini): `LLM_MODE=deepseek`, `DEEPSEEK_API_KEY=<tu key>`. Sirve tanto con la [API oficial de DeepSeek](https://platform.deepseek.com/sign_in) (5M tokens gratis de prueba, deja `DEEPSEEK_BASE_URL` como está) como con [OpenRouter](https://openrouter.ai/) (`DEEPSEEK_BASE_URL=https://openrouter.ai/api/v1` + tu key de OpenRouter + `LLM_MODEL=deepseek/deepseek-chat-v3.1:free` o el modelo gratis que esté disponible).

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
