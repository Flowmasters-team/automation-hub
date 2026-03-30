"""Сервис AI-чата с SSE-стримингом."""

import json
from typing import AsyncGenerator

import httpx

from app.core.config import settings


async def stream_chat(
    system_prompt: str,
    messages: list[dict],
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """SSE-стриминг ответа от LLM (посимвольный, как в ChatGPT).

    Yields:
        SSE-события в формате: data: {"content": "..."}
    """
    model = model or settings.DEFAULT_MODEL

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "stream": True,
                "messages": [{"role": "system", "content": system_prompt}] + messages,
            },
            timeout=None,
        )
        resp.raise_for_status()

        full_response = ""
        async for line in resp.aiter_lines():
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    full_response += content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        # Финальное событие с полным ответом
        yield f"data: {json.dumps({'done': True, 'full_response': full_response})}\n\n"
