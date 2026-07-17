import json
import queue
import threading
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from backend.db import engine, get_session
from backend.schemas import ReviewEventOut, ReviewRequest, SignalGenerateRequest, SignalOut
from backend.services import attribution as attribution_service
from backend.services import signals as signals_service

router = APIRouter(prefix="/api/signals", tags=["signals"])

_STREAM_DONE = object()


@router.get("", response_model=list[SignalOut])
def list_signals(asset: Optional[str] = None, session: Session = Depends(get_session)):
    return signals_service.list_signals(asset, session)


@router.post("/generate", response_model=SignalOut)
def generate_signal(payload: SignalGenerateRequest, session: Session = Depends(get_session)):
    try:
        return signals_service.generate_signal(
            payload.news_id,
            payload.instrument,
            session,
            force=payload.force,
            demo_contaminate=payload.demo_contaminate,
        )
    except signals_service.NewsNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/generate/stream")
def generate_signal_stream(
    news_id: str, instrument: str, force: bool = True, demo_contaminate: bool = False
):
    """Sala de Maquinas: genera la senal y transmite cada evento del pipeline
    en vivo (SSE). El replay de la traza persistida es el camino por defecto de
    la demo; esto es la version server-push, con heartbeat y sesion propia."""
    events: "queue.Queue" = queue.Queue()

    def worker():
        # Sesion propia: la del request (Depends) no es thread-safe ni sobrevive.
        try:
            with Session(engine) as session:
                out = signals_service.generate_signal(
                    news_id,
                    instrument,
                    session,
                    force=force,
                    demo_contaminate=demo_contaminate,
                    on_event=lambda evt: events.put(evt),
                )
            events.put({"type": "done", "signal_id": out.id})
        except signals_service.NewsNotFound as exc:
            events.put({"type": "error", "detail": str(exc)})
        except Exception as exc:  # noqa: BLE001 - el error viaja al cliente y termina el stream
            events.put({"type": "error", "detail": f"Fallo generando la senal: {exc}"})
        finally:
            events.put(_STREAM_DONE)

    threading.Thread(target=worker, daemon=True).start()

    def event_stream():
        while True:
            try:
                item = events.get(timeout=1.0)
            except queue.Empty:
                yield ": keep-alive\n\n"  # comentario SSE: mantiene viva la conexion
                continue
            if item is _STREAM_DONE:
                break
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/review-causes")
def review_causes(session: Session = Depends(get_session)):
    """Tablero NTSB: distribucion de causas raiz de descartes/escaladas."""
    return signals_service.review_cause_counts(session)


@router.post("/{signal_id}/review", response_model=SignalOut)
def review_signal(signal_id: str, payload: ReviewRequest, session: Session = Depends(get_session)):
    try:
        result = signals_service.review_signal(
            signal_id,
            payload.status,
            payload.justification,
            session,
            cause=payload.cause,
            reviewer=payload.reviewer,
            role=payload.role,
        )
    except signals_service.NotAuthorized as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Senal no encontrada")
    return result


@router.get("/{signal_id}/events", response_model=list[ReviewEventOut])
def signal_events(signal_id: str, session: Session = Depends(get_session)):
    """Expediente 360: cadena de custodia append-only de la senal."""
    if signals_service.get_signal(signal_id, session) is None:
        raise HTTPException(status_code=404, detail="Senal no encontrada")
    return signals_service.list_review_events(signal_id, session)


@router.get("/{signal_id}/trace")
def get_signal_trace(signal_id: str, session: Session = Depends(get_session)):
    """Caja de Cristal: la traza de ejecucion escrita por el orquestador."""
    signal = signals_service.get_signal(signal_id, session)
    if signal is None:
        raise HTTPException(status_code=404, detail="Senal no encontrada")
    if not signal.execution_trace:
        raise HTTPException(
            status_code=404,
            detail="Senal anterior a la trazabilidad: no tiene traza de ejecucion registrada.",
        )
    return signal.execution_trace


@router.post("/{signal_id}/attribution")
def compute_signal_attribution(
    signal_id: str, force: bool = False, session: Session = Depends(get_session)
):
    """Sondeo contrafactual '¿Que peso mas?': 2 re-ejecuciones controladas."""
    signal = signals_service.get_signal(signal_id, session)
    if signal is None:
        raise HTTPException(status_code=404, detail="Senal no encontrada")
    try:
        return attribution_service.compute_attribution(signal, session, force=force)
    except signals_service.NewsNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
