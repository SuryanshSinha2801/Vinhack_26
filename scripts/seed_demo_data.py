from sqlalchemy import func, select

from api.app.database import SessionLocal, engine
from api.app.core.config import settings
from api.app.models import DailyCheckin, User
from api.app.services.demo_users import seed_demo_history, seed_demo_users


def main() -> None:
    if settings.app_env == "production":
        raise SystemExit("Demo-data seeding is disabled in production.")
    seed_demo_users()
    seed_demo_history()
    with SessionLocal() as db:
        user_count = db.scalar(select(func.count(User.id))) or 0
        checkin_count = db.scalar(select(func.count(DailyCheckin.id))) or 0
    print(f"Database: {engine.dialect.name}")
    print(f"Users: {user_count}")
    print(f"Daily check-ins: {checkin_count}")


if __name__ == "__main__":
    main()
