from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Impact = Literal["positive", "negative", "neutral", "uncertain"]
ReviewStatus = Literal["pending", "revisada", "escalada", "descartada"]

# Taxonomia NTSB: causa raiz cerrada del descarte/escalada (ademas de la
# justificacion libre). Legible por maquina -> viaja al few-shot del Comite.
ReviewCause = Literal[
    "evidencia_insuficiente",
    "sobre_reaccion_al_precio",
    "dato_no_soportado_por_fuente",
    "contexto_faltante",
    "criterio_del_comite",
]

# Expediente 360: rol declarado del revisor (no autenticacion criptografica).
ReviewerRole = Literal["analista", "lead", "compliance"]


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
    evidence: list[str] = Field(min_length=2)
    reasoning: str
    suggested_action: str


class ReviewExample(BaseModel):
    """Revision humana pasada, reutilizada como ejemplo few-shot para el Analista."""

    instrument: str
    impact: Impact
    confidence: float
    evidence: list[str]
    review_status: ReviewStatus
    review_justification: str
    cause: Optional[ReviewCause] = None


class TriageOut(BaseModel):
    """Nivel de triaje derivado (Manchester/CVSS) con su regla literal."""

    level: Literal["rojo", "naranja", "amarillo", "verde", "azul"]
    priority: int
    sla: str
    rule: str


class FreshnessOut(BaseModel):
    """Vigencia derivada: la senal declara su propia caducidad."""

    pct: float
    age_days: float
    half_life_days: float
    stale: bool
    rule: str


class GateCheck(BaseModel):
    """Un check determinista del Compliance Gate con su regla literal."""

    item: str
    passed: bool
    detail: str
    rule: str = ""


class ComplianceOut(BaseModel):
    """Veredicto del Compliance Gate 360 (checklist de despacho)."""

    verdict: Literal["ok", "corregida", "marcada"]
    passed: int
    total: int
    checks: list[GateCheck] = Field(default_factory=list)


class ReviewEventOut(BaseModel):
    """Una fila de la cadena de custodia append-only (Expediente 360)."""

    from_status: str
    to_status: str
    reviewer: str
    role: str
    cause: Optional[str] = None
    justification: str = ""
    at: datetime


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
    review_cause: Optional[ReviewCause] = None
    reviewed_by: Optional[str] = None
    review_examples_used: list[ReviewExample] = Field(default_factory=list)
    # Caja de Cristal: la UI decide mostrar "Ver ejecucion" sin llamada extra.
    has_trace: bool = False
    has_attribution: bool = False
    # Compliance Gate 360: checklist de despacho.
    compliance: Optional[ComplianceOut] = None
    # Derivados al servir (sin migracion): triaje con SLA y vigencia.
    triage: Optional[TriageOut] = None
    freshness: Optional[FreshnessOut] = None


class SignalGenerateRequest(BaseModel):
    news_id: str
    instrument: str
    force: bool = False
    # SOLO demo (mock): fuerza una salida alucinada para mostrar el gate.
    demo_contaminate: bool = False


class ReviewRequest(BaseModel):
    status: Literal["revisada", "escalada", "descartada"]
    # HU3 exige guardar la justificacion del analista: no se acepta vacia.
    justification: str = Field(min_length=3)
    # NTSB: causa raiz opcional de la taxonomia cerrada.
    cause: Optional[ReviewCause] = None
    # Expediente 360: identidad y rol declarados del revisor.
    reviewer: str = "Analista"
    role: ReviewerRole = "analista"


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
