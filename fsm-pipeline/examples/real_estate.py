"""Пример FSM: агентство недвижимости."""

from fsm_engine import FSM, State, Transition


def build() -> FSM:
    fsm = FSM(
        name="Агентство недвижимости — бот-консультант",
        description="Бот для агентства недвижимости. Квалифицирует запрос (покупка/аренда/продажа), собирает параметры и назначает просмотр.",
        initial_state="greeting",
    )

    states = [
        State("greeting", "Приветствие", "Первый контакт",
              "Поприветствуй. Спроси: покупка, аренда или продажа?", max_messages=3),
        State("intent", "Определение цели", "Покупка / аренда / продажа",
              "Уточни цель: покупка, аренда или продажа. Если продажа — переходи к оценке.",
              collect_fields=["intent_type"], max_messages=4),
        State("buy_params", "Параметры покупки", "Сбор требований для покупки",
              "Собери: район, количество комнат, бюджет, срочность, ипотека (да/нет).",
              collect_fields=["district", "rooms", "budget", "urgency", "mortgage"], max_messages=10),
        State("rent_params", "Параметры аренды", "Сбор требований для аренды",
              "Собери: район, комнаты, бюджет/мес, дата заезда, с животными/детьми.",
              collect_fields=["district", "rooms", "monthly_budget", "move_date", "pets_kids"], max_messages=8),
        State("sell_params", "Параметры продажи", "Оценка объекта",
              "Собери: адрес, площадь, комнаты, этаж/этажность, ремонт, желаемая цена.",
              collect_fields=["address", "area_sqm", "rooms", "floor", "renovation", "desired_price"], max_messages=8),
        State("presentation", "Подбор вариантов", "Предложение объектов",
              "На основе параметров предложи 2-3 подходящих варианта. Укажи цену, район, ключевые плюсы.",
              max_messages=6),
        State("viewing", "Назначение просмотра", "Организация встречи",
              "Предложи даты просмотра. Собери: имя, телефон, удобное время.",
              collect_fields=["client_name", "phone", "viewing_date"], max_messages=5),
        State("completed", "Просмотр назначен", "Завершение",
              "Подтверди запись. Отправь адрес и контакт агента.", is_terminal=True, max_messages=2),
        State("handoff", "Передача агенту", "Сложный запрос",
              "Переключи на агента. Резюмируй запрос.", is_terminal=True, max_messages=2),
    ]
    for s in states:
        fsm.add_state(s)

    transitions = [
        Transition("greeting", "intent", "user_responded"),
        Transition("intent", "buy_params", "intent_buy", "Клиент хочет купить"),
        Transition("intent", "rent_params", "intent_rent", "Клиент хочет арендовать"),
        Transition("intent", "sell_params", "intent_sell", "Клиент хочет продать"),
        Transition("intent", "handoff", "request_human"),
        Transition("buy_params", "presentation", "params_collected"),
        Transition("rent_params", "presentation", "params_collected"),
        Transition("sell_params", "viewing", "params_collected", "Для продажи — сразу на оценку/показ"),
        Transition("presentation", "viewing", "user_interested", "Клиент заинтересован"),
        Transition("presentation", "handoff", "no_match", "Нет подходящих вариантов"),
        Transition("viewing", "completed", "viewing_set"),
        Transition("viewing", "handoff", "request_human"),
    ]
    for t in transitions:
        fsm.add_transition(t)

    return fsm


if __name__ == "__main__":
    fsm = build()
    errors = fsm.validate()
    print("Errors:", errors) if errors else print(fsm.to_prompt())
