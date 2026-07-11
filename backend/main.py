from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS
from backend.db import init_db
from backend.routers import briefing, instruments, news, signals, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Track 5 - Inteligencia de Mercado y Recomendaciones Informadas por Noticias",
    description=(
        "API de los dos agentes IA (Analista de Coyuntura de Mercados y Asesor Financiero e "
        "Inversiones) que generan senales explicables y briefings para revision humana. "
        "No ejecuta ordenes de compra/venta."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(instruments.router)
app.include_router(news.router)
app.include_router(signals.router)
app.include_router(briefing.router)
app.include_router(tasks.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
