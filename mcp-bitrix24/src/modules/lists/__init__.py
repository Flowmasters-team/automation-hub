"""Модуль универсальных списков Bitrix24."""

from src.core.registry import registry

MODULE = "lists"


# === СПИСКИ ===
@registry.tool("lists_get", "Список универсальных списков", MODULE, {"iblockTypeId": {"type": "string", "description": "lists|bitrix_processes|crm_lists"}})
async def lists_get(client, iblockTypeId="lists"):
    return await client.call("lists.get", {"IBLOCK_TYPE_ID": iblockTypeId})

@registry.tool("lists_add", "Создать список", MODULE, {
    "iblockTypeId": {"type": "string"}, "name": {"type": "string"}, "description": {"type": "string"},
})
async def lists_add(client, iblockTypeId="lists", name="", description=""):
    return await client.call("lists.add", {"IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_CODE": name.lower().replace(" ", "_"), "FIELDS": {"NAME": name, "DESCRIPTION": description}})

@registry.tool("lists_update", "Обновить список", MODULE, {"iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}, "fields": {"type": "object"}})
async def lists_update(client, iblockTypeId, iblockId, fields):
    return await client.call("lists.update", {"IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId, "FIELDS": fields})

@registry.tool("lists_delete", "Удалить список", MODULE, {"iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}})
async def lists_delete(client, iblockTypeId, iblockId):
    return await client.call("lists.delete", {"IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId})


# === ПОЛЯ СПИСКА ===
@registry.tool("lists_field_list", "Поля списка", MODULE, {"iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}})
async def field_list(client, iblockTypeId, iblockId):
    return await client.call("lists.field.get", {"IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId})

@registry.tool("lists_field_add", "Добавить поле в список", MODULE, {
    "iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}, "fields": {"type": "object"},
})
async def field_add(client, iblockTypeId, iblockId, fields):
    return await client.call("lists.field.add", {"IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId, "FIELDS": fields})

@registry.tool("lists_field_update", "Обновить поле списка", MODULE, {
    "iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}, "fieldId": {"type": "string"}, "fields": {"type": "object"},
})
async def field_update(client, iblockTypeId, iblockId, fieldId, fields):
    return await client.call("lists.field.update", {"IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId, "FIELD_ID": fieldId, "FIELDS": fields})

@registry.tool("lists_field_delete", "Удалить поле списка", MODULE, {
    "iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}, "fieldId": {"type": "string"},
})
async def field_delete(client, iblockTypeId, iblockId, fieldId):
    return await client.call("lists.field.delete", {"IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId, "FIELD_ID": fieldId})


# === ЭЛЕМЕНТЫ СПИСКА ===
@registry.tool("lists_element_list", "Элементы списка", MODULE, {
    "iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"},
    "filter": {"type": "object"}, "select": {"type": "array"}, "start": {"type": "integer"},
})
async def element_list(client, iblockTypeId, iblockId, filter=None, select=None, start=0):
    return await client.call("lists.element.get", {
        "IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId,
        "FILTER": filter or {}, "SELECT": select or [], "start": start,
    })

@registry.tool("lists_element_add", "Добавить элемент списка", MODULE, {
    "iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}, "elementCode": {"type": "string"}, "fields": {"type": "object"},
})
async def element_add(client, iblockTypeId, iblockId, elementCode, fields):
    return await client.call("lists.element.add", {
        "IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId, "ELEMENT_CODE": elementCode, "FIELDS": fields,
    })

@registry.tool("lists_element_update", "Обновить элемент списка", MODULE, {
    "iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}, "elementId": {"type": "integer"}, "fields": {"type": "object"},
})
async def element_update(client, iblockTypeId, iblockId, elementId, fields):
    return await client.call("lists.element.update", {
        "IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId, "ELEMENT_ID": elementId, "FIELDS": fields,
    })

@registry.tool("lists_element_delete", "Удалить элемент списка", MODULE, {
    "iblockTypeId": {"type": "string"}, "iblockId": {"type": "integer"}, "elementId": {"type": "integer"},
})
async def element_delete(client, iblockTypeId, iblockId, elementId):
    return await client.call("lists.element.delete", {
        "IBLOCK_TYPE_ID": iblockTypeId, "IBLOCK_ID": iblockId, "ELEMENT_ID": elementId,
    })
