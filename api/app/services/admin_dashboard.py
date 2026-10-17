from collections import defaultdict
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.app.core.clock import local_now, local_today
from api.app.models import DailyCheckin, User
from api.app.schemas.admin import AdminDailyAggregate, AdminDashboard


PRIVACY_MINIMUM_GROUP = 5


def _requested_follow_up(answers: dict | None) -> bool:
    value = str((answers or {}).get("follow_up_requested", "")).strip().lower()
    return value.startswith("yes")


def get_admin_dashboard(db: Session, window_days: int) -> AdminDashboard:
    today = local_today()
    cutoff = today - timedelta(days=window_days - 1)
    active_students = db.scalar(
        select(func.count(User.id)).where(User.is_active.is_(True), User.role == "student")
    ) or 0
    rows = db.scalars(
        select(DailyCheckin)
        .where(DailyCheckin.checkin_date >= cutoff, DailyCheckin.checkin_date <= today)
        .order_by(DailyCheckin.checkin_date)
    ).all()
    completed_today = len({row.user_id for row in rows if row.checkin_date == today})
    grouped: dict = defaultdict(list)
    for row in rows:
        grouped[row.checkin_date].append(row)

    daily: list[AdminDailyAggregate] = []
    for day in sorted(grouped):
        day_rows = grouped[day]
        participants = len({row.user_id for row in day_rows})
        suppressed = participants < PRIVACY_MINIMUM_GROUP
        daily.append(
            AdminDailyAggregate(
                date=day,
                participants=participants,
                average_mood=None if suppressed else round(sum(row.mood for row in day_rows) / len(day_rows), 1),
                average_stress=None if suppressed else round(sum(row.stress for row in day_rows) / len(day_rows), 1),
                follow_up_requests=None if suppressed else sum(_requested_follow_up(row.answers) for row in day_rows),
                suppressed=suppressed,
            )
        )

    return AdminDashboard(
        generated_at=local_now(),
        window_days=window_days,
        privacy_minimum_group=PRIVACY_MINIMUM_GROUP,
        active_students=active_students,
        completed_today=completed_today,
        completion_rate_today=round(completed_today / active_students * 100, 1) if active_students else 0,
        checkins_in_window=len(rows),
        daily=daily,
        privacy_notice=(
            f"Daily wellbeing averages and follow-up counts are hidden when fewer than "
            f"{PRIVACY_MINIMUM_GROUP} students participated. Individual answers and identities are never returned."
        ),
    )
