"""
FSM Engine для промптов.

Ядро конечного автомата: состояния, сигналы, переходы, guard-условия.
Генерирует промпт-инструкцию для LLM на основе таблицы переходов.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class State:
    """Состояние FSM."""
    id: str
    name: str
    description: str
    prompt_instructions: str  # Что делает бот в этом состоянии
    collect_fields: list[str] = field(default_factory=list)  # Какие данные собирать
    max_messages: int = 10  # Лимит сообщений в состоянии
    is_terminal: bool = False


@dataclass
class Transition:
    """Переход между состояниями."""
    from_state: str
    to_state: str
    signal: str  # Сигнал, вызывающий переход
    guard: str = ""  # Условие (на естественном языке для LLM)
    action: str = ""  # Действие при переходе


@dataclass
class FSM:
    """Конечный автомат."""
    name: str
    description: str
    initial_state: str
    states: dict[str, State] = field(default_factory=dict)
    transitions: list[Transition] = field(default_factory=list)

    def add_state(self, state: State):
        self.states[state.id] = state

    def add_transition(self, transition: Transition):
        self.transitions.append(transition)

    def get_transitions_from(self, state_id: str) -> list[Transition]:
        return [t for t in self.transitions if t.from_state == state_id]

    def validate(self) -> list[str]:
        """Проверяет целостность автомата."""
        errors = []
        state_ids = set(self.states.keys())

        if self.initial_state not in state_ids:
            errors.append(f"Initial state '{self.initial_state}' not found")

        for t in self.transitions:
            if t.from_state not in state_ids:
                errors.append(f"Transition from unknown state '{t.from_state}'")
            if t.to_state not in state_ids:
                errors.append(f"Transition to unknown state '{t.to_state}'")

        # Проверка достижимости всех состояний (DFS)
        reachable = set()
        stack = [self.initial_state]
        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)
            for t in self.get_transitions_from(current):
                stack.append(t.to_state)

        unreachable = state_ids - reachable
        if unreachable:
            errors.append(f"Unreachable states: {unreachable}")

        # Проверка наличия терминальных состояний
        terminals = [s for s in self.states.values() if s.is_terminal]
        if not terminals:
            errors.append("No terminal states defined")

        return errors

    def to_prompt(self) -> str:
        """Генерирует промпт-инструкцию из FSM."""
        lines = []
        lines.append(f"# {self.name}")
        lines.append(f"\n{self.description}\n")

        # Таблица состояний
        lines.append("## Состояния\n")
        for state in self.states.values():
            terminal = " [ТЕРМИНАЛЬНОЕ]" if state.is_terminal else ""
            lines.append(f"### {state.id}: {state.name}{terminal}")
            lines.append(f"{state.description}")
            lines.append(f"**Инструкция:** {state.prompt_instructions}")
            if state.collect_fields:
                lines.append(f"**Собрать:** {', '.join(state.collect_fields)}")
            lines.append(f"**Лимит:** {state.max_messages} сообщений\n")

        # Таблица переходов
        lines.append("## Таблица переходов\n")
        lines.append("| Из | Сигнал | В | Условие | Действие |")
        lines.append("|---|---|---|---|---|")
        for t in self.transitions:
            guard = t.guard or "—"
            action = t.action or "—"
            lines.append(f"| {t.from_state} | {t.signal} | {t.to_state} | {guard} | {action} |")

        # Инструкция для LLM
        lines.append("""
## Правила работы автомата

1. **Текущее состояние** определяется полем `current_state` в JSON-ответе.
2. **Переход** происходит, когда в диалоге возникает сигнал И выполнено условие.
3. **Реконструкция данных**: перед генерацией ответа ЗАНОВО извлеки ВСЕ собранные данные из истории диалога. НЕ полагайся на предыдущий JSON — ты его не видишь.
4. **Один переход за ход**: не перескакивай через состояния.
5. **Приоритет сигналов**: если несколько сигналов возможны, выбери самый специфичный.

## Формат JSON-ответа

```json
{
  "current_state": "STATE_ID",
  "collected_data": {
    "field1": "value1",
    "field2": "value2"
  },
  "next_message": "Текст ответа пользователю",
  "transition_reason": "Почему перешли / остались (для отладки)"
}
```
""")
        return "\n".join(lines)

    def to_mermaid(self) -> str:
        """Генерирует Mermaid-диаграмму."""
        lines = ["stateDiagram-v2"]
        lines.append(f"    [*] --> {self.initial_state}")
        for t in self.transitions:
            label = t.signal
            if t.guard:
                label += f" [{t.guard}]"
            lines.append(f"    {t.from_state} --> {t.to_state}: {label}")
        for s in self.states.values():
            if s.is_terminal:
                lines.append(f"    {s.id} --> [*]")
        return "\n".join(lines)
