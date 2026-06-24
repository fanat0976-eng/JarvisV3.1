"""Unit tests for Graph plugin."""
import sys
import os
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.graph.graph_engine import GraphEngine


class TestGraphEngine:
    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        conn = sqlite3.connect(self.tmp.name, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        from core.db import set_graph_conn
        set_graph_conn(conn)
        self.engine = GraphEngine(self.tmp.name)

    def teardown_method(self):
        from core.db import set_graph_conn
        old = set_graph_conn(None)
        if old:
            old.close()
        try:
            os.unlink(self.tmp.name)
        except PermissionError:
            pass

    def test_add_entity(self):
        result = self.engine.add_entity("user_badge", "user", "badge")
        assert result["id"] == "user_badge"
        assert result["type"] == "user"

    def test_add_relation(self):
        self.engine.add_entity("user_badge", "user", "badge")
        self.engine.add_entity("proj_jarvis", "project", "Jarvis")
        result = self.engine.add_relation("user_badge", "proj_jarvis", "works_on")
        assert result["source"] == "user_badge"
        assert result["relation"] == "works_on"

    def test_get_entity(self):
        self.engine.add_entity("test_id", "tool", "Python")
        entity = self.engine.get_entity("test_id")
        assert entity is not None
        assert entity["name"] == "Python"

    def test_get_entity_missing(self):
        entity = self.engine.get_entity("nonexistent")
        assert entity is None

    def test_neighbors(self):
        self.engine.add_entity("a", "x", "A")
        self.engine.add_entity("b", "x", "B")
        self.engine.add_entity("c", "x", "C")
        self.engine.add_relation("a", "b", "knows")
        self.engine.add_relation("b", "c", "knows")

        result = self.engine.neighbors("a", depth=1)
        assert len(result["neighbors"]) == 1
        assert result["neighbors"][0]["to"] == "b"

    def test_neighbors_depth2(self):
        self.engine.add_entity("a", "x", "A")
        self.engine.add_entity("b", "x", "B")
        self.engine.add_entity("c", "x", "C")
        self.engine.add_relation("a", "b", "knows")
        self.engine.add_relation("b", "c", "knows")

        result = self.engine.neighbors("a", depth=2)
        assert len(result["neighbors"]) == 2

    def test_shortest_path(self):
        self.engine.add_entity("a", "x", "A")
        self.engine.add_entity("b", "x", "B")
        self.engine.add_entity("c", "x", "C")
        self.engine.add_relation("a", "b", "knows")
        self.engine.add_relation("b", "c", "knows")

        result = self.engine.shortest_path("a", "c")
        assert result["length"] == 2
        assert result["path"] == ["a", "b", "c"]

    def test_no_path(self):
        self.engine.add_entity("a", "x", "A")
        self.engine.add_entity("b", "x", "B")
        result = self.engine.shortest_path("a", "b")
        assert result["length"] == 0

    def test_query(self):
        self.engine.add_entity("a", "user", "A")
        self.engine.add_entity("b", "project", "B")
        self.engine.add_relation("a", "b", "works_on")
        results = self.engine.query(relation_type="works_on")
        assert len(results) == 1

    def test_stats(self):
        self.engine.add_entity("a", "user", "A")
        self.engine.add_entity("b", "project", "B")
        self.engine.add_relation("a", "b", "works_on")
        stats = self.engine.stats()
        assert stats["entities"] == 2
        assert stats["relations"] == 1
