from fastapi import APIRouter, Depends, HTTPException, status

from api.app.models import User
from api.app.routers.auth import current_user
from api.app.schemas.checkins import CheckinSubmission, CheckinSubmissionResult, TodayCheckin
from api.app.schemas.common import ApiResponse
from api.app.services.checkin_catalog import get_today_checkin
from api.app.services.checkin_store import save_checkin


router = APIRouter(prefix="/checkins", tags=["check-ins"])


@router.get("/today", response_model=ApiResponse[TodayCheckin])
async def today_checkin() -> ApiResponse[TodayCheckin]:
    return ApiResponse(data=get_today_checkin())


@router.post("", response_model=ApiResponse[CheckinSubmissionResult])
def submit_checkin(payload: CheckinSubmission, user: User = Depends(current_user)):
    try:
        result = save_checkin(user.username, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ApiResponse(data=result)
