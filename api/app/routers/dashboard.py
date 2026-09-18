from fastapi import APIRouter, Depends, HTTPException, status

from api.app.models import User
from api.app.routers.auth import current_user
from api.app.schemas.common import ApiResponse
from api.app.schemas.dashboard import UserDashboard
from api.app.services.dashboard import get_user_dashboard


router = APIRouter(prefix="/me", tags=["dashboard"])


@router.get("/dashboard", response_model=ApiResponse[UserDashboard])
def dashboard(user: User = Depends(current_user)):
    data = get_user_dashboard(user.username, user.display_name)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No demo history is available for this user")
    return ApiResponse(data=data)
