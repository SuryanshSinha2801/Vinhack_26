from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column("email", String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default="student", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    checkins: Mapped[list["DailyCheckin"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"
    __table_args__ = (
        UniqueConstraint("user_id", "checkin_date", name="uq_daily_checkins_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    checkin_date: Mapped[date] = mapped_column(Date, index=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    form_version: Mapped[str] = mapped_column(String(40), default="seed-import")
    mood: Mapped[float] = mapped_column(Float)
    stress: Mapped[float] = mapped_column(Float)
    sleep_hours: Mapped[float] = mapped_column(Float, default=0)
    energy: Mapped[float] = mapped_column(Float)
    connectedness: Mapped[float] = mapped_column(Float, default=3)
    checkin_completed: Mapped[bool] = mapped_column(Boolean, default=True)
    support_response: Mapped[str] = mapped_column(String(120), default="No action")
    note: Mapped[str] = mapped_column(Text, default="Daily check-in")
    answers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="checkins")
