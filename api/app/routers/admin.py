from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.app.database import get_db
from api.app.models import User
from api.app.routers.auth import current_admin
from api.app.schemas.admin import AdminDashboard
from api.app.schemas.common import ApiResponse
from api.app.services.admin_dashboard import get_admin_dashboard
from api.app.services.audit import record_audit


router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/dashboard", response_model=ApiResponse[AdminDashboard])
def admin_dashboard(
    days: int = Query(default=30, ge=7, le=180),
    admin: User = Depends(current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[AdminDashboard]:
    data = get_admin_dashboard(db, days)
    record_audit(db, "admin.dashboard_view", "success", user=admin, event_data={"days": days})
    return ApiResponse(data=data)
