"""Async HTTP-клиент для Bitrix24 REST API."""

import asyncio
from typing import Any

import httpx


class BitrixClient:
    """Асинхронный клиент Bitrix24 REST API с rate limiting и batch."""

    BASE_METHODS_PER_SEC = 2  # Лимит Bitrix24

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._semaphore = asyncio.Semaphore(self.BASE_METHODS_PER_SEC)

    async def call(self, method: str, params: dict[str, Any] | None = None) -> dict:
        """Вызов одного метода Bitrix24 REST API."""
        async with self._semaphore:
            url = f"{self.webhook_url}/{method}"
            response = await self._client.post(url, json=params or {})
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise BitrixApiError(data["error"], data.get("error_description", ""))
            return data.get("result", data)

    async def call_batch(
        self, commands: dict[str, str], params: dict[str, dict] | None = None
    ) -> dict:
        """Batch-вызов до 50 методов за один запрос."""
        batch_params: dict[str, Any] = {"cmd": commands}
        if params:
            batch_params["params"] = params
        return await self.call("batch", batch_params)

    async def list_all(self, method: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Получить ВСЕ записи с автопагинацией."""
        params = dict(params or {})
        params.setdefault("start", 0)
        all_items: list[dict] = []

        while True:
            result = await self.call(method, params)
            if isinstance(result, list):
                all_items.extend(result)
                break
            elif isinstance(result, dict):
                items = result.get("result", result)
                if isinstance(items, list):
                    all_items.extend(items)
                total = result.get("total", 0)
                next_start = result.get("next")
                if next_start and len(all_items) < total:
                    params["start"] = next_start
                else:
                    break
            else:
                break

        return all_items

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


class BitrixApiError(Exception):
    def __init__(self, code: str, description: str):
        self.code = code
        self.description = description
        super().__init__(f"Bitrix24 API Error [{code}]: {description}")
