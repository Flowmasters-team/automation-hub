"""Модель AI-учителя — 4 слоя контекста."""

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Teacher(Base):
    """AI-учитель с настраиваемой личностью.

    4 слоя контекста:
    1. personality — характер (терпеливый, с юмором, строгий)
    2. knowledge — программа предмета (позже заменяется на RAG)
    3. student_context — знание ученика (прогресс, ошибки, мотивация)
    4. session_context — текущий диалог (управляется в runtime)
    """

    __tablename__ = "teachers"

    name: Mapped[str] = mapped_column(String(100))
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), index=True)

    # Слой 1: Личность
    personality: Mapped[str] = mapped_column(Text)  # "Терпеливый, объясняет с аналогиями из Minecraft"

    # Слой 2: Знание предмета
    knowledge_prompt: Mapped[str] = mapped_column(Text)  # Программа класса, темы

    # Слой 3: Шаблон для знания ученика
    student_prompt_template: Mapped[str] = mapped_column(
        Text,
        default="Ученик {name}, {grade} класс. Пройденные темы: {completed_topics}. Частые ошибки: {common_errors}.",
    )

    avatar_url: Mapped[str] = mapped_column(String(500), default="")

    subject: Mapped["Subject"] = relationship(back_populates="teachers", lazy="raise")
    sessions: Mapped[list["ChatSession"]] = relationship(back_populates="teacher", lazy="raise")

    def build_system_prompt(self, student_context: dict | None = None) -> str:
        """Собирает системный промпт из 3 слоёв (4-й — runtime)."""
        parts = [
            f"# Личность\n{self.personality}",
            f"\n# Предмет\n{self.knowledge_prompt}",
        ]
        if student_context:
            try:
                student_part = self.student_prompt_template.format(**student_context)
                parts.append(f"\n# Ученик\n{student_part}")
            except KeyError:
                pass
        return "\n".join(parts)
