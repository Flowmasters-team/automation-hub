"""Модуль бизнес-процессов Bitrix24."""

from src.core.registry import registry

MODULE = "bizproc"


# === ШАБЛОНЫ ===
@registry.tool("bizproc_workflow_template_list", "Список шаблонов БП", MODULE, {
    "filter": {"type": "object"}, "select": {"type": "array"},
})
async def template_list(client, filter=None, select=None):
    return await client.call("bizproc.workflow.template.list", {"filter": filter or {}, "select": select or []})

@registry.tool("bizproc_workflow_template_add", "Создать шаблон БП", MODULE, {"fields": {"type": "object"}})
async def template_add(client, fields):
    return await client.call("bizproc.workflow.template.add", fields)

@registry.tool("bizproc_workflow_template_update", "Обновить шаблон БП", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def template_update(client, id, fields):
    return await client.call("bizproc.workflow.template.update", {"ID": id, **fields})

@registry.tool("bizproc_workflow_template_delete", "Удалить шаблон БП", MODULE, {"id": {"type": "integer"}})
async def template_delete(client, id):
    return await client.call("bizproc.workflow.template.delete", {"ID": id})


# === ЭКЗЕМПЛЯРЫ (ЗАПУСК / ОСТАНОВКА) ===
@registry.tool("bizproc_workflow_start", "Запустить бизнес-процесс", MODULE, {
    "templateId": {"type": "integer"},
    "documentId": {"type": "array", "description": "['module', 'entity', 'ID']"},
    "parameters": {"type": "object"},
})
async def workflow_start(client, templateId, documentId, parameters=None):
    return await client.call("bizproc.workflow.start", {
        "TEMPLATE_ID": templateId,
        "DOCUMENT_ID": documentId,
        "PARAMETERS": parameters or {},
    })

@registry.tool("bizproc_workflow_terminate", "Остановить бизнес-процесс", MODULE, {
    "id": {"type": "string", "description": "ID экземпляра БП"}, "status": {"type": "string"},
})
async def workflow_terminate(client, id, status="Terminated"):
    return await client.call("bizproc.workflow.terminate", {"ID": id, "STATUS": status})

@registry.tool("bizproc_workflow_instances", "Список запущенных БП", MODULE, {
    "filter": {"type": "object"}, "select": {"type": "array"},
})
async def workflow_instances(client, filter=None, select=None):
    return await client.call("bizproc.workflow.instances", {"filter": filter or {}, "select": select or []})

@registry.tool("bizproc_workflow_kill", "Принудительно удалить экземпляр БП", MODULE, {"id": {"type": "string"}})
async def workflow_kill(client, id):
    return await client.call("bizproc.workflow.kill", {"ID": id})


# === ЗАДАНИЯ БП ===
@registry.tool("bizproc_task_list", "Список заданий БП", MODULE, {
    "filter": {"type": "object"}, "select": {"type": "array"},
})
async def task_list(client, filter=None, select=None):
    return await client.call("bizproc.task.list", {"filter": filter or {}, "select": select or []})

@registry.tool("bizproc_task_complete", "Выполнить задание БП", MODULE, {
    "taskId": {"type": "integer"}, "status": {"type": "integer", "description": "1=approve, 2=reject, 3=cancel, 4=timeout"},
    "comment": {"type": "string"},
})
async def task_complete(client, taskId, status, comment=""):
    return await client.call("bizproc.task.complete", {"TASK_ID": taskId, "STATUS": status, "COMMENT": comment})


# === РОБОТЫ ===
@registry.tool("bizproc_robot_list", "Список зарегистрированных роботов", MODULE, {})
async def robot_list(client):
    return await client.call("bizproc.robot.list")

@registry.tool("bizproc_robot_add", "Зарегистрировать робота", MODULE, {"fields": {"type": "object"}})
async def robot_add(client, fields):
    return await client.call("bizproc.robot.add", fields)

@registry.tool("bizproc_robot_update", "Обновить робота", MODULE, {"code": {"type": "string"}, "fields": {"type": "object"}})
async def robot_update(client, code, fields):
    return await client.call("bizproc.robot.update", {"CODE": code, **fields})

@registry.tool("bizproc_robot_delete", "Удалить робота", MODULE, {"code": {"type": "string"}})
async def robot_delete(client, code):
    return await client.call("bizproc.robot.delete", {"CODE": code})


# === ТРИГГЕРЫ ===
@registry.tool("bizproc_trigger_list", "Список триггеров", MODULE, {"filter": {"type": "object"}})
async def trigger_list(client, filter=None):
    return await client.call("bizproc.automation.trigger.list", filter or {})

@registry.tool("bizproc_trigger_add", "Добавить триггер", MODULE, {"fields": {"type": "object"}})
async def trigger_add(client, fields):
    return await client.call("bizproc.automation.trigger.add", fields)

@registry.tool("bizproc_trigger_delete", "Удалить триггер", MODULE, {"id": {"type": "integer"}})
async def trigger_delete(client, id):
    return await client.call("bizproc.automation.trigger.delete", {"ID": id})
