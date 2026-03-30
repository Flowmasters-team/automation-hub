"""Эндпоинты чата с AI-учителями (SSE-стриминг)."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.teacher import Teacher
from app.models.session import ChatSession, ChatMessage, MessageRole
from app.schemas import ChatMessageRequest, ChatSessionResponse, ChatMessageResponse
from app.services.ai_chat import stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    teacher_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать новую чат-сессию с учителем."""
    result = await db.execute(select(Teacher).where(Teacher.id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    session = ChatSession(user_id=user.id, teacher_id=teacher_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ChatSessionResponse(
        id=session.id, title=session.title, teacher_id=session.teacher_id,
        is_active=session.is_active, created_at=str(session.created_at),
    )


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc())
    )
    return [
        ChatSessionResponse(
            id=s.id, title=s.title, teacher_id=s.teacher_id,
            is_active=s.is_active, created_at=str(s.created_at),
        )
        for s in result.scalars()
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_user_session(session_id, user.id, db)
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    )
    return [
        ChatMessageResponse(id=m.id, role=m.role.value, content=m.content, created_at=str(m.created_at))
        for m in result.scalars()
    ]


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    data: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отправить сообщение и получить SSE-стрим ответа учителя."""
    session = await _get_user_session(session_id, user.id, db)

    # Загружаем учителя
    teacher_result = await db.execute(select(Teacher).where(Teacher.id == session.teacher_id))
    teacher = teacher_result.scalar_one()

    # Сохраняем сообщение ученика
    user_msg = ChatMessage(session_id=session_id, role=MessageRole.USER, content=data.content)
    db.add(user_msg)
    await db.commit()

    # Собираем историю
    messages_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    )
    history = [{"role": m.role.value, "content": m.content} for m in messages_result.scalars()]

    # Строим системный промпт (3 слоя)
    student_context = {
        "name": user.full_name,
        "grade": str(user.grade or "не указан"),
        "completed_topics": "пока нет",
        "common_errors": "пока нет",
    }
    system_prompt = teacher.build_system_prompt(student_context)

    async def sse_and_save():
        """Стримим ответ и сохраняем полный текст в БД."""
        full_response = ""
        async for chunk in stream_chat(system_prompt, history):
            yield chunk
            # Извлекаем текст из чанка для сохранения
            if '"done": true' in chunk:
                import json
                try:
                    data_str = chunk.split("data: ", 1)[1].strip()
                    parsed = json.loads(data_str)
                    full_response = parsed.get("full_response", full_response)
                except (json.JSONDecodeError, IndexError):
                    pass

        # Сохраняем ответ учителя
        if full_response:
            async with db.begin():
                assistant_msg = ChatMessage(
                    session_id=session_id, role=MessageRole.ASSISTANT, content=full_response
                )
                db.add(assistant_msg)

    return StreamingResponse(sse_and_save(), media_type="text/event-stream")


async def _get_user_session(session_id: str, user_id: str, db: AsyncSession) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
