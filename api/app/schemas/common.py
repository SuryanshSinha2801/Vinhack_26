from typing import Generic, TypeVar

from pydantic import BaseModel


DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ApiResponse(BaseModel, Generic[DataT]):
    data: DataT | None = None
    error: ErrorDetail | None = None


class HealthData(BaseModel):
    status: str
    service: str
    environment: str

