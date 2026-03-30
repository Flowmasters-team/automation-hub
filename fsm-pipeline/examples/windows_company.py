"""Пример FSM: оконная компания."""

from fsm_engine import FSM, State, Transition


def build() -> FSM:
    fsm = FSM(
        name="Оконная компания — бот-консультант",
        description=(
            "Бот для оконной компании. Квалифицирует клиента, выявляет тип работ "
            "(остекление балкона, замена окон, новостройка), собирает параметры и "
            "назначает замер."
        ),
        initial_state="greeting",
    )

    fsm.add_state(State(
        id="greeting", name="Приветствие",
        description="Первый контакт",
        prompt_instructions=(
            "Поприветствуй клиента. Представься как консультант оконной компании. "
            "Спроси, что интересует: замена окон, остекление балкона или что-то другое."
        ),
        max_messages=3,
    ))

    fsm.add_state(State(
        id="need_detection", name="Выявление потребности",
        description="Определяем тип работ",
        prompt_instructions=(
            "Уточни тип работ. Задавай по одному вопросу:\n"
            "- Что именно нужно? (замена, остекление, ремонт)\n"
            "- Количество окон/балконов\n"
            "- Тип дома (панельный, кирпичный, новостройка)\n"
            "- Этаж"
        ),
        collect_fields=["work_type", "quantity", "house_type", "floor"],
        max_messages=8,
    ))

    fsm.add_state(State(
        id="dimensions", name="Размеры и параметры",
        description="Сбор размеров",
        prompt_instructions=(
            "Спроси приблизительные размеры. Если клиент не знает — "
            "предложи стандартные размеры и скажи, что точные снимет замерщик. "
            "Уточни: стеклопакет (одно/двух/трёхкамерный), цвет профиля."
        ),
        collect_fields=["dimensions", "glass_type", "profile_color"],
        max_messages=6,
    ))

    fsm.add_state(State(
        id="pricing", name="Предварительный расчёт",
        description="Ориентировочная стоимость",
        prompt_instructions=(
            "На основе собранных данных назови ориентировочную вилку цен. "
            "Подчеркни, что точная цена — после замера. "
            "Упомяни текущую акцию, если есть."
        ),
        max_messages=4,
    ))

    fsm.add_state(State(
        id="objection", name="Возражения",
        description="Работа с ценой и сомнениями",
        prompt_instructions=(
            "Типичные возражения: 'дорого', 'подумаю', 'у конкурентов дешевле'. "
            "Отвечай:\n"
            "- 'Дорого' → рассрочка, скидка за объём, сравнение по сроку службы\n"
            "- 'Подумаю' → замер бесплатный и ни к чему не обязывает\n"
            "- 'Конкуренты' → наш профиль VEKA/KBE, гарантия 10 лет"
        ),
        max_messages=6,
    ))

    fsm.add_state(State(
        id="appointment", name="Назначение замера",
        description="Фиксация даты и контактов",
        prompt_instructions=(
            "Предложи удобное время для бесплатного замера. "
            "Собери: имя, телефон, адрес, удобную дату/время. "
            "Подтверди: 'Замерщик приедет [дата] в [время] по адресу [адрес]'."
        ),
        collect_fields=["client_name", "phone", "address", "appointment_date", "appointment_time"],
        max_messages=6,
    ))

    fsm.add_state(State(
        id="completed", name="Замер назначен",
        description="Успешное завершение",
        prompt_instructions="Подтверди запись. Напомни телефон компании. Попрощайся тепло.",
        is_terminal=True,
        max_messages=2,
    ))

    fsm.add_state(State(
        id="handoff", name="Передача менеджеру",
        description="Сложный случай",
        prompt_instructions="Сообщи, что переключаешь на менеджера. Кратко резюмируй запрос.",
        is_terminal=True,
        max_messages=2,
    ))

    # Переходы
    for t in [
        Transition("greeting", "need_detection", "user_responded"),
        Transition("greeting", "handoff", "request_human"),
        Transition("need_detection", "dimensions", "work_type_clear", "Тип работ определён"),
        Transition("need_detection", "handoff", "request_human"),
        Transition("dimensions", "pricing", "dimensions_collected", "Размеры и параметры собраны"),
        Transition("pricing", "appointment", "user_agrees", "Клиент готов к замеру"),
        Transition("pricing", "objection", "user_objects", "Клиент сомневается"),
        Transition("objection", "appointment", "objection_resolved", "Сомнения сняты"),
        Transition("objection", "handoff", "cannot_resolve", "Не удаётся убедить"),
        Transition("appointment", "completed", "appointment_set", "Замер назначен"),
        Transition("appointment", "handoff", "request_human"),
    ]:
        fsm.add_transition(t)

    return fsm


if __name__ == "__main__":
    fsm = build()
    errors = fsm.validate()
    if errors:
        print("Errors:", errors)
    else:
        print(fsm.to_prompt())
        print("\n---\n")
        print(fsm.to_mermaid())
