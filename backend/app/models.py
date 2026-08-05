from typing import Any, Literal

from pydantic import BaseModel, Field


class EntryRequest(BaseModel):
    resident_id: str
    locale: str | None = None
    speech_register: Literal["standard", "local-light"] = "standard"
    room_id: str | None = "screening-01"


class MessageRequest(BaseModel):
    text: str = Field(min_length=1)


class SessionSummary(BaseModel):
    id: str
    resident_id: str
    preferred_name: str | None
    locale: str
    speech_register: str
    room_id: str | None
    status: str
    created_at: str
    ended_at: str | None
    turn_count: int
    has_report: bool
    validation_error_count: int


class SessionDetail(BaseModel):
    id: str
    resident_id: str
    preferred_name: str | None
    locale: str
    speech_register: str
    room_id: str | None
    status: str
    transcript: list[dict[str, Any]]
    report: dict[str, Any] | None
    validation_errors: list[str]
    created_at: str
    ended_at: str | None


class ResidentOut(BaseModel):
    resident_id: str
    preferred_name: str | None
    locale: str
    notes: str
