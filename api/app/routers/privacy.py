from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from api.app.core.security import verify_password
from api.app.database import get_db
from api.app.models import User
from api.app.routers.auth import COOKIE_NAME, CSRF_COOKIE_NAME, current_user
from api.app.schemas.common import ApiResponse
from api.app.schemas.privacy import ConsentState, ConsentUpdate, DeleteMyDataRequest, UserDataExport
from api.app.services.privacy import export_user_data, get_consent_state, record_consent
from api.app.services.audit import record_audit


router = APIRouter(prefix="/me", tags=["privacy"])


@router.get("/consent", response_model=ApiResponse[ConsentState])
def consent(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return ApiResponse(data=get_consent_state(user.id, db))


@router.post("/consent", response_model=ApiResponse[ConsentState])
def update_consent(
    payload: ConsentUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    result = record_consent(user.id, payload.personalization_enabled, db)
    record_audit(
        db,
        "privacy.consent_changed",
        "success",
        user=user,
        event_data={"personalization_enabled": payload.personalization_enabled},
    )
    return ApiResponse(data=result)


@router.get("/export", response_model=ApiResponse[UserDataExport])
def export(user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = export_user_data(user, db)
    record_audit(db, "privacy.export", "success", user=user)
    return ApiResponse(data=data)


@router.delete("/data", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_data(
    payload: DeleteMyDataRequest,
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Administrator accounts must be removed by an authorized database operator.",
        )
    if not verify_password(payload.password, user.password_hash):
        record_audit(db, "privacy.delete", "failure", user=user, event_data={"reason": "bad_password"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect")
    record_audit(db, "privacy.delete", "success", user=user, commit=False)
    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")
