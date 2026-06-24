"""
Agent Registry — Реестр доступных агентов.
Каждый агент: модель, инструменты, описание, system prompt.
"""
from dataclasses import dataclass, field


@dataclass
class Agent:
    name: str
    model: str
    description: str
    tools: list[str] = field(default_factory=list)
    system_prompt: str = ""
    max_iterations: int = 3
    temperature: float = 0.7


REGISTRY: dict[str, Agent] = {
    "code": Agent(
        name="code",
        model="hf.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF:Q4_K_M",
        description="Генерация кода, скрипты, парсеры, алгоритмы",
        tools=["files/read", "files/write", "files/ls", "files/search", "files/mkdir"],
        system_prompt="Ты — кодовый агент. Пиши чистый, рабочий код. Минимум комментариев, максимум функциональности.",
        max_iterations=5,
        temperature=0.2,
    ),
    "research": Agent(
        name="research",
        model="qwen2.5:14b",
        description="Исследование, анализ, поиск информации, суммаризация",
        tools=["files/read", "files/search", "web/search", "rag/search", "rag/ask"],
        system_prompt="Ты — исследовательский агент. Анализируй, ищи информацию, давай структурированные ответы.",
        max_iterations=3,
        temperature=0.5,
    ),
    "file_ops": Agent(
        name="file_ops",
        model="gemma2:2b",
        description="Файловые операции: копирование, перемещение, чтение, запись",
        tools=["files/ls", "files/read", "files/write", "files/mkdir", "files/rm", "files/mv", "files/cp"],
        system_prompt="Ты — файловый агент. Выполняй файловые операции быстро и точно.",
        max_iterations=2,
        temperature=0.3,
    ),
}

DEFAULT_AGENT = "orchestrator"


def get_agent(name: str) -> Agent | None:
    return REGISTRY.get(name)


def list_agents() -> list[dict]:
    return [
        {
            "name": a.name,
            "model": a.model,
            "description": a.description,
            "tools": a.tools,
            "max_iterations": a.max_iterations,
        }
        for a in REGISTRY.values()
    ]


def classify_task(text: str) -> str:
    text_lower = text.lower()

    research_signals = [
        "найди", "проанализируй", "сравни", "объясни", "что такое",
        "как работает", "почему", "исследуй", "суммариз", "обзор",
    ]
    if any(s in text_lower for s in research_signals):
        return "research"

    code_signals = [
        "напиши код", "код для", "функцию", "скрипт", "программ",
        "python", "def ", "class ", "import ", "async ", "await ",
        "алгоритм", "парсер", "регулярк",
    ]
    if any(s in text_lower for s in code_signals):
        return "code"

    file_signals = [
        "покажи файл", "прочитай файл", "создай папку", "удали файл",
        "перемести", "скопируй", "список файл", "ls", "dir",
    ]
    if any(s in text_lower for s in file_signals):
        return "file_ops"

    return DEFAULT_AGENT
