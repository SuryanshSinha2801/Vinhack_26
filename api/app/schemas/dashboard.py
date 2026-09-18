from datetime import date

from pydantic import BaseModel


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


class UserDashboard(BaseModel):
    username: str
    display_name: str
    summary: DashboardSummary
    history: list[DailyWellbeingRecord]
