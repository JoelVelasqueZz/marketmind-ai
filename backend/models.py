import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Signal(SQLModel, table=True):
    """Señal explicable de impacto generada por el Analista de Coyuntura (HU2).

    review_status guarda el estado de revisión humana definido en HU3
    (pending -> revisada | escalada | descartada), nunca una orden de compra/venta.
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    news_id: str = Field(index=True)
    instrument: str = Field(index=True)
    impact: str  # positive | negative | neutral | uncertain
    confidence: float  # 0.0 - 1.0
    evidence: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    sources: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    price_comparison: dict = Field(default_factory=dict, sa_column=Column(JSON))
    disclaimer: str
    suggested_action: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)

    review_status: str = Field(default="pending")  # pending | revisada | escalada | descartada
    review_justification: Optional[str] = None
    # NTSB: causa raiz taxonomizada del descarte/escalada (schemas.ReviewCause).
    review_cause: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    # Expediente 360: ultimo revisor (identidad declarada, no auth cripto).
    reviewed_by: Optional[str] = None

    # Caja de Cristal: traza de ejecucion escrita por el orquestador (contrato
    # v1 en backend/agents/trace.py) y sondeo contrafactual cacheado. Nullable:
    # senales anteriores a estas columnas no los tienen (la UI degrada).
    execution_trace: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    attribution: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    # Compliance Gate 360: veredicto y checks deterministas de despacho.
    compliance: Optional[dict] = Field(default=None, sa_column=Column(JSON))


class ReviewEvent(SQLModel, table=True):
    """Cadena de custodia append-only de las revisiones humanas (Expediente 360).

    Cada transicion de estado escribe una fila nueva (nunca se actualiza): quien
    decidio que, con que rol, cuando y por que. Es el sustrato de una pista de
    auditoria para un regulador (SCVS / Superintendencia de Bancos).
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    signal_id: str = Field(index=True)
    from_status: str
    to_status: str
    reviewer: str
    role: str  # analista | lead | compliance
    cause: Optional[str] = None
    justification: str = ""
    at: datetime = Field(default_factory=_now)


class TaskAlert(SQLModel, table=True):
    """Tarea/alerta de investigacion creada para revision humana (HU3).

    Nunca representa una orden de compra/venta.
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    signal_id: Optional[str] = Field(default=None, index=True)
    instrument: str
    title: str
    description: str
    # Resumen del Asesor persistido para que regenerar el briefing devuelva el
    # mismo contenido (nullable: tareas previas a esta columna no lo tienen).
    executive_summary: Optional[list] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default="open")  # open | done
    created_at: datetime = Field(default_factory=_now)
