"""Модуль телефонии Bitrix24."""

from src.core.registry import registry

MODULE = "telephony"


# === ЗВОНКИ ===
@registry.tool("telephony_call_register", "Зарегистрировать звонок", MODULE, {
    "userId": {"type": "integer"}, "phoneNumber": {"type": "string"},
    "type": {"type": "integer", "description": "1=исходящий, 2=входящий, 3=входящий+перенаправление, 4=обратный"},
    "callStartDate": {"type": "string"},
})
async def call_register(client, userId, phoneNumber, type=2, callStartDate=""):
    params = {"USER_ID": userId, "PHONE_NUMBER": phoneNumber, "TYPE": type}
    if callStartDate:
        params["CALL_START_DATE"] = callStartDate
    return await client.call("telephony.externalcall.register", params)

@registry.tool("telephony_call_finish", "Завершить звонок", MODULE, {
    "callId": {"type": "string"}, "userId": {"type": "integer"},
    "duration": {"type": "integer"}, "statusCode": {"type": "string", "description": "200=успешный, 304=пропущенный, 603=отклонён"},
})
async def call_finish(client, callId, userId, duration, statusCode="200"):
    return await client.call("telephony.externalcall.finish", {
        "CALL_ID": callId, "USER_ID": userId, "DURATION": duration, "STATUS_CODE": statusCode,
    })

@registry.tool("telephony_call_attach_record", "Прикрепить запись к звонку", MODULE, {
    "callId": {"type": "string"}, "filename": {"type": "string"}, "fileContent": {"type": "string", "description": "Base64"},
})
async def call_attach_record(client, callId, filename, fileContent):
    return await client.call("telephony.externalCall.attachRecord", {
        "CALL_ID": callId, "FILENAME": filename, "FILE_CONTENT": fileContent,
    })

@registry.tool("telephony_call_show", "Показать карточку звонка", MODULE, {
    "callId": {"type": "string"}, "userId": {"type": "array", "items": {"type": "integer"}},
})
async def call_show(client, callId, userId):
    return await client.call("telephony.externalcall.show", {"CALL_ID": callId, "USER_ID": userId})

@registry.tool("telephony_call_hide", "Скрыть карточку звонка", MODULE, {
    "callId": {"type": "string"}, "userId": {"type": "array"},
})
async def call_hide(client, callId, userId):
    return await client.call("telephony.externalcall.hide", {"CALL_ID": callId, "USER_ID": userId})


# === СТАТИСТИКА ===
@registry.tool("voximplant_statistic_get", "Статистика звонков", MODULE, {
    "filter": {"type": "object"}, "sort": {"type": "string"}, "order": {"type": "string"},
})
async def statistic_get(client, filter=None, sort="ID", order="DESC"):
    return await client.call("voximplant.statistic.get", {"FILTER": filter or {}, "SORT": sort, "ORDER": order})


# === SIP-ЛИНИИ ===
@registry.tool("voximplant_sip_list", "Список SIP-линий", MODULE, {})
async def sip_list(client):
    return await client.call("voximplant.sip.get")

@registry.tool("voximplant_sip_add", "Создать SIP-линию", MODULE, {"fields": {"type": "object"}})
async def sip_add(client, fields):
    return await client.call("voximplant.sip.add", fields)

@registry.tool("voximplant_sip_update", "Обновить SIP-линию", MODULE, {"fields": {"type": "object"}})
async def sip_update(client, fields):
    return await client.call("voximplant.sip.update", fields)

@registry.tool("voximplant_sip_delete", "Удалить SIP-линию", MODULE, {"regId": {"type": "integer"}})
async def sip_delete(client, regId):
    return await client.call("voximplant.sip.delete", {"REG_ID": regId})

@registry.tool("voximplant_sip_status", "Статус SIP-регистрации", MODULE, {"regId": {"type": "integer"}})
async def sip_status(client, regId):
    return await client.call("voximplant.sip.status", {"REG_ID": regId})


# === НОМЕРА ===
@registry.tool("voximplant_line_list", "Список телефонных линий", MODULE, {})
async def line_list(client):
    return await client.call("voximplant.line.get")

@registry.tool("voximplant_line_outgoing_set", "Установить исходящую линию", MODULE, {
    "lineId": {"type": "string"}, "userId": {"type": "integer"},
})
async def line_outgoing_set(client, lineId, userId):
    return await client.call("voximplant.line.outgoing.set", {"LINE_ID": lineId, "USER_ID": userId})
