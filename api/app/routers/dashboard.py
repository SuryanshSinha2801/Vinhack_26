from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.app.database import get_db
from api.app.models import User
from api.app.routers.auth import current_user
from api.app.schemas.common import ApiResponse
from api.app.schemas.dashboard import UserDashboard
from api.app.services.dashboard import get_user_dashboard


router = APIRouter(prefix="/me", tags=["dashboard"])


@router.get("/dashboard", response_model=ApiResponse[UserDashboard])
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    data = get_user_dashboard(user, db)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No demo history is available for this user")
    return ApiResponse(data=data)
