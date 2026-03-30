"""Модуль Диска Bitrix24 — хранилища, папки, файлы."""

from src.core.registry import registry

MODULE = "disk"


# === ХРАНИЛИЩА ===
@registry.tool("disk_storage_list", "Список хранилищ", MODULE, {})
async def storage_list(client):
    return await client.call("disk.storage.getlist")

@registry.tool("disk_storage_get", "Получить хранилище", MODULE, {"id": {"type": "integer"}})
async def storage_get(client, id):
    return await client.call("disk.storage.get", {"id": id})

@registry.tool("disk_storage_children", "Содержимое корня хранилища", MODULE, {"id": {"type": "integer"}, "filter": {"type": "object"}})
async def storage_children(client, id, filter=None):
    return await client.call("disk.storage.getchildren", {"id": id, "filter": filter or {}})

@registry.tool("disk_storage_add_folder", "Создать папку в хранилище", MODULE, {"id": {"type": "integer"}, "name": {"type": "string"}})
async def storage_add_folder(client, id, name):
    return await client.call("disk.storage.addfolder", {"id": id, "data": {"NAME": name}})

@registry.tool("disk_storage_upload", "Загрузить файл в хранилище", MODULE, {
    "id": {"type": "integer"}, "name": {"type": "string"}, "content": {"type": "string", "description": "Base64 содержимое файла"},
})
async def storage_upload(client, id, name, content):
    return await client.call("disk.storage.uploadfile", {"id": id, "data": {"NAME": name}, "fileContent": [name, content]})


# === ПАПКИ ===
@registry.tool("disk_folder_get", "Получить папку", MODULE, {"id": {"type": "integer"}})
async def folder_get(client, id):
    return await client.call("disk.folder.get", {"id": id})

@registry.tool("disk_folder_children", "Содержимое папки", MODULE, {"id": {"type": "integer"}, "filter": {"type": "object"}})
async def folder_children(client, id, filter=None):
    return await client.call("disk.folder.getchildren", {"id": id, "filter": filter or {}})

@registry.tool("disk_folder_add_subfolder", "Создать подпапку", MODULE, {"id": {"type": "integer"}, "name": {"type": "string"}})
async def folder_add_subfolder(client, id, name):
    return await client.call("disk.folder.addsubfolder", {"id": id, "data": {"NAME": name}})

@registry.tool("disk_folder_upload", "Загрузить файл в папку", MODULE, {
    "id": {"type": "integer"}, "name": {"type": "string"}, "content": {"type": "string"},
})
async def folder_upload(client, id, name, content):
    return await client.call("disk.folder.uploadfile", {"id": id, "data": {"NAME": name}, "fileContent": [name, content]})

@registry.tool("disk_folder_rename", "Переименовать папку", MODULE, {"id": {"type": "integer"}, "name": {"type": "string"}})
async def folder_rename(client, id, name):
    return await client.call("disk.folder.update", {"id": id, "data": {"NAME": name}})

@registry.tool("disk_folder_move", "Переместить папку", MODULE, {"id": {"type": "integer"}, "targetFolderId": {"type": "integer"}})
async def folder_move(client, id, targetFolderId):
    return await client.call("disk.folder.moveto", {"id": id, "targetFolderId": targetFolderId})

@registry.tool("disk_folder_copy", "Скопировать папку", MODULE, {"id": {"type": "integer"}, "targetFolderId": {"type": "integer"}})
async def folder_copy(client, id, targetFolderId):
    return await client.call("disk.folder.copyto", {"id": id, "targetFolderId": targetFolderId})

@registry.tool("disk_folder_delete", "Удалить папку", MODULE, {"id": {"type": "integer"}})
async def folder_delete(client, id):
    return await client.call("disk.folder.markdeleted", {"id": id})

@registry.tool("disk_folder_restore", "Восстановить папку из корзины", MODULE, {"id": {"type": "integer"}})
async def folder_restore(client, id):
    return await client.call("disk.folder.restore", {"id": id})


# === ФАЙЛЫ ===
@registry.tool("disk_file_get", "Получить информацию о файле", MODULE, {"id": {"type": "integer"}})
async def file_get(client, id):
    return await client.call("disk.file.get", {"id": id})

@registry.tool("disk_file_rename", "Переименовать файл", MODULE, {"id": {"type": "integer"}, "name": {"type": "string"}})
async def file_rename(client, id, name):
    return await client.call("disk.file.update", {"id": id, "data": {"NAME": name}})

@registry.tool("disk_file_move", "Переместить файл", MODULE, {"id": {"type": "integer"}, "targetFolderId": {"type": "integer"}})
async def file_move(client, id, targetFolderId):
    return await client.call("disk.file.moveto", {"id": id, "targetFolderId": targetFolderId})

@registry.tool("disk_file_copy", "Скопировать файл", MODULE, {"id": {"type": "integer"}, "targetFolderId": {"type": "integer"}})
async def file_copy(client, id, targetFolderId):
    return await client.call("disk.file.copyto", {"id": id, "targetFolderId": targetFolderId})

@registry.tool("disk_file_delete", "Удалить файл", MODULE, {"id": {"type": "integer"}})
async def file_delete(client, id):
    return await client.call("disk.file.markdeleted", {"id": id})

@registry.tool("disk_file_restore", "Восстановить файл из корзины", MODULE, {"id": {"type": "integer"}})
async def file_restore(client, id):
    return await client.call("disk.file.restore", {"id": id})

@registry.tool("disk_file_get_versions", "Версии файла", MODULE, {"id": {"type": "integer"}})
async def file_versions(client, id):
    return await client.call("disk.file.getVersions", {"id": id})

@registry.tool("disk_file_get_external_link", "Внешняя ссылка на файл", MODULE, {"id": {"type": "integer"}})
async def file_external_link(client, id):
    return await client.call("disk.file.getExternalLink", {"id": id})


# === ПРАВА ===
@registry.tool("disk_rights_get", "Права доступа к объекту", MODULE, {"objectId": {"type": "integer"}, "objectType": {"type": "string", "description": "folder|file"}})
async def rights_get(client, objectId, objectType="folder"):
    method = f"disk.{objectType}.listSharing"
    return await client.call(method, {"id": objectId})
