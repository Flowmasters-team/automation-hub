"""Pydantic-схемы."""

from pydantic import BaseModel, EmailStr


# === Auth ===
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    grade: int | None = None


# === Subject ===
class SubjectResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str


# === Teacher ===
class TeacherResponse(BaseModel):
    id: str
    name: str
    subject_id: str
    personality: str
    avatar_url: str


# === Chat ===
class ChatMessageRequest(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    teacher_id: str
    is_active: bool
    created_at: str


# === Generic ===
class ApiResponse(BaseModel):
    data: dict | list | None = None
    meta: dict | None = None
    errors: list[dict] = []
