"""
5-шаговый конвейер FSM-промптов.

1. Анализ — парсинг реальных диалогов, выявление паттернов и багов
2. Проектирование — генерация таблицы состояний
3. Калибровка — прогон тестовых сценариев, итерации промпта
4. Деплой — публикация через API
5. A/B-анализ — метрики до/после
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from fsm_engine import FSM, State, Transition


class PipelineStage(str, Enum):
    ANALYZE = "analyze"
    DESIGN = "design"
    CALIBRATE = "calibrate"
    DEPLOY = "deploy"
    AB_TEST = "ab_test"


@dataclass
class AnalysisResult:
    """Результат анализа диалогов."""
    total_dialogs: int = 0
    bugs_found: list[dict] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)
    common_intents: list[str] = field(default_factory=list)
    drop_off_points: list[str] = field(default_factory=list)
    avg_messages_per_dialog: float = 0


@dataclass
class CalibrationResult:
    """Результат калибровки."""
    iteration: int
    scenarios_total: int
    scenarios_passed: int
    failures: list[dict] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.scenarios_passed / self.scenarios_total if self.scenarios_total else 0


@dataclass
class ABResult:
    """Результат A/B-теста."""
    period_days: int
    before: dict = field(default_factory=dict)  # {"conversion": 0.15, "avg_messages": 8}
    after: dict = field(default_factory=dict)


@dataclass
class PipelineRun:
    """Один прогон конвейера."""
    niche: str
    client_name: str
    started_at: str = ""
    current_stage: PipelineStage = PipelineStage.ANALYZE
    fsm: FSM | None = None
    analysis: AnalysisResult | None = None
    calibrations: list[CalibrationResult] = field(default_factory=list)
    ab_result: ABResult | None = None
    prompt_versions: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


def analyze_dialogs(dialogs: list[dict]) -> AnalysisResult:
    """Шаг 1: Анализ реальных диалогов."""
    result = AnalysisResult(total_dialogs=len(dialogs))

    for dialog in dialogs:
        messages = dialog.get("messages", [])
        msg_count = len(messages)
        result.avg_messages_per_dialog += msg_count

        # Детекция багов
        for i, msg in enumerate(messages):
            content = msg.get("content", "").lower()
            # Бот повторяется
            if i > 0 and content == messages[i - 1].get("content", "").lower() and msg.get("role") == "assistant":
                result.bugs_found.append({"type": "repeat", "dialog_id": dialog.get("id"), "message_index": i})
            # Бот игнорирует вопрос
            if msg.get("role") == "user" and "?" in content:
                if i + 1 < len(messages) and "?" not in messages[i + 1].get("content", ""):
                    # Проверяем, ответил ли бот по существу (упрощённо)
                    pass

        # Детекция drop-off (последнее сообщение от пользователя без ответа или с негативом)
        if messages and messages[-1].get("role") == "user":
            result.drop_off_points.append(messages[-1].get("content", "")[:100])

    if dialogs:
        result.avg_messages_per_dialog /= len(dialogs)

    return result


def design_fsm(niche: str, analysis: AnalysisResult) -> FSM:
    """Шаг 2: Проектирование FSM на основе анализа."""
    # Базовый шаблон — адаптируется под нишу
    fsm = FSM(
        name=f"FSM: {niche}",
        description=f"Конечный автомат для бота в нише '{niche}'",
        initial_state="greeting",
    )

    # Универсальные состояния
    fsm.add_state(State(
        id="greeting", name="Приветствие",
        description="Первый контакт с клиентом",
        prompt_instructions="Поприветствуй, представься, задай первый квалифицирующий вопрос.",
        max_messages=3,
    ))
    fsm.add_state(State(
        id="qualification", name="Квалификация",
        description="Выявление потребностей",
        prompt_instructions="Задавай вопросы по одному. Собери все обязательные поля.",
        collect_fields=["name", "need", "budget", "timeline"],
        max_messages=10,
    ))
    fsm.add_state(State(
        id="presentation", name="Презентация",
        description="Предложение решения",
        prompt_instructions="На основе собранных данных предложи конкретное решение с ценой.",
        max_messages=5,
    ))
    fsm.add_state(State(
        id="objection", name="Работа с возражениями",
        description="Обработка сомнений клиента",
        prompt_instructions="Выслушай возражение, дай аргументированный ответ, предложи альтернативу.",
        max_messages=8,
    ))
    fsm.add_state(State(
        id="closing", name="Закрытие",
        description="Договорённость о следующем шаге",
        prompt_instructions="Зафиксируй договорённость: дата, время, контакт. Попрощайся тепло.",
        collect_fields=["appointment_date", "contact_phone"],
        max_messages=5,
    ))
    fsm.add_state(State(
        id="handoff", name="Передача менеджеру",
        description="Переключение на живого человека",
        prompt_instructions="Сообщи, что переключаешь на специалиста. Резюмируй собранную информацию.",
        is_terminal=True,
        max_messages=2,
    ))
    fsm.add_state(State(
        id="completed", name="Завершено",
        description="Диалог успешно завершён",
        prompt_instructions="Попрощайся. Напомни контакты.",
        is_terminal=True,
        max_messages=2,
    ))

    # Переходы
    transitions = [
        Transition("greeting", "qualification", "user_responded", "Пользователь ответил на приветствие"),
        Transition("greeting", "handoff", "request_human", "Пользователь сразу просит человека"),
        Transition("qualification", "presentation", "all_fields_collected", "Все обязательные поля собраны"),
        Transition("qualification", "handoff", "request_human", "Пользователь просит человека"),
        Transition("qualification", "qualification", "partial_answer", "Ещё не все поля собраны"),
        Transition("presentation", "closing", "user_agrees", "Клиент согласен"),
        Transition("presentation", "objection", "user_objects", "Клиент возражает или сомневается"),
        Transition("presentation", "qualification", "need_more_info", "Нужна дополнительная информация"),
        Transition("objection", "presentation", "objection_resolved", "Возражение снято"),
        Transition("objection", "closing", "user_agrees", "Клиент согласен после работы с возражением"),
        Transition("objection", "handoff", "cannot_resolve", "Не удаётся снять возражение"),
        Transition("closing", "completed", "appointment_set", "Встреча/замер назначены"),
        Transition("closing", "handoff", "request_human", "Нужен менеджер для финализации"),
    ]
    for t in transitions:
        fsm.add_transition(t)

    return fsm


def calibrate(fsm: FSM, scenarios: list[dict], results: list[dict]) -> CalibrationResult:
    """Шаг 3: Оценка результатов прогона сценариев."""
    passed = 0
    failures = []

    for scenario, result in zip(scenarios, results):
        expected_state = scenario.get("expected_final_state")
        actual_state = result.get("final_state")
        expected_fields = scenario.get("expected_fields", {})
        actual_fields = result.get("collected_data", {})

        state_ok = expected_state == actual_state
        fields_ok = all(actual_fields.get(k) == v for k, v in expected_fields.items())

        if state_ok and fields_ok:
            passed += 1
        else:
            failures.append({
                "scenario": scenario.get("name"),
                "expected_state": expected_state,
                "actual_state": actual_state,
                "missing_fields": [k for k, v in expected_fields.items() if actual_fields.get(k) != v],
            })

    return CalibrationResult(
        iteration=1,
        scenarios_total=len(scenarios),
        scenarios_passed=passed,
        failures=failures,
    )


def generate_deploy_payload(fsm: FSM) -> dict:
    """Шаг 4: Генерация payload для деплоя через API."""
    return {
        "system_prompt": fsm.to_prompt(),
        "metadata": {
            "fsm_name": fsm.name,
            "states_count": len(fsm.states),
            "transitions_count": len(fsm.transitions),
            "generated_at": datetime.now().isoformat(),
        },
    }


def compare_ab(before_metrics: dict, after_metrics: dict) -> dict:
    """Шаг 5: Сравнение метрик до/после."""
    comparison = {}
    for key in set(list(before_metrics.keys()) + list(after_metrics.keys())):
        b = before_metrics.get(key, 0)
        a = after_metrics.get(key, 0)
        if b != 0:
            change_pct = round((a - b) / b * 100, 1)
        else:
            change_pct = None
        comparison[key] = {"before": b, "after": a, "change_pct": change_pct}
    return comparison
