from fastapi import FastAPI

from api.app.core.config import settings
from api.app.schemas.common import ApiResponse, HealthData


app = FastAPI(title=settings.app_name, debug=settings.app_debug, version="0.1.0")


def health_response() -> ApiResponse[HealthData]:
    return ApiResponse(
        data=HealthData(
            status="ok",
            service=settings.app_name,
            environment=settings.app_env,
        )
    )


@app.get("/health", response_model=ApiResponse[HealthData], tags=["health"])
async def health() -> ApiResponse[HealthData]:
    return health_response()


@app.get(
    f"{settings.api_v1_prefix}/health",
    response_model=ApiResponse[HealthData],
    tags=["health"],
)
async def versioned_health() -> ApiResponse[HealthData]:
    return health_response()

