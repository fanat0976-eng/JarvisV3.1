"""Unit tests — no server required."""
import sys
import os
import tempfile
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.brain.router import BrainRouter, TaskType
from plugins.brain.tool_executor import parse_tool_calls, execute_tool_call, TOOL_DEFINITIONS
from plugins.brain.personality import PersonalityEngine, _tokenize, _fact_relevance


# ── Router ──

class TestRouter:
    def setup_method(self):
        self.router = BrainRouter()

    def test_simple_chat(self):
        assert self.router.classify("привет") == TaskType.SIMPLE_CHAT
        assert self.router.classify("как дела?") == TaskType.SIMPLE_CHAT

    def test_code_gen(self):
        assert self.router.classify("напиши код для парсера") == TaskType.CODE_GEN
        assert self.router.classify("def hello():") == TaskType.CODE_GEN
        assert self.router.classify("python script") == TaskType.CODE_GEN

    def test_reasoning(self):
        assert self.router.classify("объясни как работает TCP") == TaskType.REASONING
        assert self.router.classify("почему это не работает") == TaskType.REASONING

    def test_extraction(self):
        assert self.router.classify("запомни что я работаю над проектом") == TaskType.EXTRACTION
        assert self.router.classify("извлеки факты") == TaskType.EXTRACTION

    def test_analysis(self):
        assert self.router.classify("сводка по встрече") == TaskType.ANALYSIS
        assert self.router.classify("итог дня") == TaskType.ANALYSIS

    def test_route_returns_required_keys(self):
        route = self.router.route("привет")
        assert "model" in route
        assert "task_type" in route
        assert "temperature" in route

    def test_different_models_per_task(self):
        simple = self.router.route("привет")
        code = self.router.route("напиши код")
        assert simple["model"] != code["model"]

    def test_temperature_ranges(self):
        for task_type in TaskType:
            route = self.router.route(f"test {task_type.value}")
            assert 0.0 <= route["temperature"] <= 1.0


# ── Tool Executor ──

class TestToolExecutor:
    def test_parse_tool_calls_empty(self):
        assert parse_tool_calls("no tools here") == []

    def test_parse_tool_calls_single(self):
        text = "result\n<<<TOOL_CALL>>>\ntool: files/ls\npath: /tmp\n<<<END_TOOL_CALL>>>"
        calls = parse_tool_calls(text)
        assert len(calls) == 1
        assert "files/ls" in calls[0]

    def test_parse_tool_calls_multiple(self):
        text = (
            "<<<TOOL_CALL>>>\ntool: files/ls\n<<<END_TOOL_CALL>>>"
            "middle"
            "<<<TOOL_CALL>>>\ntool: files/read\npath: /tmp/test.txt\n<<<END_TOOL_CALL>>>"
        )
        calls = parse_tool_calls(text)
        assert len(calls) == 2

    def test_execute_files_ls(self):
        result = execute_tool_call("tool: files/ls\npath: C:\\Users\\badge\\JarvisV3.1\\workspace")
        assert result["status"] == "ok"
        assert "items" in result

    def test_execute_files_ls_default_path(self):
        result = execute_tool_call("tool: files/ls")
        assert result["status"] == "ok"

    def test_execute_unknown_tool(self):
        result = execute_tool_call("tool: nonexistent/tool")
        assert result["status"] == "error"

    def test_execute_memory_remember_no_engine(self):
        result = execute_tool_call("tool: memory/remember\nkey: name\nvalue: badge")
        assert result["status"] == "error"

    def test_tool_definitions_complete(self):
        assert "files/ls" in TOOL_DEFINITIONS
        assert "files/read" in TOOL_DEFINITIONS
        assert "memory/remember" in TOOL_DEFINITIONS


# ── Personality ──

class TestPersonality:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY,
                entity TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                UNIQUE(entity, key)
            );
        """)
        from core.db import set_memory_conn
        set_memory_conn(conn)
        self.personality = PersonalityEngine(self.db_path)

    def teardown_method(self):
        from core.db import set_memory_conn
        conn = set_memory_conn(None)
        if conn:
            conn.close()
        try:
            os.unlink(self.db_path)
        except PermissionError:
            pass

    def test_build_system_prompt_base(self):
        prompt = self.personality.build_system_prompt()
        assert "Jarvis" in prompt

    def test_build_system_prompt_ru(self):
        prompt = self.personality.build_system_prompt(query="Привет")
        assert "Jarvis" in prompt
        assert "ПРАВИЛА ОБЩЕНИЯ" in prompt or "COMMUNICATION RULES" in prompt

    def test_extract_and_recall_preference(self):
        self.personality.extract_user_preference("name", "badge")
        facts = self.personality.get_user_facts("user")
        assert len(facts) == 1
        assert facts[0]["key"] == "name"
        assert facts[0]["value"] == "badge"

    def test_upsert_preference(self):
        self.personality.extract_user_preference("name", "badge")
        self.personality.extract_user_preference("name", "new_name")
        facts = self.personality.get_user_facts("user")
        assert len(facts) == 1
        assert facts[0]["value"] == "new_name"

    def test_prompt_includes_user_facts(self):
        self.personality.extract_user_preference("lang", "python")
        prompt = self.personality.build_system_prompt()
        assert "python" in prompt

    def test_get_project_facts_empty(self):
        facts = self.personality.get_project_facts()
        assert facts == []

    def test_tokenize(self):
        tokens = _tokenize("напиши код для парсера")
        assert "код" in tokens
        assert "парсера" in tokens
        assert "напиши" not in tokens

    def test_fact_relevance_high(self):
        fact = {"key": "lang", "value": "python", "confidence": 1.0, "access_count": 5}
        score = _fact_relevance(fact, {"python", "код"})
        assert score > 0.3

    def test_fact_relevance_low(self):
        fact = {"key": "name", "value": "badge", "confidence": 1.0, "access_count": 5}
        score = _fact_relevance(fact, {"python", "код"})
        assert score < 0.4

    def test_build_system_prompt_with_query(self):
        self.personality.extract_user_preference("lang", "python")
        self.personality.extract_user_preference("name", "badge")
        prompt = self.personality.build_system_prompt(query="напиши python код")
        assert "python" in prompt


class TestLanguageDetection:
    def test_detect_russian(self):
        from core.language import detect_language
        assert detect_language("Привет, как дела?") == "ru"
        assert detect_language("Покажи мне файлы") == "ru"
        assert detect_language("Что ты умеешь?") == "ru"

    def test_detect_english(self):
        from core.language import detect_language
        assert detect_language("Hello, how are you?") == "en"
        assert detect_language("Show me the files") == "en"
        assert detect_language("What can you do?") == "en"

    def test_detect_empty(self):
        from core.language import detect_language
        assert detect_language("") == "en"
        assert detect_language("   ") == "en"

    def test_get_system_prompt(self):
        from core.language import get_system_prompt
        ru = get_system_prompt("ru")
        en = get_system_prompt("en")
        assert "Jarvis" in ru
        assert "Jarvis" in en
        assert "ПРАВИЛА" in ru
        assert "RULES" in en

    def test_get_greeting(self):
        from core.language import get_greeting
        assert "Привет" in get_greeting("ru")
        assert "Hello" in get_greeting("en")

    def test_supported_languages(self):
        from core.language import get_supported_languages
        langs = get_supported_languages()
        codes = [l["code"] for l in langs]
        assert "ru" in codes
        assert "en" in codes
        assert "kz" in codes
