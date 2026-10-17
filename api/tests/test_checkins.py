from fastapi.testclient import TestClient
from datetime import date
from uuid import uuid4

from sqlalchemy import select

from api.app.core.security import hash_password
from api.app.database import SessionLocal
from api.app.main import app
from api.app.models import DailyCheckin, User
from api.app.services.question_curator import get_personalization, rank_focus_areas


client = TestClient(app)


def login(test_client: TestClient) -> None:
    assert test_client.post(
        "/v1/auth/login", json={"username": "arjun01", "password": "Trail@Arjun26"}
    ).status_code == 200


def submission_payload() -> dict:
    return {
        "form_version": "2026-10-17",
        "answers": {
            "year_of_study": "Year 2",
            "overall_mood": 4,
            "stress_level": 2,
            "energy_level": "Good",
            "social_connection": 4,
            "sleep_quality": "Good",
            "sleep_hours": 7,
            "academic_workload": "Manageable",
            "additional_support": "No, I am doing okay",
            "immediate_help": "No",
            "follow_up_requested": "No",
            "trend_suggestions_consent": "Yes",
            "privacy_acknowledgement": [
                "I understand that this check-in is voluntary and is intended to support my wellbeing."
            ],
        },
    }


def test_today_checkin_matches_form_structure() -> None:
    assert TestClient(app).get("/v1/checkins/today").status_code == 401
    login(client)
    response = client.get("/v1/checkins/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None

    checkin = payload["data"]
    assert checkin["title"] == "MindTrail – Student Wellbeing Check-in"
    assert isinstance(checkin["completed"], bool)
    assert len(checkin["sections"]) == 6
    assert checkin["personalization"]["strategy_version"] == "adaptive-checkin-v1"
    assert len(checkin["personalization"]["focus_areas"]) == 2

    questions = {
        question["id"]: question
        for section in checkin["sections"]
        for question in section["questions"]
    }
    assert 10 <= len(questions) <= 13
    assert questions["overall_mood"]["min_value"] == 1
    assert questions["overall_mood"]["max_value"] == 5
    assert questions["stress_level"]["max_label"] == "Very high"
    assert "student_id" not in questions
    assert questions["privacy_acknowledgement"]["required"] is True


def test_curator_prioritizes_sleep_and_academic_pressure() -> None:
    records = [
        {
            "mood": 3.0,
            "stress": 4.2 + index * 0.05,
            "sleep_hours": 5.5 - index * 0.05,
            "energy": 3.0,
            "connectedness": 4.0,
        }
        for index in range(14)
    ]
    focus = rank_focus_areas(records, "student", date(2026, 10, 17))
    assert set(focus) == {"sleep", "academic"}


def test_curator_respects_trend_personalization_opt_out() -> None:
    with SessionLocal() as db:
        user = User(
            username=f"optout-{uuid4().hex}",
            display_name="Opt Out",
            password_hash=hash_password("testing-password"),
        )
        db.add(user)
        db.flush()
        db.add(
            DailyCheckin(
                user_id=user.id,
                checkin_date=date(2098, 12, 31),
                mood=3,
                stress=3,
                sleep_hours=7,
                energy=3,
                connectedness=3,
                answers={"trend_suggestions_consent": "No"},
            )
        )
        db.commit()
        personalization = get_personalization(user, db)
    assert personalization.personalized is False
    assert personalization.based_on_days == 0
    assert "were not used" in personalization.explanation


def test_immediate_help_option_triggers_support_path() -> None:
    login(client)
    response = client.get("/v1/checkins/today")
    sections = response.json()["data"]["sections"]
    immediate_help = next(
        question
        for section in sections
        for question in section["questions"]
        if question["id"] == "immediate_help"
    )

    triggering_options = [
        option for option in immediate_help["options"] if option["triggers_immediate_support"]
    ]
    assert triggering_options == [
        {
            "value": "Yes – I need immediate help",
            "label": "Yes – I need immediate help",
            "triggers_immediate_support": True,
        }
    ]


def test_authenticated_checkin_is_saved_to_database(monkeypatch) -> None:
    test_day = date(2099, 1, 2)
    monkeypatch.setattr("api.app.services.checkin_store.local_today", lambda: test_day)

    client = TestClient(app)
    username = f"checkin-{uuid4().hex}"
    register = client.post(
        "/v1/auth/register",
        json={"username": username, "display_name": "Test Student", "password": "testing-password"},
    )
    assert register.status_code == 201
    assert client.get("/v1/checkins/today").json()["data"]["completed"] is False
    response = client.post("/v1/checkins", json=submission_payload())
    assert response.status_code == 200
    assert response.json()["data"]["username"] == username
    assert response.json()["data"]["date"] == test_day.isoformat()
    assert client.get("/v1/checkins/today").json()["data"]["completed"] is True

    duplicate = client.post("/v1/checkins", json=submission_payload())
    assert duplicate.status_code == 409
    assert "already completed" in duplicate.json()["detail"]

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        saved = db.scalars(
            select(DailyCheckin).where(
                DailyCheckin.user_id == user.id,
                DailyCheckin.checkin_date == test_day,
            )
        ).all()
        assert len(saved) == 1
        assert saved[0].answers["overall_mood"] == 4
