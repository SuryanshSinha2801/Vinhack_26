from __future__ import annotations

import hashlib
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.app.core.clock import local_today
from api.app.models import DailyCheckin, User
from api.app.schemas.checkins import CheckinPersonalization


STRATEGY_VERSION = "adaptive-checkin-v1"
FOCUS_LABELS = {
    "sleep": "sleep and recovery",
    "academic": "study pressure",
    "connection": "social connection",
    "support": "support preferences",
}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = (len(values) - 1) / 2
    denominator = sum((index - center) ** 2 for index in range(len(values)))
    return sum((index - center) * (value - _mean(values)) for index, value in enumerate(values)) / denominator


def rank_focus_areas(records: list[dict[str, float]], username: str, today: date) -> list[str]:
    """Rank non-clinical follow-up topics from recent wellbeing patterns."""
    if not records:
        rotation = ["sleep", "academic", "connection", "support"]
        digest = hashlib.sha256(f"{username}:{today.isoformat()}".encode()).digest()[0]
        start = digest % len(rotation)
        return [rotation[start], rotation[(start + 1) % len(rotation)]]

    recent = records[-14:]
    mood = [row["mood"] for row in recent]
    stress = [row["stress"] for row in recent]
    sleep = [row["sleep_hours"] for row in recent]
    energy = [row["energy"] for row in recent]
    connection = [row["connectedness"] for row in recent]
    scores = {
        "sleep": max(0.0, 7.0 - _mean(sleep)) + max(0.0, -_slope(sleep)) * 2,
        "academic": max(0.0, _mean(stress) - 2.5) + max(0.0, _slope(stress)) * 2,
        "connection": max(0.0, 3.5 - _mean(connection)) + max(0.0, -_slope(connection)),
        "support": max(0.0, 3.2 - _mean(mood)) + max(0.0, 3.2 - _mean(energy)),
    }
    tie_break = {name: index for index, name in enumerate(["sleep", "academic", "connection", "support"])}
    return sorted(scores, key=lambda name: (-scores[name], tie_break[name]))[:2]


def get_personalization(user: User, db: Session) -> CheckinPersonalization:
    history = db.scalars(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user.id)
        .order_by(DailyCheckin.checkin_date)
    ).all()
    records = [
        {
            "date": row.checkin_date,
            "mood": row.mood,
            "stress": row.stress,
            "sleep_hours": row.sleep_hours,
            "energy": row.energy,
            "connectedness": row.connectedness,
        }
        for row in history
    ]
    consent: str | None = None
    for row in reversed(history):
        if row.answers and "trend_suggestions_consent" in row.answers:
            consent = str(row.answers["trend_suggestions_consent"])
            break

    allowed = consent != "No"
    focus_areas = rank_focus_areas(records if allowed else [], user.username, local_today())
    labels = [FOCUS_LABELS[area] for area in focus_areas]
    if records and allowed:
        explanation = f"Today includes {labels[0]} and {labels[1]} based on your recent check-in patterns."
    elif consent == "No":
        explanation = f"Today includes a rotating mix of {labels[0]} and {labels[1]}; recent trends were not used."
    else:
        explanation = f"Today starts with {labels[0]} and {labels[1]}; future forms can adapt as your history grows."
    return CheckinPersonalization(
        strategy_version=STRATEGY_VERSION,
        personalized=bool(records and allowed),
        focus_areas=focus_areas,
        based_on_days=min(len(records), 14) if allowed else 0,
        explanation=explanation,
    )
