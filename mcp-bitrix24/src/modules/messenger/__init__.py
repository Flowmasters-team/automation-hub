"""Модуль мессенджера Bitrix24 — чаты, сообщения, уведомления."""

from src.core.registry import registry

MODULE = "messenger"


# === ЧАТЫ ===
@registry.tool("im_chat_list", "Список чатов пользователя", MODULE, {"filter": {"type": "object"}})
async def chat_list(client, filter=None):
    return await client.call("im.recent.list", filter or {})

@registry.tool("im_chat_get", "Получить чат", MODULE, {"chatId": {"type": "integer"}})
async def chat_get(client, chatId):
    return await client.call("im.chat.get", {"CHAT_ID": chatId})

@registry.tool("im_chat_create", "Создать групповой чат", MODULE, {
    "title": {"type": "string"}, "users": {"type": "array", "items": {"type": "integer"}}, "description": {"type": "string"},
})
async def chat_create(client, title, users, description=""):
    return await client.call("im.chat.add", {"TITLE": title, "USERS": users, "DESCRIPTION": description})

@registry.tool("im_chat_update", "Обновить чат", MODULE, {"chatId": {"type": "integer"}, "fields": {"type": "object"}})
async def chat_update(client, chatId, fields):
    return await client.call("im.chat.update", {"CHAT_ID": chatId, **fields})

@registry.tool("im_chat_add_users", "Добавить пользователей в чат", MODULE, {"chatId": {"type": "integer"}, "users": {"type": "array"}})
async def chat_add_users(client, chatId, users):
    return await client.call("im.chat.user.add", {"CHAT_ID": chatId, "USERS": users})

@registry.tool("im_chat_remove_user", "Удалить пользователя из чата", MODULE, {"chatId": {"type": "integer"}, "userId": {"type": "integer"}})
async def chat_remove_user(client, chatId, userId):
    return await client.call("im.chat.user.delete", {"CHAT_ID": chatId, "USER_ID": userId})

@registry.tool("im_chat_set_owner", "Назначить владельца чата", MODULE, {"chatId": {"type": "integer"}, "userId": {"type": "integer"}})
async def chat_set_owner(client, chatId, userId):
    return await client.call("im.chat.setOwner", {"CHAT_ID": chatId, "USER_ID": userId})

@registry.tool("im_chat_leave", "Покинуть чат", MODULE, {"chatId": {"type": "integer"}})
async def chat_leave(client, chatId):
    return await client.call("im.chat.leave", {"CHAT_ID": chatId})

@registry.tool("im_chat_mute", "Мут/анмут чата", MODULE, {"chatId": {"type": "integer"}, "mute": {"type": "boolean"}})
async def chat_mute(client, chatId, mute=True):
    action = "Y" if mute else "N"
    return await client.call("im.chat.mute", {"CHAT_ID": chatId, "MUTE": action})


# === СООБЩЕНИЯ ===
@registry.tool("im_message_send", "Отправить сообщение", MODULE, {
    "dialog_id": {"type": "string", "description": "ID диалога (chatXXX для группового, userID для ЛС)"},
    "message": {"type": "string"},
})
async def message_send(client, dialog_id, message):
    return await client.call("im.message.add", {"DIALOG_ID": dialog_id, "MESSAGE": message})

@registry.tool("im_message_update", "Обновить сообщение", MODULE, {"messageId": {"type": "integer"}, "message": {"type": "string"}})
async def message_update(client, messageId, message):
    return await client.call("im.message.update", {"MESSAGE_ID": messageId, "MESSAGE": message})

@registry.tool("im_message_delete", "Удалить сообщение", MODULE, {"messageId": {"type": "integer"}})
async def message_delete(client, messageId):
    return await client.call("im.message.delete", {"MESSAGE_ID": messageId})

@registry.tool("im_message_like", "Лайк сообщения", MODULE, {"messageId": {"type": "integer"}})
async def message_like(client, messageId):
    return await client.call("im.message.like", {"MESSAGE_ID": messageId})

@registry.tool("im_dialog_messages", "История сообщений диалога", MODULE, {
    "dialog_id": {"type": "string"}, "limit": {"type": "integer"}, "last_id": {"type": "integer"},
})
async def dialog_messages(client, dialog_id, limit=20, last_id=0):
    params = {"DIALOG_ID": dialog_id, "LIMIT": limit}
    if last_id:
        params["LAST_ID"] = last_id
    return await client.call("im.dialog.messages.get", params)

@registry.tool("im_message_read", "Отметить сообщения прочитанными", MODULE, {"dialog_id": {"type": "string"}, "messageId": {"type": "integer"}})
async def message_read(client, dialog_id, messageId):
    return await client.call("im.dialog.read", {"DIALOG_ID": dialog_id, "MESSAGE_ID": messageId})


# === УВЕДОМЛЕНИЯ ===
@registry.tool("im_notify_send", "Отправить уведомление пользователю", MODULE, {
    "userId": {"type": "integer"}, "message": {"type": "string"}, "type": {"type": "string", "description": "SYSTEM|CONFIRM"},
})
async def notify_send(client, userId, message, type="SYSTEM"):
    return await client.call("im.notify.system.add", {"USER_ID": userId, "MESSAGE": message, "MESSAGE_TYPE": type})

@registry.tool("im_notify_list", "Список уведомлений", MODULE, {})
async def notify_list(client):
    return await client.call("im.notify.get")

@registry.tool("im_notify_read", "Прочитать уведомления", MODULE, {"id": {"type": "integer"}})
async def notify_read(client, id):
    return await client.call("im.notify.read", {"ID": id})

@registry.tool("im_notify_delete", "Удалить уведомление", MODULE, {"id": {"type": "integer"}})
async def notify_delete(client, id):
    return await client.call("im.notify.delete", {"ID": id})


# === БОТЫ ===
@registry.tool("im_bot_list", "Список ботов", MODULE, {})
async def bot_list(client):
    return await client.call("imbot.bot.list")

@registry.tool("im_bot_register", "Зарегистрировать бота", MODULE, {"fields": {"type": "object"}})
async def bot_register(client, fields):
    return await client.call("imbot.register", fields)

@registry.tool("im_bot_unregister", "Удалить бота", MODULE, {"botId": {"type": "integer"}})
async def bot_unregister(client, botId):
    return await client.call("imbot.unregister", {"BOT_ID": botId})

@registry.tool("im_bot_send_message", "Отправить сообщение от бота", MODULE, {
    "botId": {"type": "integer"}, "dialog_id": {"type": "string"}, "message": {"type": "string"},
})
async def bot_send_message(client, botId, dialog_id, message):
    return await client.call("imbot.message.add", {"BOT_ID": botId, "DIALOG_ID": dialog_id, "MESSAGE": message})
