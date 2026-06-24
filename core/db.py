"""
Jarvis V3.1 — Shared Database Connections.
Single connection per DB, WAL mode, lifecycle managed by server.
"""
import os
import sqlite3
from pathlib import Path

DATA_DIR = str(Path(__file__).parent.parent / "data")
MEMORY_DB = os.path.join(DATA_DIR, "memory.db")
GRAPH_DB = os.path.join(DATA_DIR, "knowledge_graph.db")

_memory_conn: sqlite3.Connection | None = None
_graph_conn: sqlite3.Connection | None = None


def _open(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def get_memory_conn() -> sqlite3.Connection:
    global _memory_conn
    if _memory_conn is None:
        _memory_conn = _open(MEMORY_DB)
    return _memory_conn


def get_graph_conn() -> sqlite3.Connection:
    global _graph_conn
    if _graph_conn is None:
        _graph_conn = _open(GRAPH_DB)
    return _graph_conn


def set_memory_conn(conn: sqlite3.Connection) -> sqlite3.Connection | None:
    global _memory_conn
    old = _memory_conn
    _memory_conn = conn
    return old


def set_graph_conn(conn: sqlite3.Connection) -> sqlite3.Connection | None:
    global _graph_conn
    old = _graph_conn
    _graph_conn = conn
    return old


def close_all():
    global _memory_conn, _graph_conn
    for conn in (_memory_conn, _graph_conn):
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    _memory_conn = None
    _graph_conn = None
