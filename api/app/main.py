from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.app.core.config import settings
from api.app.middleware import (
    CSRFMiddleware,
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from api.app.routers.admin import router as admin_router
from api.app.routers.auth import router as auth_router
from api.app.routers.checkins import router as checkins_router
from api.app.routers.dashboard import router as dashboard_router
from api.app.routers.privacy import router as privacy_router
from api.app.schemas.common import ApiResponse, HealthData


production = settings.app_env == "production"
app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
    docs_url=None if production else "/docs",
    redoc_url=None if production else "/redoc",
    openapi_url=None if production else "/openapi.json",
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.include_router(admin_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(checkins_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(privacy_router, prefix=settings.api_v1_prefix)


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


frontend_directory = Path(__file__).resolve().parents[2] / "frontend"
if frontend_directory.exists():
    app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
