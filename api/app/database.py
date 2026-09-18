from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from api.app.core.config import settings


if settings.auth_database_url.startswith("sqlite"):
    database_path = settings.auth_database_url.removeprefix("sqlite:///./")
    if database_path != settings.auth_database_url:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.auth_database_url,
    connect_args={"check_same_thread": False} if settings.auth_database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as session:
        yield session
