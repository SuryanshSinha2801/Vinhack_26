import hashlib
import hmac

from sqlalchemy.orm import Session

from api.app.core.config import settings
from api.app.models import SecurityAuditEvent, User


def actor_reference(value: str) -> str:
    return hmac.new(
        settings.jwt_secret_key.encode(), value.strip().lower().encode(), hashlib.sha256
    ).hexdigest()


def record_audit(
    db: Session,
    event_type: str,
    outcome: str,
    *,
    user: User | None = None,
    attempted_username: str | None = None,
    event_data: dict | None = None,
    commit: bool = True,
) -> None:
    reference_source = user.username if user else attempted_username or "anonymous"
    db.add(
        SecurityAuditEvent(
            event_type=event_type,
            actor_user_id=user.id if user else None,
            actor_reference=actor_reference(reference_source),
            outcome=outcome,
            event_data=event_data or {},
        )
    )
    if commit:
        db.commit()
