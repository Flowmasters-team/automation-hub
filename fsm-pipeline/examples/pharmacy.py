"""Пример FSM: аптечная сеть."""

from fsm_engine import FSM, State, Transition


def build() -> FSM:
    fsm = FSM(
        name="Аптечная сеть — бот-консультант",
        description="Бот для аптечной сети. Помогает найти лекарство, проверить наличие, забронировать. НЕ ставит диагнозы.",
        initial_state="greeting",
    )

    states = [
        State("greeting", "Приветствие", "Первый контакт",
              "Поприветствуй. Спроси, чем помочь: найти лекарство, проверить наличие, узнать график работы.",
              max_messages=3),
        State("search", "Поиск лекарства", "Клиент ищет конкретный препарат",
              "Уточни название препарата и дозировку. Если не уверен в названии — предложи варианты. "
              "ВАЖНО: не рекомендуй лекарства, не ставь диагнозы.",
              collect_fields=["drug_name", "dosage"], max_messages=6),
        State("availability", "Проверка наличия", "Есть ли в аптеке",
              "Сообщи о наличии, цене, аналогах. Спроси, в каком районе удобнее забрать.",
              collect_fields=["preferred_location"], max_messages=5),
        State("booking", "Бронирование", "Резерв лекарства",
              "Забронируй на 24 часа. Собери: имя, телефон, аптека. Подтверди бронь.",
              collect_fields=["client_name", "phone", "pharmacy_location"], max_messages=5),
        State("info", "Справочная информация", "График, адреса, услуги",
              "Ответь на вопрос о графике работы, адресах, услугах (вакцинация, измерение давления и т.д.).",
              max_messages=4),
        State("symptoms", "Симптомы — отказ", "Клиент описывает симптомы",
              "СТРОГО: не ставь диагноз, не рекомендуй лечение. "
              "Скажи: 'Я не могу рекомендовать лечение. Обратитесь к врачу. "
              "Могу помочь найти лекарство, если у вас есть рецепт или название.'",
              max_messages=3),
        State("completed", "Готово", "Бронь оформлена или вопрос решён",
              "Подтверди результат. Напомни адрес аптеки и график. Попрощайся.",
              is_terminal=True, max_messages=2),
        State("handoff", "Фармацевт", "Переключение на фармацевта",
              "Переключи на фармацевта. Резюмируй запрос.",
              is_terminal=True, max_messages=2),
    ]
    for s in states:
        fsm.add_state(s)

    transitions = [
        Transition("greeting", "search", "wants_drug", "Клиент называет лекарство"),
        Transition("greeting", "info", "wants_info", "Вопрос про график/адрес/услуги"),
        Transition("greeting", "symptoms", "describes_symptoms", "Описывает симптомы вместо названия"),
        Transition("greeting", "handoff", "request_human"),
        Transition("search", "availability", "drug_identified", "Препарат определён"),
        Transition("search", "handoff", "unclear_drug", "Не удаётся определить препарат"),
        Transition("symptoms", "search", "has_prescription", "У клиента есть рецепт/название"),
        Transition("symptoms", "handoff", "insists_on_advice", "Настаивает на рекомендации"),
        Transition("availability", "booking", "wants_to_book", "Хочет забронировать"),
        Transition("availability", "completed", "just_checking", "Только проверял наличие"),
        Transition("booking", "completed", "booking_confirmed"),
        Transition("info", "completed", "question_answered"),
        Transition("info", "search", "also_needs_drug", "Также нужно лекарство"),
    ]
    for t in transitions:
        fsm.add_transition(t)

    return fsm


if __name__ == "__main__":
    fsm = build()
    errors = fsm.validate()
    print("Errors:", errors) if errors else print(fsm.to_prompt())
