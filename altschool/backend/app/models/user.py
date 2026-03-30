"""Модель пользователя (ученик)."""

import enum
from sqlalchemy import String, Enum as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(PgEnum(UserRole), default=UserRole.STUDENT)
    grade: Mapped[int | None] = mapped_column(default=None)  # Класс (1-11)
    is_active: Mapped[bool] = mapped_column(default=True)

    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user", lazy="raise")
