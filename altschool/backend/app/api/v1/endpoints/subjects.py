"""Эндпоинты предметов и учителей."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas import SubjectResponse, TeacherResponse

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("/", response_model=list[SubjectResponse])
async def list_subjects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subject).order_by(Subject.name))
    return [SubjectResponse(id=s.id, name=s.name, description=s.description, icon=s.icon) for s in result.scalars()]


@router.get("/{subject_id}/teachers", response_model=list[TeacherResponse])
async def list_teachers(
    subject_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Teacher).where(Teacher.subject_id == subject_id)
    )
    return [
        TeacherResponse(id=t.id, name=t.name, subject_id=t.subject_id, personality=t.personality, avatar_url=t.avatar_url)
        for t in result.scalars()
    ]
