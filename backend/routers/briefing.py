from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from backend.db import get_session
from backend.schemas import BriefingOut, WatchlistOverviewOut
from backend.services import briefing as briefing_service

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/watchlists")
def get_watchlists():
    return briefing_service.list_watchlists()


@router.get("/watchlists/{watchlist_id}/overview", response_model=WatchlistOverviewOut)
def get_watchlist_overview(watchlist_id: str, session: Session = Depends(get_session)):
    try:
        return briefing_service.get_watchlist_overview(watchlist_id, session)
    except briefing_service.WatchlistNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=BriefingOut)
@router.post("/generate", response_model=BriefingOut)
def get_or_generate_briefing(
    watchlist: str, force: bool = False, session: Session = Depends(get_session)
):
    try:
        return briefing_service.generate_briefing(watchlist, session, force=force)
    except briefing_service.WatchlistNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
