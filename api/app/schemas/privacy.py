from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConsentState(BaseModel):
    personalization_enabled: bool
    updated_at: datetime | None = None


class ConsentUpdate(BaseModel):
    personalization_enabled: bool


class ExportedCheckin(BaseModel):
    date: date
    submitted_at: datetime
    form_version: str
    mood: float
    stress: float
    sleep_hours: float
    energy: float
    connectedness: float
    support_response: str
    note: str
    answers: dict[str, Any]


class ExportedConsent(BaseModel):
    personalization_enabled: bool
    created_at: datetime


class UserDataExport(BaseModel):
    exported_at: datetime
    username: str
    display_name: str
    created_at: datetime
    checkins: list[ExportedCheckin]
    consent_history: list[ExportedConsent]


class DeleteMyDataRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)
    confirmation: Literal["DELETE"]
