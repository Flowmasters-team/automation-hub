"""Модели чат-сессий и сообщений."""

import enum
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Enum as PgEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    teacher_id: Mapped[str] = mapped_column(ForeignKey("teachers.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Новый диалог")
    is_active: Mapped[bool] = mapped_column(default=True)

    user: Mapped["User"] = relationship(back_populates="sessions", lazy="raise")
    teacher: Mapped["Teacher"] = relationship(back_populates="sessions", lazy="raise")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", lazy="raise", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[MessageRole] = mapped_column(PgEnum(MessageRole))
    content: Mapped[str] = mapped_column(Text)

    session: Mapped["ChatSession"] = relationship(back_populates="messages", lazy="raise")
