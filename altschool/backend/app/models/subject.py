"""Модель предмета."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(10), default="")  # Emoji
    grade_from: Mapped[int] = mapped_column(default=1)
    grade_to: Mapped[int] = mapped_column(default=11)

    teachers: Mapped[list["Teacher"]] = relationship(back_populates="subject", lazy="raise")
