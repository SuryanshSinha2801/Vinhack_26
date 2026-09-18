from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.split())


class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    id: int
    username: str
    display_name: str
    created_at: datetime

    model_config = {"from_attributes": True}
