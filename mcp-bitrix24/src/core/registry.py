"""Реестр MCP-инструментов с автоматической регистрацией модулей."""

from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine


@dataclass
class ToolDef:
    """Определение одного MCP-инструмента."""
    name: str
    description: str
    module: str
    parameters: dict[str, Any]
    handler: Callable[..., Coroutine]


class ToolRegistry:
    """Глобальный реестр инструментов. Модули регистрируют свои инструменты сюда."""

    def __init__(self):
        self._tools: dict[str, ToolDef] = {}
        self._modules: dict[str, list[str]] = {}

    def register(
        self,
        name: str,
        description: str,
        module: str,
        parameters: dict[str, Any],
        handler: Callable,
    ):
        """Регистрирует инструмент."""
        tool = ToolDef(
            name=name,
            description=description,
            module=module,
            parameters=parameters,
            handler=handler,
        )
        self._tools[name] = tool
        self._modules.setdefault(module, []).append(name)

    def tool(self, name: str, description: str, module: str, parameters: dict[str, Any]):
        """Декоратор для регистрации инструмента."""
        def decorator(func: Callable) -> Callable:
            self.register(name, description, module, parameters, func)
            return func
        return decorator

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDef]:
        return list(self._tools.values())

    def list_by_module(self, module: str) -> list[ToolDef]:
        names = self._modules.get(module, [])
        return [self._tools[n] for n in names]

    def module_stats(self) -> dict[str, int]:
        return {mod: len(tools) for mod, tools in self._modules.items()}

    @property
    def total_count(self) -> int:
        return len(self._tools)


# Глобальный реестр
registry = ToolRegistry()
