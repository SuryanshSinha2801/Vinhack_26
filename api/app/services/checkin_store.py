from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.app.core.clock import local_today, utc_now
from api.app.models import DailyCheckin, User
from api.app.schemas.checkins import CheckinSubmission, CheckinSubmissionResult
from api.app.services.checkin_catalog import get_today_checkin
from api.app.services.question_curator import get_personalization


ENERGY_VALUES = {"Very low": 1, "Low": 2, "Moderate": 3, "Good": 4, "Very good": 5}


class DuplicateCheckinError(ValueError):
    """Raised when a user tries to submit more than once on the same date."""


def has_submitted_today(user_id: int, db: Session) -> bool:
    return db.scalar(
        select(DailyCheckin.id).where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.checkin_date == local_today(),
        )
    ) is not None


def validate_submission(user: User, submission: CheckinSubmission, db: Session) -> None:
    form = get_today_checkin(personalization=get_personalization(user, db))
    if submission.form_version != form.form_version:
        raise ValueError("The check-in form has changed. Refresh and try again.")
    for section in form.sections:
        for question in section.questions:
            value = submission.answers.get(question.id)
            if question.required and (value is None or value == "" or value == []):
                raise ValueError(f"Missing required answer: {question.id}")
            if value is None:
                continue
            if question.type in {"number", "linear_scale"}:
                try:
                    number = float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid numeric answer: {question.id}") from exc
                if question.min_value is not None and number < question.min_value:
                    raise ValueError(f"Answer below minimum: {question.id}")
                if question.max_value is not None and number > question.max_value:
                    raise ValueError(f"Answer above maximum: {question.id}")


def save_checkin(user: User, submission: CheckinSubmission, db: Session) -> CheckinSubmissionResult:
    validate_submission(user, submission, db)
    today = local_today()
    answers = submission.answers
    record = DailyCheckin(
        user_id=user.id,
        checkin_date=today,
        submitted_at=utc_now(),
        form_version=submission.form_version,
        mood=float(answers["overall_mood"]),
        stress=float(answers["stress_level"]),
        sleep_hours=float(answers.get("sleep_hours") or 0),
        energy=float(ENERGY_VALUES.get(str(answers["energy_level"]), 3)),
        connectedness=float(answers.get("social_connection") or 3),
        checkin_completed=True,
        support_response=str(answers.get("additional_support") or "No action")[:120],
        note=str(answers.get("additional_context") or "Daily check-in")[:200],
        answers=answers,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCheckinError(
            "You have already completed today's check-in. Come back tomorrow."
        ) from exc
    return CheckinSubmissionResult(
        date=today,
        username=user.username,
        created=True,
        message="Your check-in was saved.",
    )
