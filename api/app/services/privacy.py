from sqlalchemy import select
from sqlalchemy.orm import Session

from api.app.core.clock import utc_now
from api.app.models import ConsentRecord, DailyCheckin, User
from api.app.schemas.privacy import (
    ConsentState,
    ExportedCheckin,
    ExportedConsent,
    UserDataExport,
)


def get_consent_state(user_id: int, db: Session) -> ConsentState:
    latest = db.scalar(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user_id)
        .order_by(ConsentRecord.created_at.desc(), ConsentRecord.id.desc())
        .limit(1)
    )
    return ConsentState(
        personalization_enabled=latest.personalization_enabled if latest else True,
        updated_at=latest.created_at if latest else None,
    )


def record_consent(user_id: int, enabled: bool, db: Session) -> ConsentState:
    record = ConsentRecord(user_id=user_id, personalization_enabled=enabled)
    db.add(record)
    db.commit()
    db.refresh(record)
    return ConsentState(
        personalization_enabled=record.personalization_enabled,
        updated_at=record.created_at,
    )


def export_user_data(user: User, db: Session) -> UserDataExport:
    checkins = db.scalars(
        select(DailyCheckin)
        .where(DailyCheckin.user_id == user.id)
        .order_by(DailyCheckin.checkin_date, DailyCheckin.id)
    ).all()
    consents = db.scalars(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user.id)
        .order_by(ConsentRecord.created_at, ConsentRecord.id)
    ).all()
    return UserDataExport(
        exported_at=utc_now(),
        username=user.username,
        display_name=user.display_name,
        created_at=user.created_at,
        checkins=[
            ExportedCheckin(
                date=row.checkin_date,
                submitted_at=row.submitted_at,
                form_version=row.form_version,
                mood=row.mood,
                stress=row.stress,
                sleep_hours=row.sleep_hours,
                energy=row.energy,
                connectedness=row.connectedness,
                support_response=row.support_response,
                note=row.note,
                answers=row.answers or {},
            )
            for row in checkins
        ],
        consent_history=[
            ExportedConsent(
                personalization_enabled=row.personalization_enabled,
                created_at=row.created_at,
            )
            for row in consents
        ],
    )
