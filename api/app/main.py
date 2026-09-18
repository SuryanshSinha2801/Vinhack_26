from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.app.core.config import settings
from api.app.database import Base, engine
from api.app.routers.auth import router as auth_router
from api.app.routers.checkins import router as checkins_router
from api.app.routers.dashboard import router as dashboard_router
from api.app.schemas.common import ApiResponse, HealthData
from api.app.services.demo_users import seed_demo_users


app = FastAPI(title=settings.app_name, debug=settings.app_debug, version="0.1.0")
Base.metadata.create_all(bind=engine)
seed_demo_users()
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(checkins_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)


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
