from datetime import date

from pydantic import BaseModel, ConfigDict


class DailyWellbeingRecord(BaseModel):
    date: date
    mood: float
    stress: float
    sleep_hours: float
    energy: float
    connectedness: float
    checkin_completed: bool
    support_response: str
    note: str


class DashboardSummary(BaseModel):
    days: int
    average_mood: float
    average_stress: float
    average_sleep_hours: float
    latest_mood: float
    latest_stress: float


class WellbeingInsight(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    level: str
    score: int
    confidence: float
    summary: str
    factors: list[str]
    suggestions: list[str]
    model_version: str
    disclaimer: str


class UserDashboard(BaseModel):
    username: str
    display_name: str
    summary: DashboardSummary
    history: list[DailyWellbeingRecord]
    insight: WellbeingInsight | None = None
