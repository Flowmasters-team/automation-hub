"""Модуль оргструктуры Bitrix24 — пользователи, отделы."""

from src.core.registry import registry

MODULE = "orgstructure"


# === ПОЛЬЗОВАТЕЛИ ===
@registry.tool("user_get", "Список пользователей с фильтрами", MODULE, {
    "filter": {"type": "object", "description": "UF_DEPARTMENT, ACTIVE и т.д."},
    "select": {"type": "array"}, "start": {"type": "integer"},
})
async def user_get(client, filter=None, select=None, start=0):
    params = {}
    if filter:
        params["FILTER"] = filter
    if select:
        params["SELECT"] = select
    if start:
        params["start"] = start
    return await client.call("user.get", params)

@registry.tool("user_current", "Текущий пользователь", MODULE, {})
async def user_current(client):
    return await client.call("user.current")

@registry.tool("user_search", "Поиск пользователей", MODULE, {"query": {"type": "string"}})
async def user_search(client, query):
    return await client.call("user.search", {"FIND": query})

@registry.tool("user_add", "Создать пользователя", MODULE, {"fields": {"type": "object"}})
async def user_add(client, fields):
    return await client.call("user.add", fields)

@registry.tool("user_update", "Обновить пользователя", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def user_update(client, id, fields):
    return await client.call("user.update", {"ID": id, **fields})


# === ОТДЕЛЫ ===
@registry.tool("department_list", "Список отделов", MODULE, {
    "parent": {"type": "integer", "description": "ID родительского отдела (0 = корень)"},
    "sort": {"type": "string"}, "order": {"type": "string"},
})
async def department_list(client, parent=None, sort="SORT", order="ASC"):
    params = {"sort": sort, "order": order}
    if parent is not None:
        params["PARENT"] = parent
    return await client.call("department.get", params)

@registry.tool("department_add", "Создать отдел", MODULE, {
    "name": {"type": "string"}, "parent": {"type": "integer"}, "head": {"type": "integer", "description": "ID руководителя"},
})
async def department_add(client, name, parent=0, head=None):
    params = {"NAME": name, "PARENT": parent}
    if head:
        params["UF_HEAD"] = head
    return await client.call("department.add", params)

@registry.tool("department_update", "Обновить отдел", MODULE, {"id": {"type": "integer"}, "fields": {"type": "object"}})
async def department_update(client, id, fields):
    return await client.call("department.update", {"ID": id, **fields})

@registry.tool("department_delete", "Удалить отдел", MODULE, {"id": {"type": "integer"}})
async def department_delete(client, id):
    return await client.call("department.delete", {"ID": id})

@registry.tool("department_tree", "Дерево отделов от корня", MODULE, {})
async def department_tree(client):
    """Рекурсивно строит дерево отделов."""
    all_deps = await client.list_all("department.get")
    by_parent: dict[int, list] = {}
    for d in all_deps:
        pid = int(d.get("PARENT", 0))
        by_parent.setdefault(pid, []).append(d)

    def build(parent_id: int) -> list:
        children = by_parent.get(parent_id, [])
        return [
            {**d, "children": build(int(d["ID"]))}
            for d in children
        ]

    return build(0)


# === ПРИСУТСТВИЕ ===
@registry.tool("user_online", "Список онлайн-пользователей", MODULE, {})
async def user_online(client):
    return await client.call("user.get", {"FILTER": {"IS_ONLINE": "Y"}, "SELECT": ["ID", "NAME", "LAST_NAME"]})

@registry.tool("user_absence_list", "Список отсутствий", MODULE, {
    "from": {"type": "string"}, "to": {"type": "string"},
})
async def absence_list(client, **kwargs):
    return await client.call("timeman.timecontrol.reports.get", kwargs)
