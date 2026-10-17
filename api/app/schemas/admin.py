from datetime import date, datetime

from pydantic import BaseModel


class AdminDailyAggregate(BaseModel):
    date: date
    participants: int
    average_mood: float | None = None
    average_stress: float | None = None
    follow_up_requests: int | None = None
    suppressed: bool


class AdminDashboard(BaseModel):
    generated_at: datetime
    window_days: int
    privacy_minimum_group: int
    active_students: int
    completed_today: int
    completion_rate_today: float
    checkins_in_window: int
    daily: list[AdminDailyAggregate]
    privacy_notice: str
