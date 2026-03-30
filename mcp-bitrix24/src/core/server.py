"""MCP-сервер: инициализация, загрузка модулей, обработка запросов."""

import importlib
import json
import os
import sys
from typing import Any

from .client import BitrixClient
from .registry import registry


MODULES = [
    "crm",
    "tasks",
    "disk",
    "messenger",
    "calendar",
    "orgstructure",
    "bizproc",
    "lists",
    "telephony",
]


def load_modules():
    """Динамически загружает все доменные модули."""
    for module_name in MODULES:
        try:
            importlib.import_module(f"src.modules.{module_name}")
        except ImportError as e:
            print(f"Warning: module '{module_name}' not loaded: {e}", file=sys.stderr)


def get_tools_manifest() -> list[dict[str, Any]]:
    """Возвращает список инструментов в формате MCP."""
    tools = []
    for tool in registry.list_tools():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": {
                "type": "object",
                "properties": tool.parameters,
            },
        })
    return tools


async def handle_tool_call(name: str, arguments: dict[str, Any], client: BitrixClient) -> Any:
    """Обрабатывает вызов инструмента."""
    tool = registry.get(name)
    if not tool:
        return {"error": f"Tool '{name}' not found"}
    return await tool.handler(client=client, **arguments)


def run_stdio_server():
    """Запускает MCP-сервер в режиме stdio (для Claude Code)."""
    import asyncio

    webhook_url = os.environ.get("BITRIX24_WEBHOOK_URL", "")
    if not webhook_url:
        print("Error: BITRIX24_WEBHOOK_URL not set", file=sys.stderr)
        sys.exit(1)

    load_modules()

    stats = registry.module_stats()
    total = registry.total_count
    print(f"Loaded {total} tools from {len(stats)} modules:", file=sys.stderr)
    for mod, count in sorted(stats.items()):
        print(f"  {mod}: {count}", file=sys.stderr)

    async def main_loop():
        async with BitrixClient(webhook_url) as client:
            for line in sys.stdin:
                try:
                    request = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                method = request.get("method")

                if method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"tools": get_tools_manifest()},
                    }
                elif method == "tools/call":
                    params = request.get("params", {})
                    result = await handle_tool_call(
                        params["name"], params.get("arguments", {}), client
                    )
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]},
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -32601, "message": f"Unknown method: {method}"},
                    }

                print(json.dumps(response, ensure_ascii=False))
                sys.stdout.flush()

    asyncio.run(main_loop())
