"""Tests for Jarvis V3.1 Brain plugin."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.brain.router import BrainRouter, TaskType


def test_router_classifies_code():
    router = BrainRouter()
    assert router.classify("напиши код для парсера") == TaskType.CODE_GEN
    assert router.classify("создай функцию hello") == TaskType.CODE_GEN
    assert router.classify("python script") == TaskType.CODE_GEN


def test_router_classifies_reasoning():
    router = BrainRouter()
    assert router.classify("объясни как работает TCP") == TaskType.REASONING
    assert router.classify("почему это не работает") == TaskType.REASONING
    assert router.classify("сравни Docker и Kubernetes") == TaskType.REASONING


def test_router_classifies_simple():
    router = BrainRouter()
    assert router.classify("привет") == TaskType.SIMPLE_CHAT
    assert router.classify("как дела") == TaskType.SIMPLE_CHAT
    assert router.classify("пока") == TaskType.SIMPLE_CHAT


def test_router_classifies_extraction():
    router = BrainRouter()
    assert router.classify("запомни что я работаю над проектом") == TaskType.EXTRACTION
    assert router.classify("извлеки факты из текста") == TaskType.EXTRACTION


def test_router_returns_model():
    router = BrainRouter()
    route = router.route("привет")
    assert "model" in route
    assert "task_type" in route
    assert "temperature" in route


def test_router_temperature_ranges():
    router = BrainRouter()
    for task_type in TaskType:
        route = router.route(f"test {task_type.value}")
        assert 0.0 <= route["temperature"] <= 1.0
