"""CRM модуль — лиды, сделки, контакты, компании, счета, товары, воронки, smart-процессы."""

from src.core.registry import registry

MODULE = "crm"


# === ЛИДЫ ===
@registry.tool("crm_lead_list", "Список лидов с фильтрами и пагинацией", MODULE, {
    "filter": {"type": "object", "description": "Фильтры (STATUS_ID, SOURCE_ID, ASSIGNED_BY_ID и т.д.)"},
    "select": {"type": "array", "items": {"type": "string"}, "description": "Поля для выборки"},
    "order": {"type": "object", "description": "Сортировка {field: ASC|DESC}"},
    "start": {"type": "integer", "description": "Смещение для пагинации"},
})
async def lead_list(client, filter=None, select=None, order=None, start=0):
    return await client.call("crm.lead.list", {"filter": filter or {}, "select": select or [], "order": order or {}, "start": start})

@registry.tool("crm_lead_get", "Получить лид по ID", MODULE, {"id": {"type": "integer", "description": "ID лида"}})
async def lead_get(client, id):
    return await client.call("crm.lead.get", {"ID": id})

@registry.tool("crm_lead_add", "Создать лид", MODULE, {"fields": {"type": "object", "description": "Поля лида (TITLE, NAME, PHONE и т.д.)"}})
async def lead_add(client, fields):
    return await client.call("crm.lead.add", {"fields": fields})

@registry.tool("crm_lead_update", "Обновить лид", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def lead_update(client, id, fields):
    return await client.call("crm.lead.update", {"ID": id, "fields": fields})

@registry.tool("crm_lead_delete", "Удалить лид", MODULE, {"id": {"type": "integer"}})
async def lead_delete(client, id):
    return await client.call("crm.lead.delete", {"ID": id})

@registry.tool("crm_lead_fields", "Получить описание полей лида", MODULE, {})
async def lead_fields(client):
    return await client.call("crm.lead.fields")

@registry.tool("crm_lead_productrows_set", "Установить товары лида", MODULE, {"id": {"type": "integer"}, "rows": {"type": "array"}})
async def lead_productrows_set(client, id, rows):
    return await client.call("crm.lead.productrows.set", {"ID": id, "rows": rows})


# === СДЕЛКИ ===
@registry.tool("crm_deal_list", "Список сделок с фильтрами", MODULE, {
    "filter": {"type": "object"}, "select": {"type": "array"}, "order": {"type": "object"}, "start": {"type": "integer"},
})
async def deal_list(client, filter=None, select=None, order=None, start=0):
    return await client.call("crm.deal.list", {"filter": filter or {}, "select": select or [], "order": order or {}, "start": start})

@registry.tool("crm_deal_get", "Получить сделку по ID", MODULE, {"id": {"type": "integer"}})
async def deal_get(client, id):
    return await client.call("crm.deal.get", {"ID": id})

@registry.tool("crm_deal_add", "Создать сделку", MODULE, {"fields": {"type": "object"}})
async def deal_add(client, fields):
    return await client.call("crm.deal.add", {"fields": fields})

@registry.tool("crm_deal_update", "Обновить сделку", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def deal_update(client, id, fields):
    return await client.call("crm.deal.update", {"ID": id, "fields": fields})

@registry.tool("crm_deal_delete", "Удалить сделку", MODULE, {"id": {"type": "integer"}})
async def deal_delete(client, id):
    return await client.call("crm.deal.delete", {"ID": id})

@registry.tool("crm_deal_fields", "Описание полей сделки", MODULE, {})
async def deal_fields(client):
    return await client.call("crm.deal.fields")

@registry.tool("crm_deal_productrows_get", "Товары сделки", MODULE, {"id": {"type": "integer"}})
async def deal_productrows_get(client, id):
    return await client.call("crm.deal.productrows.get", {"ID": id})

@registry.tool("crm_deal_productrows_set", "Установить товары сделки", MODULE, {"id": {"type": "integer"}, "rows": {"type": "array"}})
async def deal_productrows_set(client, id, rows):
    return await client.call("crm.deal.productrows.set", {"ID": id, "rows": rows})


# === КОНТАКТЫ ===
@registry.tool("crm_contact_list", "Список контактов", MODULE, {"filter": {"type": "object"}, "select": {"type": "array"}, "order": {"type": "object"}, "start": {"type": "integer"}})
async def contact_list(client, filter=None, select=None, order=None, start=0):
    return await client.call("crm.contact.list", {"filter": filter or {}, "select": select or [], "order": order or {}, "start": start})

@registry.tool("crm_contact_get", "Получить контакт по ID", MODULE, {"id": {"type": "integer"}})
async def contact_get(client, id):
    return await client.call("crm.contact.get", {"ID": id})

@registry.tool("crm_contact_add", "Создать контакт", MODULE, {"fields": {"type": "object"}})
async def contact_add(client, fields):
    return await client.call("crm.contact.add", {"fields": fields})

@registry.tool("crm_contact_update", "Обновить контакт", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def contact_update(client, id, fields):
    return await client.call("crm.contact.update", {"ID": id, "fields": fields})

@registry.tool("crm_contact_delete", "Удалить контакт", MODULE, {"id": {"type": "integer"}})
async def contact_delete(client, id):
    return await client.call("crm.contact.delete", {"ID": id})

@registry.tool("crm_contact_fields", "Описание полей контакта", MODULE, {})
async def contact_fields(client):
    return await client.call("crm.contact.fields")


# === КОМПАНИИ ===
@registry.tool("crm_company_list", "Список компаний", MODULE, {"filter": {"type": "object"}, "select": {"type": "array"}, "order": {"type": "object"}, "start": {"type": "integer"}})
async def company_list(client, filter=None, select=None, order=None, start=0):
    return await client.call("crm.company.list", {"filter": filter or {}, "select": select or [], "order": order or {}, "start": start})

@registry.tool("crm_company_get", "Получить компанию", MODULE, {"id": {"type": "integer"}})
async def company_get(client, id):
    return await client.call("crm.company.get", {"ID": id})

@registry.tool("crm_company_add", "Создать компанию", MODULE, {"fields": {"type": "object"}})
async def company_add(client, fields):
    return await client.call("crm.company.add", {"fields": fields})

@registry.tool("crm_company_update", "Обновить компанию", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def company_update(client, id, fields):
    return await client.call("crm.company.update", {"ID": id, "fields": fields})

@registry.tool("crm_company_delete", "Удалить компанию", MODULE, {"id": {"type": "integer"}})
async def company_delete(client, id):
    return await client.call("crm.company.delete", {"ID": id})

@registry.tool("crm_company_fields", "Описание полей компании", MODULE, {})
async def company_fields(client):
    return await client.call("crm.company.fields")


# === СЧЕТА ===
@registry.tool("crm_invoice_list", "Список счетов", MODULE, {"filter": {"type": "object"}, "select": {"type": "array"}, "start": {"type": "integer"}})
async def invoice_list(client, filter=None, select=None, start=0):
    return await client.call("crm.invoice.list", {"filter": filter or {}, "select": select or [], "start": start})

@registry.tool("crm_invoice_get", "Получить счёт", MODULE, {"id": {"type": "integer"}})
async def invoice_get(client, id):
    return await client.call("crm.invoice.get", {"ID": id})

@registry.tool("crm_invoice_add", "Создать счёт", MODULE, {"fields": {"type": "object"}})
async def invoice_add(client, fields):
    return await client.call("crm.invoice.add", {"fields": fields})

@registry.tool("crm_invoice_delete", "Удалить счёт", MODULE, {"id": {"type": "integer"}})
async def invoice_delete(client, id):
    return await client.call("crm.invoice.delete", {"ID": id})


# === ТОВАРЫ ===
@registry.tool("crm_product_list", "Список товаров", MODULE, {"filter": {"type": "object"}, "select": {"type": "array"}, "start": {"type": "integer"}})
async def product_list(client, filter=None, select=None, start=0):
    return await client.call("crm.product.list", {"filter": filter or {}, "select": select or [], "start": start})

@registry.tool("crm_product_get", "Получить товар", MODULE, {"id": {"type": "integer"}})
async def product_get(client, id):
    return await client.call("crm.product.get", {"ID": id})

@registry.tool("crm_product_add", "Создать товар", MODULE, {"fields": {"type": "object"}})
async def product_add(client, fields):
    return await client.call("crm.product.add", {"fields": fields})

@registry.tool("crm_product_update", "Обновить товар", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def product_update(client, id, fields):
    return await client.call("crm.product.update", {"ID": id, "fields": fields})

@registry.tool("crm_product_delete", "Удалить товар", MODULE, {"id": {"type": "integer"}})
async def product_delete(client, id):
    return await client.call("crm.product.delete", {"ID": id})


# === ВОРОНКИ / СТАДИИ ===
@registry.tool("crm_dealcategory_list", "Список воронок сделок", MODULE, {})
async def dealcategory_list(client):
    return await client.call("crm.dealcategory.list")

@registry.tool("crm_dealcategory_stage_list", "Стадии воронки", MODULE, {"id": {"type": "integer", "description": "ID воронки (0 = дефолтная)"}})
async def dealcategory_stage_list(client, id=0):
    return await client.call("crm.dealcategory.stage.list", {"ID": id})

@registry.tool("crm_status_list", "Справочник статусов CRM", MODULE, {})
async def status_list(client):
    return await client.call("crm.status.list")

@registry.tool("crm_lead_status_list", "Статусы лидов", MODULE, {})
async def lead_status_list(client):
    return await client.call("crm.status.list", {"filter": {"ENTITY_ID": "STATUS"}})


# === АКТИВИТИ / ДЕЛА ===
@registry.tool("crm_activity_list", "Список дел (звонки, письма, встречи)", MODULE, {
    "filter": {"type": "object"}, "select": {"type": "array"}, "start": {"type": "integer"},
})
async def activity_list(client, filter=None, select=None, start=0):
    return await client.call("crm.activity.list", {"filter": filter or {}, "select": select or [], "start": start})

@registry.tool("crm_activity_get", "Получить дело", MODULE, {"id": {"type": "integer"}})
async def activity_get(client, id):
    return await client.call("crm.activity.get", {"ID": id})

@registry.tool("crm_activity_add", "Создать дело", MODULE, {"fields": {"type": "object"}})
async def activity_add(client, fields):
    return await client.call("crm.activity.add", {"fields": fields})

@registry.tool("crm_activity_update", "Обновить дело", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def activity_update(client, id, fields):
    return await client.call("crm.activity.update", {"ID": id, "fields": fields})

@registry.tool("crm_activity_delete", "Удалить дело", MODULE, {"id": {"type": "integer"}})
async def activity_delete(client, id):
    return await client.call("crm.activity.delete", {"ID": id})


# === TIMELINE ===
@registry.tool("crm_timeline_comment_add", "Добавить комментарий в таймлайн", MODULE, {
    "entity_type": {"type": "string", "description": "lead|deal|contact|company"},
    "entity_id": {"type": "integer"},
    "comment": {"type": "string"},
})
async def timeline_comment_add(client, entity_type, entity_id, comment):
    fields = {"ENTITY_ID": entity_id, "ENTITY_TYPE": entity_type, "COMMENT": comment}
    return await client.call("crm.timeline.comment.add", {"fields": fields})


# === SMART-ПРОЦЕССЫ ===
@registry.tool("crm_type_list", "Список smart-процессов", MODULE, {})
async def type_list(client):
    return await client.call("crm.type.list")

@registry.tool("crm_item_list", "Элементы smart-процесса", MODULE, {"entityTypeId": {"type": "integer"}, "filter": {"type": "object"}, "select": {"type": "array"}})
async def item_list(client, entityTypeId, filter=None, select=None):
    return await client.call("crm.item.list", {"entityTypeId": entityTypeId, "filter": filter or {}, "select": select or []})

@registry.tool("crm_item_add", "Создать элемент smart-процесса", MODULE, {"entityTypeId": {"type": "integer"}, "fields": {"type": "object"}})
async def item_add(client, entityTypeId, fields):
    return await client.call("crm.item.add", {"entityTypeId": entityTypeId, "fields": fields})

@registry.tool("crm_item_update", "Обновить элемент smart-процесса", MODULE, {"entityTypeId": {"type": "integer"}, "id": {"type": "integer"}, "fields": {"type": "object"}})
async def item_update(client, entityTypeId, id, fields):
    return await client.call("crm.item.update", {"entityTypeId": entityTypeId, "ID": id, "fields": fields})

@registry.tool("crm_item_delete", "Удалить элемент smart-процесса", MODULE, {"entityTypeId": {"type": "integer"}, "id": {"type": "integer"}})
async def item_delete(client, entityTypeId, id):
    return await client.call("crm.item.delete", {"entityTypeId": entityTypeId, "ID": id})
