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
    reviewed_at: Optional[datetime] = None


class TaskAlert(SQLModel, table=True):
    """Tarea/alerta de investigacion creada para revision humana (HU3).

    Nunca representa una orden de compra/venta.
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    signal_id: Optional[str] = Field(default=None, index=True)
    instrument: str
    title: str
    description: str
    status: str = Field(default="open")  # open | done
    created_at: datetime = Field(default_factory=_now)
