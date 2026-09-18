from datetime import date

from api.app.schemas.checkins import (
    CheckinOption,
    CheckinQuestion,
    CheckinSection,
    TodayCheckin,
)


def options(*labels: str) -> list[CheckinOption]:
    return [CheckinOption(value=label, label=label) for label in labels]


def get_today_checkin() -> TodayCheckin:
    """Return the current MindTrail check-in form.

    The catalog mirrors the linked Google Form while keeping the API independent
    from Google Forms. Completion will be populated from persistence later.
    """

    return TodayCheckin(
        date=date.today(),
        form_version="2026-09-19",
        title="MindTrail – Student Wellbeing Check-in",
        description=(
            "A short, private-feeling daily check-in designed for the MindTrail "
            "student wellbeing environment. Responses support reflection and "
            "connection to appropriate resources; they are not for academic grading."
        ),
        sections=[
            CheckinSection(
                id="about_you",
                title="1. A little about you",
                description="A broad study-year choice adds context without asking for an identifier.",
                questions=[
                    CheckinQuestion(
                        id="year_of_study",
                        prompt="Year of study",
                        type="single_choice",
                        required=True,
                        options=options("Year 1", "Year 2", "Year 3", "Year 4", "Other"),
                    ),
                ],
            ),
            CheckinSection(
                id="today",
                title="2. How are you doing today?",
                description="There are no right or wrong answers. Choose what feels closest to your experience.",
                questions=[
                    CheckinQuestion(
                        id="overall_mood",
                        prompt="How would you describe your overall mood today?",
                        type="linear_scale",
                        required=True,
                        min_value=1,
                        max_value=5,
                        min_label="Very low",
                        max_label="Very good",
                    ),
                    CheckinQuestion(
                        id="stress_level",
                        prompt="How stressed do you feel today?",
                        type="linear_scale",
                        required=True,
                        min_value=1,
                        max_value=5,
                        min_label="Very low",
                        max_label="Very high",
                    ),
                    CheckinQuestion(
                        id="energy_level",
                        prompt="How would you describe your energy today?",
                        type="single_choice",
                        required=True,
                        options=options("Very low", "Low", "Moderate", "Good", "Very good"),
                    ),
                ],
            ),
            CheckinSection(
                id="daily_rhythm",
                title="3. Sleep, study & daily rhythm",
                questions=[
                    CheckinQuestion(
                        id="sleep_quality",
                        prompt="How was your sleep recently?",
                        type="single_choice",
                        required=True,
                        options=options("Very poor", "Poor", "Average", "Good", "Very good"),
                    ),
                    CheckinQuestion(
                        id="sleep_hours",
                        prompt="Approximately how many hours did you sleep last night?",
                        type="number",
                        required=False,
                        help_text="Example: 6.5",
                        min_value=0,
                        max_value=24,
                    ),
                    CheckinQuestion(
                        id="academic_workload",
                        prompt="How is your academic workload feeling right now?",
                        type="single_choice",
                        required=True,
                        options=options(
                            "Very manageable", "Manageable", "Moderate", "Difficult", "Very difficult"
                        ),
                    ),
                    CheckinQuestion(
                        id="affected_areas",
                        prompt="Which areas are affecting you most right now?",
                        type="multiple_choice",
                        required=False,
                        options=options(
                            "Academic workload",
                            "Exams or deadlines",
                            "Sleep or tiredness",
                            "Time management",
                            "Relationships or social life",
                            "Homesickness or adjustment",
                            "Financial concerns",
                            "Other",
                            "Nothing in particular",
                        ),
                    ),
                ],
            ),
            CheckinSection(
                id="support_resources",
                title="4. Support & resources",
                description="You stay in control of what happens next.",
                questions=[
                    CheckinQuestion(
                        id="additional_support",
                        prompt="Would additional support be useful right now?",
                        type="single_choice",
                        required=True,
                        options=options(
                            "No, I am doing okay",
                            "Maybe – I would like some resources",
                            "Yes – I would like to talk to someone",
                            "I am not sure",
                        ),
                    ),
                    CheckinQuestion(
                        id="support_types",
                        prompt="What kind of support would be useful?",
                        type="multiple_choice",
                        required=False,
                        options=options(
                            "Stress management",
                            "Sleep and wellbeing",
                            "Academic pacing / study support",
                            "Someone to talk to",
                            "Peer support",
                            "Counselling / professional support",
                            "Campus wellbeing resources",
                            "A short break or calming exercise",
                            "I am not sure",
                        ),
                    ),
                    CheckinQuestion(
                        id="additional_context",
                        prompt="Is there anything you would like MindTrail to know? (optional)",
                        type="text",
                        required=False,
                        help_text="Share only what you are comfortable sharing.",
                    ),
                ],
            ),
            CheckinSection(
                id="immediate_support",
                title="5. Immediate support",
                description=(
                    "This question helps the prototype offer an appropriate support path. "
                    "It is not a clinical assessment."
                ),
                questions=[
                    CheckinQuestion(
                        id="immediate_help",
                        prompt="Do you feel unsafe or in need of immediate help right now?",
                        type="single_choice",
                        required=True,
                        help_text=(
                            "If you are in immediate danger or think you may hurt yourself or "
                            "someone else, contact your local emergency service or your "
                            "institution's crisis/support service now."
                        ),
                        options=[
                            CheckinOption(value="No", label="No"),
                            CheckinOption(value="I am not sure", label="I am not sure"),
                            CheckinOption(
                                value="Yes – I need immediate help",
                                label="Yes – I need immediate help",
                                triggers_immediate_support=True,
                            ),
                        ],
                    )
                ],
            ),
            CheckinSection(
                id="choice_privacy",
                title="6. Your choice & privacy",
                questions=[
                    CheckinQuestion(
                        id="follow_up_requested",
                        prompt="Would you like a follow-up from a wellbeing/support person?",
                        type="single_choice",
                        required=True,
                        options=options("Yes", "No", "I am not sure"),
                    ),
                    CheckinQuestion(
                        id="trend_suggestions_consent",
                        prompt="Would you like MindTrail to use your recent check-in trends to suggest resources?",
                        type="single_choice",
                        required=True,
                        options=options("Yes", "No", "I am not sure"),
                    ),
                    CheckinQuestion(
                        id="privacy_acknowledgement",
                        prompt="Privacy acknowledgement",
                        type="multiple_choice",
                        required=True,
                        options=options(
                            "I understand that this check-in is voluntary and is intended to support my wellbeing."
                        ),
                    ),
                ],
            ),
        ],
        immediate_support_message=(
            "If you feel unsafe or are in immediate danger, contact your local emergency "
            "service, a trusted person nearby, or your institution's emergency/crisis "
            "support service. Do not rely on MindTrail for emergency assistance."
        ),
    )
