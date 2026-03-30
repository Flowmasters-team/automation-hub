"""
Reverse Engineering Toolkit — перехват XHR-запросов через Playwright.

Запускает браузер, авторизуется на целевой платформе, перехватывает все API-запросы,
строит карту эндпоинтов и генерирует async Python-клиент.

Использование:
    python interceptor.py --url https://app.example.com --output api_map.json
    python interceptor.py --url https://app.example.com --output api_map.json --headless
"""

import argparse
import asyncio
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from urllib.parse import urlparse, parse_qs


@dataclass
class CapturedRequest:
    method: str
    url: str
    path: str
    query_params: dict
    headers: dict
    body: str | None
    response_status: int | None = None
    response_body: str | None = None
    content_type: str = ""
    timestamp: str = ""


@dataclass
class Endpoint:
    method: str
    path: str
    path_pattern: str  # /api/users/123 → /api/users/{id}
    query_params: list[str] = field(default_factory=list)
    request_body_sample: dict | None = None
    response_body_sample: dict | None = None
    headers_required: list[str] = field(default_factory=list)
    auth_type: str = ""  # bearer | cookie | api_key | none
    occurrences: int = 0


class APIInterceptor:
    """Перехватчик API-запросов через Playwright."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.captured: list[CapturedRequest] = []
        self.endpoints: dict[str, Endpoint] = {}

    async def start(self, headless: bool = False, wait_seconds: int = 60):
        """Запускает браузер и перехватывает запросы."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("Install: pip install playwright && playwright install chromium")
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            # Перехват запросов
            page.on("request", lambda req: asyncio.ensure_future(self._on_request(req)))
            page.on("response", lambda resp: asyncio.ensure_future(self._on_response(resp)))

            print(f"Opening {self.base_url}")
            print(f"Intercepting for {wait_seconds}s... Navigate the app manually.\n")

            await page.goto(self.base_url)

            # Ждём, пока пользователь навигирует по приложению
            await asyncio.sleep(wait_seconds)

            await browser.close()

        self._build_endpoints()

    async def _on_request(self, request):
        """Обработчик перехваченного запроса."""
        url = request.url
        parsed = urlparse(url)

        # Фильтруем: только XHR/fetch к тому же домену или API
        if request.resource_type not in ("xhr", "fetch"):
            return
        if parsed.netloc != self.base_domain and "api" not in parsed.path:
            return

        # Пропускаем статику
        if any(parsed.path.endswith(ext) for ext in (".js", ".css", ".png", ".jpg", ".svg", ".woff2")):
            return

        body = None
        try:
            body = request.post_data
        except Exception:
            pass

        captured = CapturedRequest(
            method=request.method,
            url=url,
            path=parsed.path,
            query_params=dict(parse_qs(parsed.query)),
            headers={k: v for k, v in request.headers.items() if k.lower() in (
                "authorization", "content-type", "x-api-key", "x-csrf-token", "cookie",
            )},
            body=body,
            timestamp=datetime.now().isoformat(),
        )
        self.captured.append(captured)
        print(f"  {request.method:6s} {parsed.path}")

    async def _on_response(self, response):
        """Обработчик ответа."""
        url = response.url
        parsed = urlparse(url)

        # Ищем соответствующий captured request
        for cap in reversed(self.captured):
            if cap.url == url and cap.response_status is None:
                cap.response_status = response.status
                cap.content_type = response.headers.get("content-type", "")
                try:
                    if "json" in cap.content_type:
                        body = await response.text()
                        cap.response_body = body[:2000]  # Лимит на размер
                except Exception:
                    pass
                break

    def _normalize_path(self, path: str) -> str:
        """Нормализует путь: /api/users/123 → /api/users/{id}."""
        parts = path.split("/")
        normalized = []
        for part in parts:
            if re.match(r"^\d+$", part):
                normalized.append("{id}")
            elif re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-", part):
                normalized.append("{uuid}")
            else:
                normalized.append(part)
        return "/".join(normalized)

    def _detect_auth(self, headers: dict) -> str:
        """Определяет тип аутентификации."""
        if "authorization" in headers:
            auth = headers["authorization"]
            if auth.startswith("Bearer "):
                return "bearer"
            elif auth.startswith("Basic "):
                return "basic"
            return "custom"
        if "x-api-key" in headers:
            return "api_key"
        if "cookie" in headers:
            return "cookie"
        return "none"

    def _build_endpoints(self):
        """Строит карту уникальных эндпоинтов."""
        for cap in self.captured:
            pattern = self._normalize_path(cap.path)
            key = f"{cap.method} {pattern}"

            if key not in self.endpoints:
                body_sample = None
                if cap.body:
                    try:
                        body_sample = json.loads(cap.body)
                    except json.JSONDecodeError:
                        pass

                resp_sample = None
                if cap.response_body:
                    try:
                        resp_sample = json.loads(cap.response_body)
                    except json.JSONDecodeError:
                        pass

                self.endpoints[key] = Endpoint(
                    method=cap.method,
                    path=cap.path,
                    path_pattern=pattern,
                    query_params=list(cap.query_params.keys()),
                    request_body_sample=body_sample,
                    response_body_sample=resp_sample,
                    headers_required=[k for k in cap.headers if k != "content-type"],
                    auth_type=self._detect_auth(cap.headers),
                    occurrences=1,
                )
            else:
                self.endpoints[key].occurrences += 1

    def export_map(self, output_path: str):
        """Экспортирует карту API в JSON."""
        data = {
            "base_url": self.base_url,
            "captured_at": datetime.now().isoformat(),
            "total_requests": len(self.captured),
            "unique_endpoints": len(self.endpoints),
            "endpoints": [asdict(ep) for ep in self.endpoints.values()],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nExported {len(self.endpoints)} endpoints to {output_path}")

    def print_summary(self):
        """Печатает сводку."""
        print(f"\n{'='*60}")
        print(f"API Map: {self.base_url}")
        print(f"Total requests captured: {len(self.captured)}")
        print(f"Unique endpoints: {len(self.endpoints)}")
        print(f"{'='*60}\n")

        by_method = defaultdict(list)
        for ep in self.endpoints.values():
            by_method[ep.method].append(ep)

        for method in sorted(by_method):
            print(f"\n{method}:")
            for ep in sorted(by_method[method], key=lambda x: x.path_pattern):
                auth = f" [{ep.auth_type}]" if ep.auth_type != "none" else ""
                print(f"  {ep.path_pattern}{auth}  (x{ep.occurrences})")


def generate_client(api_map_path: str, output_path: str):
    """Генерирует async Python-клиент из карты API."""
    with open(api_map_path, encoding="utf-8") as f:
        data = json.load(f)

    base_url = data["base_url"]
    endpoints = data["endpoints"]

    lines = [
        '"""Auto-generated async API client."""',
        "",
        "import httpx",
        "from typing import Any",
        "",
        "",
        "class APIClient:",
        f'    """Client for {base_url}."""',
        "",
        "    def __init__(self, base_url: str, token: str = ''):",
        f'        self.base_url = base_url.rstrip("/")',
        "        self.token = token",
        "        self._client = httpx.AsyncClient(timeout=30.0)",
        "",
        "    async def _request(self, method: str, path: str, **kwargs) -> dict:",
        "        headers = kwargs.pop('headers', {})",
        "        if self.token:",
        "            headers['Authorization'] = f'Bearer {self.token}'",
        "        resp = await self._client.request(method, f'{self.base_url}{path}', headers=headers, **kwargs)",
        "        resp.raise_for_status()",
        "        return resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {'status': resp.status_code}",
        "",
    ]

    seen_names = set()
    for ep in endpoints:
        method = ep["method"].lower()
        pattern = ep["path_pattern"]

        # Генерируем имя метода
        name_parts = [method] + [p for p in pattern.split("/") if p and p not in ("{id}", "{uuid}", "api", "v1", "v2")]
        func_name = "_".join(name_parts).replace("-", "_")
        if func_name in seen_names:
            func_name += f"_{len(seen_names)}"
        seen_names.add(func_name)

        # Параметры
        path_params = re.findall(r"\{(\w+)\}", pattern)
        params = ", ".join(f"{p}: str" for p in path_params)
        if params:
            params = ", " + params

        # Тело
        has_body = method in ("post", "put", "patch") and ep.get("request_body_sample")
        body_param = ", data: dict | None = None" if has_body else ""

        # Путь с подстановкой
        path_expr = f'f"{pattern}"' if path_params else f'"{pattern}"'

        body_kwarg = ", json=data" if has_body else ""

        lines.extend([
            f"    async def {func_name}(self{params}{body_param}) -> dict:",
            f'        return await self._request("{method.upper()}", {path_expr}{body_kwarg})',
            "",
        ])

    lines.extend([
        "    async def close(self):",
        "        await self._client.aclose()",
        "",
        "    async def __aenter__(self):",
        "        return self",
        "",
        "    async def __aexit__(self, *args):",
        "        await self.close()",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated client with {len(seen_names)} methods: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="API Reverse Engineering Toolkit")
    sub = parser.add_subparsers(dest="command")

    # intercept
    intercept = sub.add_parser("intercept", help="Capture API requests via Playwright")
    intercept.add_argument("--url", required=True)
    intercept.add_argument("--output", default="api_map.json")
    intercept.add_argument("--headless", action="store_true")
    intercept.add_argument("--wait", type=int, default=60, help="Seconds to wait")

    # generate
    gen = sub.add_parser("generate", help="Generate async client from API map")
    gen.add_argument("--input", required=True, help="api_map.json path")
    gen.add_argument("--output", default="client.py")

    args = parser.parse_args()

    if args.command == "intercept":
        interceptor = APIInterceptor(args.url)
        asyncio.run(interceptor.start(headless=args.headless, wait_seconds=args.wait))
        interceptor.print_summary()
        interceptor.export_map(args.output)
    elif args.command == "generate":
        generate_client(args.input, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
