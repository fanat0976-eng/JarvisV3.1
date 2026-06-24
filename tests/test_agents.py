"""Unit tests for Agents plugin."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.agents.registry import (
    get_agent, list_agents, classify_task, REGISTRY
)


class TestRegistry:
    def test_list_agents(self):
        agents = list_agents()
        assert len(agents) >= 3
        names = [a["name"] for a in agents]
        assert "code" in names
        assert "research" in names
        assert "file_ops" in names

    def test_get_agent(self):
        agent = get_agent("code")
        assert agent is not None
        assert agent.name == "code"
        assert "gemma" in agent.model.lower() or "coder" in agent.model.lower()

    def test_get_agent_missing(self):
        agent = get_agent("nonexistent")
        assert agent is None

    def test_agent_has_tools(self):
        for name in REGISTRY:
            agent = get_agent(name)
            assert len(agent.tools) > 0

    def test_agent_has_system_prompt(self):
        for name in REGISTRY:
            agent = get_agent(name)
            assert len(agent.system_prompt) > 0


class TestClassifyTask:
    def test_code_task(self):
        assert classify_task("напиши код для парсера") == "code"
        assert classify_task("python script") == "code"
        assert classify_task("создай функцию hello") == "code"

    def test_research_task(self):
        assert classify_task("найди информацию о Python") == "research"
        assert classify_task("проанализируй этот код") == "research"
        assert classify_task("что такое Docker") == "research"

    def test_file_task(self):
        assert classify_task("покажи файлы в папке") == "file_ops"
        assert classify_task("прочитай файл test.txt") == "file_ops"
        assert classify_task("создай папку data") == "file_ops"

    def test_default_task(self):
        assert classify_task("привет") == "orchestrator"
        assert classify_task("как дела") == "orchestrator"
