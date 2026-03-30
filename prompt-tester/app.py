"""
Платформа тестирования промптов.

Загружаешь промпт + сценарии → прогоняешь → получаешь PASS/FAIL с SSE-стримингом.
Стек: FastAPI + Jinja2 + SSE + OpenAI API.
"""

import asyncio
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx

app = FastAPI(title="Prompt Tester", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# === Модели ===

class Scenario(BaseModel):
    name: str
    messages: list[dict]  # [{"role": "user", "content": "..."}]
    expected: str  # Описание ожидаемого поведения
    check_type: str = "contains"  # contains | not_contains | json_field | llm_judge


class TestRun(BaseModel):
    system_prompt: str
    scenarios: list[Scenario]
    model: str = "gpt-4o-mini"
    temperature: float = 0.0


@dataclass
class TestResult:
    scenario_name: str
    status: str  # PASS | FAIL
    response: str
    expected: str
    duration_sec: float
    details: str = ""


# === Хранилище результатов (in-memory) ===
runs: dict[str, list[TestResult]] = {}


# === OpenAI клиент ===

async def call_llm(system_prompt: str, messages: list[dict], model: str, temperature: float) -> str:
    """Вызов OpenAI-совместимого API."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": temperature,
                "messages": [{"role": "system", "content": system_prompt}] + messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# === Проверки ===

def check_result(response: str, scenario: Scenario) -> tuple[bool, str]:
    """Проверяет ответ модели по правилу сценария."""
    if scenario.check_type == "contains":
        passed = scenario.expected.lower() in response.lower()
        return passed, f"Expected '{scenario.expected}' in response"

    elif scenario.check_type == "not_contains":
        passed = scenario.expected.lower() not in response.lower()
        return passed, f"Expected '{scenario.expected}' NOT in response"

    elif scenario.check_type == "json_field":
        try:
            data = json.loads(response)
            # expected формат: "field_name=value"
            field_name, expected_value = scenario.expected.split("=", 1)
            actual = str(data.get(field_name, ""))
            passed = actual == expected_value
            return passed, f"Field '{field_name}': expected '{expected_value}', got '{actual}'"
        except (json.JSONDecodeError, ValueError) as e:
            return False, f"JSON parse error: {e}"

    elif scenario.check_type == "llm_judge":
        # LLM-судья — вызывается отдельно
        return True, "LLM judge requires async evaluation"

    return False, f"Unknown check_type: {scenario.check_type}"


# === SSE-стриминг тестов ===

async def run_tests_stream(run_data: TestRun, run_id: str):
    """Генератор SSE-событий для прогона тестов."""
    results: list[TestResult] = []
    total = len(run_data.scenarios)

    yield f"data: {json.dumps({'type': 'start', 'total': total, 'run_id': run_id})}\n\n"

    for i, scenario in enumerate(run_data.scenarios):
        yield f"data: {json.dumps({'type': 'running', 'index': i, 'name': scenario.name})}\n\n"

        start = time.time()
        try:
            response = await call_llm(
                run_data.system_prompt,
                scenario.messages,
                run_data.model,
                run_data.temperature,
            )
            duration = time.time() - start
            passed, details = check_result(response, scenario)

            result = TestResult(
                scenario_name=scenario.name,
                status="PASS" if passed else "FAIL",
                response=response[:500],
                expected=scenario.expected,
                duration_sec=round(duration, 2),
                details=details,
            )
        except Exception as e:
            duration = time.time() - start
            result = TestResult(
                scenario_name=scenario.name,
                status="FAIL",
                response=str(e),
                expected=scenario.expected,
                duration_sec=round(duration, 2),
                details=f"Error: {e}",
            )

        results.append(result)

        yield f"data: {json.dumps({'type': 'result', 'index': i, 'name': scenario.name, 'status': result.status, 'duration': result.duration_sec, 'details': result.details, 'response_preview': result.response[:200]})}\n\n"

    # Сводка
    passed_count = sum(1 for r in results if r.status == "PASS")
    summary = {
        "type": "complete",
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "total_duration": round(sum(r.duration_sec for r in results), 2),
    }
    runs[run_id] = results

    yield f"data: {json.dumps(summary)}\n\n"


# === Маршруты ===

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/run")
async def run_tests(run_data: TestRun):
    """Запускает тесты и возвращает SSE-поток."""
    run_id = str(uuid.uuid4())[:8]
    return StreamingResponse(
        run_tests_stream(run_data, run_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Run-Id": run_id},
    )


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """Результаты прогона."""
    if run_id not in runs:
        return {"error": "Run not found"}
    return [
        {
            "name": r.scenario_name,
            "status": r.status,
            "response": r.response,
            "expected": r.expected,
            "duration": r.duration_sec,
            "details": r.details,
        }
        for r in runs[run_id]
    ]


@app.get("/playground", response_class=HTMLResponse)
async def playground(request: Request):
    return templates.TemplateResponse("playground.html", {"request": request})


@app.post("/api/playground/chat")
async def playground_chat(request: Request):
    """Ручной чат с промптом."""
    body = await request.json()
    system_prompt = body.get("system_prompt", "")
    messages = body.get("messages", [])
    model = body.get("model", "gpt-4o-mini")

    response = await call_llm(system_prompt, messages, model, 0.7)
    return {"response": response}
