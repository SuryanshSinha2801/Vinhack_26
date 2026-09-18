import json
from datetime import date, datetime, timezone
from threading import Lock

from openpyxl import load_workbook

from api.app.schemas.checkins import CheckinSubmission, CheckinSubmissionResult
from api.app.services.checkin_catalog import get_today_checkin
from api.app.services.demo_users import WORKBOOK_PATH


workbook_lock = Lock()
ENERGY_VALUES = {"Very low": 1, "Low": 2, "Moderate": 3, "Good": 4, "Very good": 5}


def validate_submission(submission: CheckinSubmission) -> None:
    form = get_today_checkin()
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


def save_checkin(username: str, submission: CheckinSubmission) -> CheckinSubmissionResult:
    validate_submission(submission)
    today = date.today()
    answers = submission.answers
    mood = float(answers["overall_mood"])
    stress = float(answers["stress_level"])
    sleep = float(answers.get("sleep_hours") or 0)
    energy = float(ENERGY_VALUES.get(str(answers["energy_level"]), 3))
    connectedness = 3.0
    support = str(answers.get("additional_support") or "No action")
    note = str(answers.get("additional_context") or "Daily check-in")[:200]

    with workbook_lock:
        workbook = load_workbook(WORKBOOK_PATH)
        history = workbook["15-Day History"]
        existing_row = None
        for row in range(2, history.max_row + 1):
            row_date = history.cell(row, 1).value
            row_username = str(history.cell(row, 2).value or "").lower()
            normalized_date = row_date.date() if hasattr(row_date, "date") else row_date
            if row_username == username.lower() and normalized_date == today:
                existing_row = row
                break
        values = [today, username, mood, stress, sleep, energy, connectedness, True, support, note]
        if existing_row:
            for column, value in enumerate(values, 1):
                history.cell(existing_row, column, value)
        else:
            history.append(values)

        if "Check-in Submissions" not in workbook.sheetnames:
            audit = workbook.create_sheet("Check-in Submissions")
            audit.append(["Submitted at (UTC)", "Username", "Date", "Form version", "Answers JSON"])
            audit.freeze_panes = "A2"
        audit = workbook["Check-in Submissions"]
        audit.append([
            datetime.now(timezone.utc).replace(tzinfo=None), username, today,
            submission.form_version, json.dumps(answers, ensure_ascii=False),
        ])
        workbook.save(WORKBOOK_PATH)
        workbook.close()
    return CheckinSubmissionResult(
        date=today,
        username=username,
        created=existing_row is None,
        message="Your check-in was saved.",
    )
