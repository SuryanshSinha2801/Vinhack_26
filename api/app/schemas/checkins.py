from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


QuestionType = Literal["text", "number", "single_choice", "multiple_choice", "linear_scale"]


class CheckinOption(BaseModel):
    value: str
    label: str
    triggers_immediate_support: bool = False


class CheckinQuestion(BaseModel):
    id: str
    prompt: str
    type: QuestionType
    required: bool
    help_text: str | None = None
    options: list[CheckinOption] = Field(default_factory=list)
    min_value: float | None = None
    max_value: float | None = None
    min_label: str | None = None
    max_label: str | None = None


class CheckinSection(BaseModel):
    id: str
    title: str
    description: str | None = None
    questions: list[CheckinQuestion] = Field(default_factory=list)


class CheckinPersonalization(BaseModel):
    strategy_version: str
    personalized: bool
    focus_areas: list[str]
    based_on_days: int
    explanation: str


class TodayCheckin(BaseModel):
    date: date
    form_version: str
    title: str
    description: str
    completed: bool = False
    sections: list[CheckinSection]
    immediate_support_message: str
    personalization: CheckinPersonalization | None = None


class CheckinSubmission(BaseModel):
    form_version: str = Field(min_length=1, max_length=80)
    answers: dict[str, Any]

    @field_validator("answers")
    @classmethod
    def validate_answer_envelope(cls, answers: dict[str, Any]) -> dict[str, Any]:
        if len(answers) > 30:
            raise ValueError("Too many answers were submitted")
        for key, value in answers.items():
            if len(key) > 80:
                raise ValueError("Answer identifier is too long")
            if isinstance(value, str) and len(value) > 1_000:
                raise ValueError(f"Answer is too long: {key}")
            if isinstance(value, list):
                if len(value) > 20 or any(not isinstance(item, str) or len(item) > 200 for item in value):
                    raise ValueError(f"Invalid multiple-choice answer: {key}")
            elif isinstance(value, (dict, tuple, set)):
                raise ValueError(f"Nested answers are not allowed: {key}")
        return answers


class CheckinSubmissionResult(BaseModel):
    date: date
    username: str
    created: bool
    message: str
