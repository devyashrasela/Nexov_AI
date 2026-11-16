"""FastAPI application for the dashboard and Pipecat signalling."""

from datetime import date
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import FRONTEND_ORIGIN, database_backend
from db import Base, engine, get_session
from store import get_doctors_with_slots, list_appointments

app = FastAPI(title="MediVoice API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from pipecat.transports.smallwebrtc.request_handler import (
    SmallWebRTCPatchRequest,
    SmallWebRTCRequest,
    SmallWebRTCRequestHandler,
)
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from bot import run_bot

webrtc_handler = SmallWebRTCRequestHandler()


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(engine)


@app.get("/api/health")
def health(session: Session = Depends(get_session)) -> dict:
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok", "db": database_backend()}


@app.get("/api/doctors")
def doctors(
    date_filter: str | None = Query(default=None, alias="date"),
    free_only: bool = False,
    session: Session = Depends(get_session),
) -> list[dict]:
    parsed_date = None
    if date_filter:
        try:
            parsed_date = date.fromisoformat(date_filter)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc
    return get_doctors_with_slots(session, parsed_date, free_only)


@app.get("/api/appointments")
def appointments(status: str | None = None, session: Session = Depends(get_session)) -> list[dict]:
    if status and status not in {"booked", "cancelled"}:
        raise HTTPException(status_code=400, detail="status must be booked or cancelled")
    return list_appointments(session, status)


@app.post("/api/offer")
async def offer(request: SmallWebRTCRequest, background_tasks: BackgroundTasks) -> dict:
    """Negotiate a browser offer and start a bot in the background."""
    async def on_connection(connection: SmallWebRTCConnection) -> None:
        background_tasks.add_task(run_bot, connection)

    answer = await webrtc_handler.handle_web_request(request, on_connection)
    if answer is None:
        raise HTTPException(status_code=500, detail="WebRTC negotiation did not return an answer")
    return answer


@app.patch("/api/offer")
async def offer_ice_candidate(request: SmallWebRTCPatchRequest) -> dict:
    await webrtc_handler.handle_patch_request(request)
    return {"status": "success"}
