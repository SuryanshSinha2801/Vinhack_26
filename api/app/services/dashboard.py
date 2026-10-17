from sqlalchemy import select
from sqlalchemy.orm import Session

from api.app.models import DailyCheckin, User
from api.app.schemas.dashboard import DailyWellbeingRecord, DashboardSummary, UserDashboard
from api.app.services.wellbeing_model import predict_wellbeing


def get_user_dashboard(user: User, db: Session) -> UserDashboard | None:
    rows = db.scalars(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user.id)
        .order_by(DailyCheckin.checkin_date)
    ).all()
    history = [
        DailyWellbeingRecord(
            date=row.checkin_date,
            mood=row.mood,
            stress=row.stress,
            sleep_hours=row.sleep_hours,
            energy=row.energy,
            connectedness=row.connectedness,
            checkin_completed=row.checkin_completed,
            support_response=row.support_response,
            note=row.note,
        )
        for row in rows
    ]
    if not history:
        return None
    latest = history[-1]
    count = len(history)
    summary = DashboardSummary(
        days=count,
        average_mood=round(sum(item.mood for item in history) / count, 1),
        average_stress=round(sum(item.stress for item in history) / count, 1),
        average_sleep_hours=round(sum(item.sleep_hours for item in history) / count, 1),
        latest_mood=latest.mood,
        latest_stress=latest.stress,
    )
    return UserDashboard(
        username=user.username,
        display_name=user.display_name,
        summary=summary,
        history=history,
        insight=predict_wellbeing(history),
    )
