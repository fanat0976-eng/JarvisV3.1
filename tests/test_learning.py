"""Unit tests for Learning plugin."""
import sys
import os
import tempfile
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.learning.fact_extractor import extract_facts
from plugins.learning.command_learner import (
    suggest_command, get_learned_commands, detect_repeated_queries
)
from plugins.learning.router_learner import record_outcome, get_model_scores, get_best_model


class TestFactExtractor:
    def test_extract_project(self):
        facts = extract_facts("я работаю над Jarvis V3.1")
        assert len(facts) == 1
        assert facts[0]["category"] == "project"
        assert "jarvis" in facts[0]["value"].lower()

    def test_extract_tool(self):
        facts = extract_facts("я использую Python для парсинга")
        assert len(facts) == 1
        assert facts[0]["category"] == "tool"

    def test_extract_preference(self):
        facts = extract_facts("мне нравится краткие ответы")
        assert len(facts) == 1
        assert facts[0]["category"] == "preference"

    def test_extract_language(self):
        facts = extract_facts("я пишу на Rust")
        assert len(facts) == 1
        assert facts[0]["category"] == "language"

    def test_no_facts(self):
        facts = extract_facts("привет как дела")
        assert len(facts) == 0

    def test_multiple_facts(self):
        facts = extract_facts("я работаю над проектом и использую Python")
        assert len(facts) >= 1

    def test_clean_value(self):
        facts = extract_facts("я работаю над Jarvis V3.1!")
        assert len(facts) == 1
        assert "jarvis" in facts[0]["value"].lower()


class TestCommandLearner:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        conn = sqlite3.connect(self.tmp.name, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_key TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                last_seen TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                UNIQUE(pattern_type, pattern_key)
            );
            CREATE TABLE IF NOT EXISTS learned_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phrase TEXT UNIQUE NOT NULL,
                command TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            );
        """)
        from core.db import set_memory_conn
        set_memory_conn(conn)

    def teardown_method(self):
        from core.db import set_memory_conn
        old = set_memory_conn(None)
        if old:
            old.close()
        try:
            os.unlink(self.tmp.name)
        except PermissionError:
            pass

    def test_suggest_command(self):
        result = suggest_command("что по планам", "/plans")
        assert result["phrase"] == "что по планам"
        assert result["command"] == "/plans"

    def test_get_learned_commands(self):
        suggest_command("test phrase", "/test")
        cmds = get_learned_commands()
        assert len(cmds) == 1
        assert cmds[0]["phrase"] == "test phrase"

    def test_auto_command_name(self):
        result = suggest_command("покажи файлы")
        assert result["command"].startswith("/")

    def test_detect_repeated(self):
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        from core.db import get_memory_conn
        conn = get_memory_conn()
        for i in range(5):
            conn.execute(
                "INSERT OR REPLACE INTO patterns (pattern_type, pattern_key, count, first_seen, last_seen) "
                "VALUES ('keyword', 'проект', ?, ?, ?)",
                (i + 1, now, now)
            )
        conn.commit()
        candidates = detect_repeated_queries(threshold=3)
        assert len(candidates) >= 1
        assert candidates[0]["phrase"] == "проект"


class TestRouterLearner:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        conn = sqlite3.connect(self.tmp.name, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS model_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                task_type TEXT NOT NULL,
                successes INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                last_used TEXT NOT NULL,
                UNIQUE(model, task_type)
            );
        """)
        from core.db import set_memory_conn
        set_memory_conn(conn)

    def teardown_method(self):
        from core.db import set_memory_conn
        old = set_memory_conn(None)
        if old:
            old.close()
        try:
            os.unlink(self.tmp.name)
        except PermissionError:
            pass

    def test_record_success(self):
        record_outcome("gemma2:2b", "simple_chat", True)
        scores = get_model_scores()
        assert len(scores) == 1
        assert scores[0]["successes"] == 1

    def test_record_failure(self):
        record_outcome("gemma2:2b", "simple_chat", False)
        scores = get_model_scores()
        assert scores[0]["failures"] == 1

    def test_accumulate(self):
        for _ in range(3):
            record_outcome("qwen2.5:14b", "reasoning", True)
        record_outcome("qwen2.5:14b", "reasoning", False)
        scores = get_model_scores()
        assert scores[0]["successes"] == 3
        assert scores[0]["failures"] == 1

    def test_get_best_model(self):
        record_outcome("gemma2:2b", "simple_chat", True)
        record_outcome("gemma2:2b", "simple_chat", True)
        record_outcome("gemma2:2b", "simple_chat", True)
        record_outcome("qwen2.5:7b", "simple_chat", True)
        record_outcome("qwen2.5:7b", "simple_chat", False)
        best = get_best_model("simple_chat")
        assert best == "gemma2:2b"

    def test_best_model_none_when_insufficient(self):
        best = get_best_model("simple_chat")
        assert best is None
