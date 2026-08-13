from fastapi import APIRouter, HTTPException, Request

from ..analyst import run_analyst
from ..companion import generate_companion_reply
from ..db import append_turn, create_session, end_session, get_session, list_sessions, save_report
from ..llm_capture import capture_enabled_for_request, llm_capture_scope
from ..models import EntryRequest, MessageRequest, ResidentOut, SessionDetail, SessionSummary
from ..observability import log_session_event, timed_span
from ..residents import RESIDENTS, get_resident
from ..skills import load_greeting

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _to_summary(session: dict) -> SessionSummary:
    return SessionSummary(
        id=session["id"],
        resident_id=session["resident_id"],
        preferred_name=session["preferred_name"],
        locale=session["locale"],
        room_id=session["room_id"],
        status=session["status"],
        created_at=session["created_at"],
        ended_at=session["ended_at"],
        turn_count=len(session["transcript"]),
        has_report=session["report"] is not None,
        validation_error_count=len(session["validation_errors"]),
    )


def _to_detail(session: dict) -> SessionDetail:
    return SessionDetail(**session)


@router.get("", response_model=list[SessionSummary])
def sessions_list():
    return [_to_summary(s) for s in list_sessions()]


@router.post("/entry", response_model=SessionDetail)
def session_entry(body: EntryRequest):
    profile = get_resident(body.resident_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Unknown resident_id")

    locale = body.locale or profile.locale
    preferred_name = profile.preferred_name
    greeting = load_greeting(locale, preferred_name)
    session = create_session(
        resident_id=body.resident_id,
        preferred_name=preferred_name,
        locale=locale,
        room_id=body.room_id,
        opening_message=greeting,
    )
    log_session_event(
        "session_entry",
        session_id=session["id"],
        resident_id=body.resident_id,
        locale=locale,
        turn_count=len(session["transcript"]),
    )
    return _to_detail(session)


@router.get("/{session_id}", response_model=SessionDetail)
def session_get(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_detail(session)


@router.post("/{session_id}/message", response_model=SessionDetail)
async def session_message(session_id: str, body: MessageRequest, request: Request):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "active":
        raise HTTPException(status_code=400, detail="Session has ended")

    resident_text = body.text.strip()
    append_turn(session_id, "resident", resident_text)
    session = get_session(session_id)
    assert session

    with llm_capture_scope(session_id, enabled=capture_enabled_for_request(request)):
        with timed_span("companion_reply", session_id=session_id, locale=session["locale"]) as span:
            reply, warnings = await generate_companion_reply(
                preferred_name=session["preferred_name"],
                locale=session["locale"],
                transcript=session["transcript"],
            )
            span["companion_warning_count"] = len(warnings)
    append_turn(session_id, "companion", reply)
    session = get_session(session_id)
    log_session_event(
        "session_message",
        session_id=session_id,
        locale=session["locale"],
        turn_count=len(session["transcript"]),
        companion_warning_count=len(warnings),
        companion_ms=span.get("duration_ms"),
    )
    return _to_detail(session)


@router.post("/{session_id}/exit", response_model=SessionDetail)
async def session_exit(session_id: str, request: Request):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] == "ended":
        return _to_detail(session)

    name = session["preferred_name"] or "there"
    closing = f"Thank you for chatting with me today. Take care, {name}."
    with llm_capture_scope(session_id, enabled=capture_enabled_for_request(request)):
        with timed_span("analyst_run", session_id=session_id, locale=session["locale"]) as span:
            report, errors = await run_analyst(session["transcript"], locale=session["locale"])
    ended = end_session(session_id, closing_message=closing, report=report, validation_errors=errors)
    log_session_event(
        "session_exit",
        session_id=session_id,
        locale=session["locale"],
        turn_count=len(ended["transcript"]),
        analyst_ms=span.get("duration_ms"),
        validation_error_count=len(errors),
        recommendation=(report or {}).get("recommendation"),
        suicide_risk_flag=(report or {}).get("suicide_risk_flag"),
        passive_suicidal_thoughts=(report or {}).get("passive_suicidal_thoughts"),
        active_suicidal_ideation=(report or {}).get("active_suicidal_ideation"),
    )
    return _to_detail(ended)


@router.post("/{session_id}/analyze", response_model=SessionDetail)
async def session_analyze(session_id: str, request: Request):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    with llm_capture_scope(session_id, enabled=capture_enabled_for_request(request)):
        with timed_span("analyst_run", session_id=session_id, locale=session["locale"]) as span:
            report, errors = await run_analyst(session["transcript"], locale=session["locale"])
    save_report(session_id, report, errors)
    session = get_session(session_id)
    log_session_event(
        "session_analyze",
        session_id=session_id,
        locale=session["locale"],
        turn_count=len(session["transcript"]),
        analyst_ms=span.get("duration_ms"),
        validation_error_count=len(errors),
        recommendation=(report or {}).get("recommendation"),
    )
    return _to_detail(session)


residents_router = APIRouter(prefix="/api/residents", tags=["residents"])


@residents_router.get("", response_model=list[ResidentOut])
def residents_list():
    return [
        ResidentOut(
            resident_id=r.resident_id,
            preferred_name=r.preferred_name,
            locale=r.locale,
            notes=r.notes,
        )
        for r in RESIDENTS.values()
    ]
