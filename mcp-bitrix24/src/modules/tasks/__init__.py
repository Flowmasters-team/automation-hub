"""Модуль задач и проектов Bitrix24."""

from src.core.registry import registry

MODULE = "tasks"


# === ЗАДАЧИ ===
@registry.tool("task_list", "Список задач с фильтрами", MODULE, {
    "filter": {"type": "object"}, "select": {"type": "array"}, "order": {"type": "object"}, "start": {"type": "integer"},
})
async def task_list(client, filter=None, select=None, order=None, start=0):
    return await client.call("tasks.task.list", {"filter": filter or {}, "select": select or [], "order": order or {}, "start": start})

@registry.tool("task_get", "Получить задачу", MODULE, {"id": {"type": "integer"}, "select": {"type": "array"}})
async def task_get(client, id, select=None):
    return await client.call("tasks.task.get", {"taskId": id, "select": select or []})

@registry.tool("task_add", "Создать задачу", MODULE, {"fields": {"type": "object", "description": "TITLE, RESPONSIBLE_ID, DESCRIPTION, DEADLINE и т.д."}})
async def task_add(client, fields):
    return await client.call("tasks.task.add", {"fields": fields})

@registry.tool("task_update", "Обновить задачу", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def task_update(client, id, fields):
    return await client.call("tasks.task.update", {"taskId": id, "fields": fields})

@registry.tool("task_delete", "Удалить задачу", MODULE, {"id": {"type": "integer"}})
async def task_delete(client, id):
    return await client.call("tasks.task.delete", {"taskId": id})

@registry.tool("task_complete", "Завершить задачу", MODULE, {"id": {"type": "integer"}})
async def task_complete(client, id):
    return await client.call("tasks.task.complete", {"taskId": id})

@registry.tool("task_renew", "Возобновить задачу", MODULE, {"id": {"type": "integer"}})
async def task_renew(client, id):
    return await client.call("tasks.task.renew", {"taskId": id})

@registry.tool("task_delegate", "Делегировать задачу", MODULE, {"id": {"type": "integer"}, "userId": {"type": "integer"}})
async def task_delegate(client, id, userId):
    return await client.call("tasks.task.delegate", {"taskId": id, "userId": userId})

@registry.tool("task_start", "Начать выполнение задачи", MODULE, {"id": {"type": "integer"}})
async def task_start(client, id):
    return await client.call("tasks.task.start", {"taskId": id})

@registry.tool("task_pause", "Поставить задачу на паузу", MODULE, {"id": {"type": "integer"}})
async def task_pause(client, id):
    return await client.call("tasks.task.pause", {"taskId": id})

@registry.tool("task_defer", "Отложить задачу", MODULE, {"id": {"type": "integer"}})
async def task_defer(client, id):
    return await client.call("tasks.task.defer", {"taskId": id})

@registry.tool("task_approve", "Принять задачу", MODULE, {"id": {"type": "integer"}})
async def task_approve(client, id):
    return await client.call("tasks.task.approve", {"taskId": id})

@registry.tool("task_disapprove", "Отклонить задачу", MODULE, {"id": {"type": "integer"}})
async def task_disapprove(client, id):
    return await client.call("tasks.task.disapprove", {"taskId": id})

@registry.tool("task_fields", "Описание полей задач", MODULE, {})
async def task_fields(client):
    return await client.call("tasks.task.getFields")


# === КОММЕНТАРИИ К ЗАДАЧАМ ===
@registry.tool("task_comment_list", "Комментарии задачи", MODULE, {"taskId": {"type": "integer"}})
async def comment_list(client, taskId):
    return await client.call("task.commentitem.getlist", {"TASKID": taskId})

@registry.tool("task_comment_add", "Добавить комментарий к задаче", MODULE, {"taskId": {"type": "integer"}, "text": {"type": "string"}})
async def comment_add(client, taskId, text):
    return await client.call("task.commentitem.add", {"TASKID": taskId, "FIELDS": {"POST_MESSAGE": text}})

@registry.tool("task_comment_update", "Обновить комментарий", MODULE, {"taskId": {"type": "integer"}, "commentId": {"type": "integer"}, "text": {"type": "string"}})
async def comment_update(client, taskId, commentId, text):
    return await client.call("task.commentitem.update", {"TASKID": taskId, "ITEMID": commentId, "FIELDS": {"POST_MESSAGE": text}})

@registry.tool("task_comment_delete", "Удалить комментарий", MODULE, {"taskId": {"type": "integer"}, "commentId": {"type": "integer"}})
async def comment_delete(client, taskId, commentId):
    return await client.call("task.commentitem.delete", {"TASKID": taskId, "ITEMID": commentId})


# === ЧЕКЛИСТЫ ===
@registry.tool("task_checklist_list", "Чеклист задачи", MODULE, {"taskId": {"type": "integer"}})
async def checklist_list(client, taskId):
    return await client.call("task.checklistitem.getlist", {"TASKID": taskId})

@registry.tool("task_checklist_add", "Добавить пункт чеклиста", MODULE, {"taskId": {"type": "integer"}, "title": {"type": "string"}})
async def checklist_add(client, taskId, title):
    return await client.call("task.checklistitem.add", {"TASKID": taskId, "FIELDS": {"TITLE": title}})

@registry.tool("task_checklist_complete", "Отметить пункт выполненным", MODULE, {"taskId": {"type": "integer"}, "itemId": {"type": "integer"}})
async def checklist_complete(client, taskId, itemId):
    return await client.call("task.checklistitem.complete", {"TASKID": taskId, "ITEMID": itemId})

@registry.tool("task_checklist_delete", "Удалить пункт чеклиста", MODULE, {"taskId": {"type": "integer"}, "itemId": {"type": "integer"}})
async def checklist_delete(client, taskId, itemId):
    return await client.call("task.checklistitem.delete", {"TASKID": taskId, "ITEMID": itemId})


# === ВРЕМЯ ===
@registry.tool("task_elapsed_list", "Затраченное время по задаче", MODULE, {"taskId": {"type": "integer"}})
async def elapsed_list(client, taskId):
    return await client.call("task.elapseditem.getlist", {"TASKID": taskId})

@registry.tool("task_elapsed_add", "Добавить запись времени", MODULE, {"taskId": {"type": "integer"}, "seconds": {"type": "integer"}, "comment": {"type": "string"}})
async def elapsed_add(client, taskId, seconds, comment=""):
    return await client.call("task.elapseditem.add", {"TASKID": taskId, "FIELDS": {"SECONDS": seconds, "COMMENT_TEXT": comment}})


# === ПРОЕКТЫ (ГРУППЫ) ===
@registry.tool("sonet_group_list", "Список проектов/групп", MODULE, {"filter": {"type": "object"}, "select": {"type": "array"}})
async def group_list(client, filter=None, select=None):
    return await client.call("sonet_group.get", {"FILTER": filter or {}, "SELECT": select or []})

@registry.tool("sonet_group_create", "Создать проект/группу", MODULE, {"fields": {"type": "object"}})
async def group_create(client, fields):
    return await client.call("sonet_group.create", fields)

@registry.tool("sonet_group_update", "Обновить проект/группу", MODULE, {"groupId": {"type": "integer"}, "fields": {"type": "object"}})
async def group_update(client, groupId, fields):
    return await client.call("sonet_group.update", {"GROUP_ID": groupId, **fields})

@registry.tool("sonet_group_delete", "Удалить проект/группу", MODULE, {"groupId": {"type": "integer"}})
async def group_delete(client, groupId):
    return await client.call("sonet_group.delete", {"GROUP_ID": groupId})


# === КАНБАН ===
@registry.tool("task_stages_get", "Стадии канбана проекта", MODULE, {"entityId": {"type": "integer"}})
async def stages_get(client, entityId):
    return await client.call("task.stages.get", {"entityId": entityId})

@registry.tool("task_stages_add", "Добавить стадию канбана", MODULE, {"fields": {"type": "object"}})
async def stages_add(client, fields):
    return await client.call("task.stages.add", {"fields": fields})

@registry.tool("task_stages_update", "Обновить стадию канбана", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def stages_update(client, id, fields):
    return await client.call("task.stages.update", {"id": id, "fields": fields})

@registry.tool("task_stages_delete", "Удалить стадию канбана", MODULE, {"id": {"type": "integer"}})
async def stages_delete(client, id):
    return await client.call("task.stages.delete", {"id": id})

@registry.tool("task_stages_move", "Переместить задачу на стадию", MODULE, {"id": {"type": "integer"}, "stageId": {"type": "integer"}})
async def stages_move(client, id, stageId):
    return await client.call("task.stages.movetask", {"id": id, "stageId": stageId})
