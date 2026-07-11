from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.db import get_session
from backend.schemas import BriefingOut
from backend.services import briefing as briefing_service

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/watchlists")
def get_watchlists():
    return briefing_service.list_watchlists()


@router.get("", response_model=BriefingOut)
@router.post("/generate", response_model=BriefingOut)
def get_or_generate_briefing(watchlist: str, session: Session = Depends(get_session)):
    try:
        return briefing_service.generate_briefing(watchlist, session)
    except briefing_service.WatchlistNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
