from fastapi import APIRouter

from api.app.schemas.checkins import TodayCheckin
from api.app.schemas.common import ApiResponse
from api.app.services.checkin_catalog import get_today_checkin


router = APIRouter(prefix="/checkins", tags=["check-ins"])


@router.get("/today", response_model=ApiResponse[TodayCheckin])
async def today_checkin() -> ApiResponse[TodayCheckin]:
    return ApiResponse(data=get_today_checkin())

