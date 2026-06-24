"""
Brain Router — Маршрутизация задач к моделям.
Простые запросы → быстрая модель (gemma2:2b)
Reasoning/analysis → мощная модель (qwen2.5:14b)
Код → кодовая модель (gemma-4-12B-coder)
Извлечение → средняя модель (qwen2.5:7b)
"""
from enum import Enum
from typing import Optional


class TaskType(str, Enum):
    SIMPLE_CHAT = "simple_chat"
    REASONING = "reasoning"
    CODE_GEN = "code_gen"
    ANALYSIS = "analysis"
    EXTRACTION = "extraction"


_TASK_MODEL_MAP = {
    TaskType.SIMPLE_CHAT: "gemma2:2b",
    TaskType.REASONING: "qwen2.5:7b",
    TaskType.CODE_GEN: "hf.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF:Q4_K_M",
    TaskType.ANALYSIS: "qwen2.5:7b",
    TaskType.EXTRACTION: "qwen2.5:7b",
}

TASK_TEMPERATURE = {
    TaskType.SIMPLE_CHAT: 0.7,
    TaskType.REASONING: 0.3,
    TaskType.CODE_GEN: 0.2,
    TaskType.ANALYSIS: 0.5,
    TaskType.EXTRACTION: 0.1,
}


def _load_config_models():
    try:
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / "core" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        brain_cfg = config.get("plugins", {}).get("brain", {})
        if brain_cfg.get("model"):
            _TASK_MODEL_MAP[TaskType.ANALYSIS] = brain_cfg["model"]
            _TASK_MODEL_MAP[TaskType.REASONING] = brain_cfg["model"]
            _TASK_MODEL_MAP[TaskType.EXTRACTION] = brain_cfg["model"]
        if brain_cfg.get("model_simple"):
            _TASK_MODEL_MAP[TaskType.SIMPLE_CHAT] = brain_cfg["model_simple"]
        if brain_cfg.get("model_code"):
            _TASK_MODEL_MAP[TaskType.CODE_GEN] = brain_cfg["model_code"]
        default = config.get("ollama", {}).get("default_model")
        if default:
            BrainRouter.default_model = default
    except Exception:
        pass

_load_config_models()

TASK_MODEL_MAP = _TASK_MODEL_MAP


class BrainRouter:
    def __init__(self, default_model: str = "qwen2.5:7b"):
        self.default_model = default_model

    def classify(self, text: str, has_tool_context: bool = False) -> TaskType:
        text_lower = text.lower()

        code_indicators = [
            "напиши код", "код для", "функцию", "класс ", "импортируй",
            "python", "def ", "class ", "import ", "async ", "await ",
            "pycode", "скрипт", "программ", "алгоритм",
        ]
        if any(ind in text_lower for ind in code_indicators):
            return TaskType.CODE_GEN

        reasoning_indicators = [
            "объясни", "почему", "как работает", "разбери", "проанализируй",
            "сравни", "оцени", "аргумент", "контраргумент", "критик",
            "плюсы", "минусы", "преимущ", "недостат",
        ]
        if any(ind in text_lower for ind in reasoning_indicators):
            return TaskType.REASONING

        extract_indicators = [
            "извлеки", "найди факт", "запомни", "сохрани", "факт",
            "сущность", "имя", "проект", "инструмент",
        ]
        if any(ind in text_lower for ind in extract_indicators):
            return TaskType.EXTRACTION

        analysis_indicators = [
            "проанализируй", "сводка", "отчёт", "resume", "итог",
            "суммариз", "кратко", "суть",
        ]
        if any(ind in text_lower for ind in analysis_indicators):
            return TaskType.ANALYSIS

        web_indicators = [
            "найди в интернете", "поищи", "загугли", "поиск в интернет",
            "что происходит", "актуальн", "свежие новости", "recent",
        ]
        if any(ind in text_lower for ind in web_indicators):
            return TaskType.ANALYSIS

        if has_tool_context:
            return TaskType.REASONING

        return TaskType.SIMPLE_CHAT

    def get_model(self, task_type: TaskType) -> str:
        return TASK_MODEL_MAP.get(task_type, self.default_model)

    def get_temperature(self, task_type: TaskType) -> float:
        return TASK_TEMPERATURE.get(task_type, 0.7)

    def route(self, text: str, has_tool_context: bool = False) -> dict:
        task_type = self.classify(text, has_tool_context)
        return {
            "task_type": task_type.value,
            "model": self.get_model(task_type),
            "temperature": self.get_temperature(task_type),
        }
