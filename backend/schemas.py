from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Impact = Literal["positive", "negative", "neutral", "uncertain"]
ReviewStatus = Literal["pending", "revisada", "escalada", "descartada"]


class InstrumentOut(BaseModel):
    symbol: str
    name: str
    type: Literal["equity", "credit", "crypto", "other"]
    sector: str


class NewsOut(BaseModel):
    id: str
    headline: str
    summary: str
    source: str
    published_at: datetime
    instruments: list[str]
    sector: str
    topic: str
    age_days: float


class PricePoint(BaseModel):
    date: str
    close: float


class PriceComparison(BaseModel):
    instrument: str
    change_pct: float
    window_days: int
    note: str


# --- Salida estructurada que produce el LLM (Analista) ---
class AnalystLLMOutput(BaseModel):
    """Salida forzada del Analista de Coyuntura de Mercados IA (nodo LangGraph)."""

    impact: Impact
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    reasoning: str
    suggested_action: str


class SignalOut(BaseModel):
    id: str
    news_id: str
    instrument: str
    impact: Impact
    confidence: float
    evidence: list[str]
    sources: list[str]
    price_comparison: PriceComparison
    disclaimer: str
    suggested_action: Optional[str] = None
    created_at: datetime
    review_status: ReviewStatus
    review_justification: Optional[str] = None


class SignalGenerateRequest(BaseModel):
    news_id: str
    instrument: str
    force: bool = False


class ReviewRequest(BaseModel):
    status: Literal["revisada", "escalada", "descartada"]
    justification: str


# --- Salida estructurada que produce el LLM (Asesor) ---
class AdvisorLLMOutput(BaseModel):
    """Salida forzada del Asesor Financiero e Inversiones IA (nodo LangGraph)."""

    research_action: str
    executive_summary: list[str]


class BriefingItemOut(BaseModel):
    instrument: str
    signal: SignalOut
    news_headline: str
    price_change_pct: float
    research_action: str
    executive_summary: list[str]


class BriefingOut(BaseModel):
    watchlist_id: str
    watchlist_name: str
    generated_at: datetime
    items: list[BriefingItemOut]
    disclaimer: str


class AssetSignalSummary(BaseModel):
    impact: Impact
    confidence: float
    created_at: datetime


class AssetOverview(BaseModel):
    symbol: str
    name: str
    type: Literal["equity", "credit", "crypto", "other"]
    price: Optional[float] = None
    change_pct_1d: Optional[float] = None
    signal: Optional[AssetSignalSummary] = None


class WatchlistOverviewOut(BaseModel):
    watchlist_id: str
    watchlist_name: str
    assets: list[AssetOverview]


class TaskOut(BaseModel):
    id: str
    signal_id: Optional[str] = None
    instrument: str
    title: str
    description: str
    status: Literal["open", "done"]
    created_at: datetime


class TaskCreateRequest(BaseModel):
    signal_id: Optional[str] = None
    instrument: str
    title: str
    description: str
