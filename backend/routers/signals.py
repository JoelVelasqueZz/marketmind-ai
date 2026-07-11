from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.db import get_session
from backend.schemas import ReviewRequest, SignalGenerateRequest, SignalOut
from backend.services import signals as signals_service

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("", response_model=list[SignalOut])
def list_signals(asset: Optional[str] = None, session: Session = Depends(get_session)):
    return signals_service.list_signals(asset, session)


@router.post("/generate", response_model=SignalOut)
def generate_signal(payload: SignalGenerateRequest, session: Session = Depends(get_session)):
    try:
        return signals_service.generate_signal(
            payload.news_id, payload.instrument, session, force=payload.force
        )
    except signals_service.NewsNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{signal_id}/review", response_model=SignalOut)
def review_signal(signal_id: str, payload: ReviewRequest, session: Session = Depends(get_session)):
    result = signals_service.review_signal(signal_id, payload.status, payload.justification, session)
    if result is None:
        raise HTTPException(status_code=404, detail="Senal no encontrada")
    return result
