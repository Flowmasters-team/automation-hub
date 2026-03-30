#!/usr/bin/env python3
"""
Оркестратор мультиагентной системы.

Запускает агентов Claude Code параллельно и собирает результаты.
Поддерживает два режима:
  - parallel: все агенты работают одновременно
  - pipeline: результат предыдущего → вход следующего

Использование:
    python orchestrator.py parallel --agents api-designer,backend-dev,code-reviewer --task "Спроектировать API для чат-платформы"
    python orchestrator.py pipeline --agents backend-dev,api-designer,code-reviewer --task "Создать backend для чат-платформы"
"""

import argparse
import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class AgentResult:
    agent: str
    status: str  # success | error
    output: str
    duration_sec: float
    files_created: list[str] = field(default_factory=list)


AGENTS_DIR = Path(__file__).parent
RESULTS_DIR = Path(__file__).parent.parent / "results"


def get_agent_prompt(agent_name: str) -> str | None:
    """Читает системный промпт агента из .md файла."""
    agent_file = AGENTS_DIR / f"{agent_name.replace('-', '_')}.md"
    if not agent_file.exists():
        return None
    content = agent_file.read_text(encoding="utf-8")
    # Отделяем frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content


async def run_agent(agent_name: str, task: str, context: str = "") -> AgentResult:
    """Запускает одного агента через Claude Code CLI."""
    start = datetime.now()

    prompt = get_agent_prompt(agent_name)
    if not prompt:
        return AgentResult(
            agent=agent_name,
            status="error",
            output=f"Agent config not found: {agent_name}",
            duration_sec=0,
        )

    full_prompt = f"""Ты работаешь как агент '{agent_name}'.

{prompt}

## Задача
{task}

{"## Контекст от предыдущего агента" + chr(10) + context if context else ""}

Выполни задачу и сохрани результаты в файлы.
"""

    try:
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "--print",
            "--dangerously-skip-permissions",
            "-m", full_prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        duration = (datetime.now() - start).total_seconds()

        return AgentResult(
            agent=agent_name,
            status="success" if proc.returncode == 0 else "error",
            output=output,
            duration_sec=duration,
        )
    except FileNotFoundError:
        return AgentResult(
            agent=agent_name,
            status="error",
            output="Claude CLI not found. Install: npm install -g @anthropic-ai/claude-code",
            duration_sec=0,
        )


async def run_parallel(agents: list[str], task: str) -> list[AgentResult]:
    """Запускает всех агентов параллельно."""
    print(f"\n🚀 Parallel mode: запуск {len(agents)} агентов")
    print(f"   Агенты: {', '.join(agents)}")
    print(f"   Задача: {task[:80]}...\n")

    tasks = [run_agent(name, task) for name in agents]
    results = await asyncio.gather(*tasks)
    return list(results)


async def run_pipeline(agents: list[str], task: str) -> list[AgentResult]:
    """Запускает агентов последовательно, передавая контекст."""
    print(f"\n🔗 Pipeline mode: {' → '.join(agents)}")
    print(f"   Задача: {task[:80]}...\n")

    results = []
    context = ""

    for agent_name in agents:
        print(f"   ⏳ {agent_name}...")
        result = await run_agent(agent_name, task, context)
        results.append(result)

        if result.status == "success":
            # Передаём вывод как контекст следующему агенту
            context = result.output
            print(f"   ✅ {agent_name} ({result.duration_sec:.1f}s)")
        else:
            print(f"   ❌ {agent_name} — {result.output[:100]}")
            break

    return results


def save_report(results: list[AgentResult], mode: str) -> Path:
    """Сохраняет отчёт о прогоне."""
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = RESULTS_DIR / f"run_{timestamp}.json"

    report = {
        "mode": mode,
        "timestamp": timestamp,
        "agents": [
            {
                "name": r.agent,
                "status": r.status,
                "duration_sec": r.duration_sec,
                "output_length": len(r.output),
            }
            for r in results
        ],
        "total_duration_sec": sum(r.duration_sec for r in results),
        "success_count": sum(1 for r in results if r.status == "success"),
        "error_count": sum(1 for r in results if r.status == "error"),
    }

    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path


def print_summary(results: list[AgentResult]):
    """Печатает сводку."""
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ")
    print("=" * 60)

    for r in results:
        icon = "✅" if r.status == "success" else "❌"
        print(f"  {icon} {r.agent:20s}  {r.duration_sec:6.1f}s  {len(r.output):>6} chars")

    total = sum(r.duration_sec for r in results)
    ok = sum(1 for r in results if r.status == "success")
    print(f"\n  Total: {total:.1f}s | Success: {ok}/{len(results)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="AI Agent Orchestrator")
    parser.add_argument("mode", choices=["parallel", "pipeline"])
    parser.add_argument("--agents", required=True, help="Comma-separated agent names")
    parser.add_argument("--task", required=True, help="Task description")

    args = parser.parse_args()
    agents = [a.strip() for a in args.agents.split(",")]

    if args.mode == "parallel":
        results = asyncio.run(run_parallel(agents, args.task))
    else:
        results = asyncio.run(run_pipeline(agents, args.task))

    print_summary(results)
    report_path = save_report(results, args.mode)
    print(f"\n📄 Отчёт: {report_path}")


if __name__ == "__main__":
    main()
