"""Модуль календаря Bitrix24."""

from src.core.registry import registry

MODULE = "calendar"


# === СОБЫТИЯ ===
@registry.tool("calendar_event_list", "Список событий календаря", MODULE, {
    "type": {"type": "string", "description": "user|group|company_calendar"},
    "ownerId": {"type": "integer"},
    "from": {"type": "string", "description": "Дата начала (YYYY-MM-DD)"},
    "to": {"type": "string", "description": "Дата конца"},
})
async def event_list(client, type="user", ownerId=0, **kwargs):
    params = {"type": type, "ownerId": ownerId}
    if "from" in kwargs:
        params["from"] = kwargs["from"]
    if "to" in kwargs:
        params["to"] = kwargs["to"]
    return await client.call("calendar.event.get", params)

@registry.tool("calendar_event_get", "Получить событие", MODULE, {"id": {"type": "integer"}})
async def event_get(client, id):
    return await client.call("calendar.event.getById", {"id": id})

@registry.tool("calendar_event_add", "Создать событие", MODULE, {
    "type": {"type": "string"}, "ownerId": {"type": "integer"},
    "name": {"type": "string"}, "from": {"type": "string"}, "to": {"type": "string"},
    "description": {"type": "string"}, "section": {"type": "integer"},
    "attendees": {"type": "array", "items": {"type": "integer"}},
})
async def event_add(client, type="user", ownerId=0, **kwargs):
    return await client.call("calendar.event.add", {"type": type, "ownerId": ownerId, **kwargs})

@registry.tool("calendar_event_update", "Обновить событие", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def event_update(client, id, fields):
    return await client.call("calendar.event.update", {"id": id, **fields})

@registry.tool("calendar_event_delete", "Удалить событие", MODULE, {"id": {"type": "integer"}})
async def event_delete(client, id):
    return await client.call("calendar.event.delete", {"id": id})


# === СЕКЦИИ (ПОДКАЛЕНДАРИ) ===
@registry.tool("calendar_section_list", "Список секций календаря", MODULE, {
    "type": {"type": "string"}, "ownerId": {"type": "integer"},
})
async def section_list(client, type="user", ownerId=0):
    return await client.call("calendar.section.get", {"type": type, "ownerId": ownerId})

@registry.tool("calendar_section_add", "Создать секцию", MODULE, {
    "type": {"type": "string"}, "ownerId": {"type": "integer"}, "name": {"type": "string"}, "color": {"type": "string"},
})
async def section_add(client, type="user", ownerId=0, name="", color=""):
    return await client.call("calendar.section.add", {"type": type, "ownerId": ownerId, "name": name, "color": color})

@registry.tool("calendar_section_update", "Обновить секцию", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def section_update(client, id, fields):
    return await client.call("calendar.section.update", {"id": id, **fields})

@registry.tool("calendar_section_delete", "Удалить секцию", MODULE, {"id": {"type": "integer"}})
async def section_delete(client, id):
    return await client.call("calendar.section.delete", {"id": id})


# === ДОСТУПНОСТЬ ===
@registry.tool("calendar_accessibility_get", "Занятость пользователей", MODULE, {
    "users": {"type": "array", "items": {"type": "integer"}},
    "from": {"type": "string"}, "to": {"type": "string"},
})
async def accessibility_get(client, users, **kwargs):
    return await client.call("calendar.accessibility.get", {"users": users, **kwargs})

@registry.tool("calendar_meeting_status_set", "Принять/отклонить встречу", MODULE, {
    "eventId": {"type": "integer"}, "status": {"type": "string", "description": "Y|N|Q (принять/отклонить/может быть)"},
})
async def meeting_status_set(client, eventId, status):
    return await client.call("calendar.meeting.status.set", {"eventId": eventId, "status": status})

@registry.tool("calendar_settings_get", "Настройки календаря пользователя", MODULE, {})
async def settings_get(client):
    return await client.call("calendar.settings.get")

@registry.tool("calendar_resource_list", "Список ресурсов (переговорки)", MODULE, {})
async def resource_list(client):
    return await client.call("calendar.resource.list")
