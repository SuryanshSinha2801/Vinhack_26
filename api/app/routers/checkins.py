from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.app.database import get_db
from api.app.models import User
from api.app.routers.auth import current_user
from api.app.schemas.checkins import CheckinSubmission, CheckinSubmissionResult, TodayCheckin
from api.app.schemas.common import ApiResponse
from api.app.services.checkin_catalog import get_today_checkin
from api.app.services.checkin_store import DuplicateCheckinError, has_submitted_today, save_checkin
from api.app.services.question_curator import get_personalization


router = APIRouter(prefix="/checkins", tags=["check-ins"])


@router.get("/today", response_model=ApiResponse[TodayCheckin])
async def today_checkin(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> ApiResponse[TodayCheckin]:
    return ApiResponse(
        data=get_today_checkin(
            completed=has_submitted_today(user.id, db),
            personalization=get_personalization(user, db),
        )
    )


@router.post("", response_model=ApiResponse[CheckinSubmissionResult])
def submit_checkin(
    payload: CheckinSubmission,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    try:
        result = save_checkin(user, payload, db)
    except DuplicateCheckinError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ApiResponse(data=result)
