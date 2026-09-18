from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field


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


class TodayCheckin(BaseModel):
    date: date
    form_version: str
    title: str
    description: str
    completed: bool = False
    sections: list[CheckinSection]
    immediate_support_message: str


class CheckinSubmission(BaseModel):
    form_version: str
    answers: dict[str, Any]


class CheckinSubmissionResult(BaseModel):
    date: date
    username: str
    created: bool
    message: str
