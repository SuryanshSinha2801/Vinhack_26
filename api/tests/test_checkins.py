from fastapi.testclient import TestClient
from openpyxl import load_workbook
from pathlib import Path
from shutil import copy2

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
    assert len(questions) == 15
    assert questions["overall_mood"]["min_value"] == 1
    assert questions["overall_mood"]["max_value"] == 5
    assert questions["stress_level"]["max_label"] == "Very high"
    assert "student_id" not in questions
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


def test_authenticated_checkin_is_saved_to_excel(tmp_path, monkeypatch) -> None:
    source = Path("data/demo/mindtrail_demo_6_months.xlsx")
    target = tmp_path / "demo.xlsx"
    copy2(source, target)
    monkeypatch.setattr("api.app.services.checkin_store.WORKBOOK_PATH", target)

    client = TestClient(app)
    assert client.post(
        "/v1/auth/login", json={"username": "arjun01", "password": "Trail@Arjun26"}
    ).status_code == 200
    response = client.post(
        "/v1/checkins",
        json={
            "form_version": "2026-09-19",
            "answers": {
                "year_of_study": "Year 2",
                "overall_mood": 4,
                "stress_level": 2,
                "energy_level": "Good",
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
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "arjun01"

    workbook = load_workbook(target, read_only=True, data_only=True)
    assert "Check-in Submissions" in workbook.sheetnames
    audit = workbook["Check-in Submissions"]
    assert audit.cell(audit.max_row, 2).value == "arjun01"
    workbook.close()
