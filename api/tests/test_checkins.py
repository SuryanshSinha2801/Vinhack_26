from fastapi.testclient import TestClient

from api.app.main import app


client = TestClient(app)


def test_today_checkin_matches_form_structure() -> None:
    response = client.get("/v1/checkins/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None

    checkin = payload["data"]
    assert checkin["title"] == "MindTrail – Student Wellbeing Check-in"
    assert checkin["completed"] is False
    assert len(checkin["sections"]) == 6

    questions = {
        question["id"]: question
        for section in checkin["sections"]
        for question in section["questions"]
    }
    assert len(questions) == 16
    assert questions["overall_mood"]["min_value"] == 1
    assert questions["overall_mood"]["max_value"] == 5
    assert questions["stress_level"]["max_label"] == "Very high"
    assert questions["student_id"]["required"] is False
    assert questions["privacy_acknowledgement"]["required"] is True


def test_immediate_help_option_triggers_support_path() -> None:
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

