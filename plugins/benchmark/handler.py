"""
Benchmark Plugin — System performance benchmark for Jarvis V3.1.
Tests: Ollama inference, embedding speed, RAG search, file I/O, memory ops.
"""
import os
import time
import httpx
import sqlite3
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = str(PROJECT_ROOT / "data")
DB_PATH = os.path.join(DATA_DIR, "memory.db")


def _bench_ollama_chat(iterations=3):
    """Benchmark Ollama chat inference."""
    try:
        times = []
        for _ in range(iterations):
            start = time.time()
            r = httpx.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "qwen2.5:7b",
                    "messages": [{"role": "user", "content": "Say hello in 5 words"}],
                    "stream": False,
                    "options": {"num_predict": 50},
                },
                timeout=60,
            )
            r.raise_for_status()
            times.append(time.time() - start)

        avg = sum(times) / len(times)
        tokens = r.json().get("eval_count", 0)
        return {
            "ok": True,
            "avg_ms": round(avg * 1000),
            "tokens_per_sec": round(tokens / avg, 1) if avg > 0 and tokens else 0,
            "iterations": iterations,
            "message": f"Ollama chat: {round(avg * 1000)}ms avg, {round(tokens / avg, 1) if avg > 0 else 0} tok/s",
        }
    except Exception as e:
        return {"ok": False, "message": f"Ollama chat: {e}"}


def _bench_ollama_embed():
    """Benchmark embedding speed."""
    try:
        texts = [f"Test sentence number {i} for embedding benchmark" for i in range(10)]
        start = time.time()
        r = httpx.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": texts[0]},
            timeout=30,
        )
        r.raise_for_status()
        elapsed = time.time() - start
        dim = len(r.json().get("embedding", []))
        return {
            "ok": True,
            "avg_ms": round(elapsed * 1000),
            "dimension": dim,
            "message": f"Embedding: {round(elapsed * 1000)}ms, dim={dim}",
        }
    except Exception as e:
        return {"ok": False, "message": f"Embedding: {e}"}


def _bench_rag_search():
    """Benchmark RAG search."""
    try:
        start = time.time()
        r = httpx.post(
            "http://localhost:8003/rag/search",
            json={"query": "Python", "n_results": 5},
            timeout=30,
            headers={"X-Auth-Key": "jarvis-v3.1"},
        )
        r.raise_for_status()
        elapsed = time.time() - start
        results = r.json().get("results", [])
        return {
            "ok": True,
            "avg_ms": round(elapsed * 1000),
            "results_count": len(results),
            "message": f"RAG search: {round(elapsed * 1000)}ms, {len(results)} results",
        }
    except Exception as e:
        return {"ok": False, "message": f"RAG search: {e}"}


def _bench_file_io():
    """Benchmark file I/O."""
    test_file = os.path.join(DATA_DIR, "_bench_test.txt")
    data = "x" * 1024 * 1024  # 1MB

    start = time.time()
    with open(test_file, "w") as f:
        f.write(data * 10)
    write_time = time.time() - start

    start = time.time()
    with open(test_file, "r") as f:
        f.read()
    read_time = time.time() - start

    os.remove(test_file)

    return {
        "ok": True,
        "write_ms": round(write_time * 1000),
        "read_ms": round(read_time * 1000),
        "message": f"File I/O: write {round(write_time * 1000)}ms, read {round(read_time * 1000)}ms (10MB)",
    }


def _bench_sqlite():
    """Benchmark SQLite operations."""
    test_db = os.path.join(DATA_DIR, "_bench_test.db")
    conn = sqlite3.connect(test_db)

    start = time.time()
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, key TEXT, value TEXT)")
    for i in range(1000):
        conn.execute("INSERT INTO test (key, value) VALUES (?, ?)", (f"key_{i}", f"value_{i}"))
    conn.commit()
    write_time = time.time() - start

    start = time.time()
    rows = conn.execute("SELECT * FROM test WHERE key LIKE 'key_5%'").fetchall()
    read_time = time.time() - start

    conn.close()
    os.remove(test_db)

    return {
        "ok": True,
        "write_ms": round(write_time * 1000),
        "read_ms": round(read_time * 1000),
        "rows_read": len(rows),
        "message": f"SQLite: write {round(write_time * 1000)}ms, read {round(read_time * 1000)}ms (1000 rows)",
    }


@router.get("/health")
def health():
    return {"status": "ok", "message": "Benchmark plugin loaded"}


@router.get("/run")
def run_benchmark():
    results = {}

    results["ollama_chat"] = _bench_ollama_chat()
    results["ollama_embed"] = _bench_ollama_embed()
    results["rag_search"] = _bench_rag_search()
    results["file_io"] = _bench_file_io()
    results["sqlite"] = _bench_sqlite()

    passed = sum(1 for v in results.values() if v.get("ok"))
    total = len(results)

    return {
        "status": "ok",
        "passed": passed,
        "total": total,
        "results": results,
    }


@router.get("/quick")
def quick_benchmark():
    """Fast benchmark — just file I/O and SQLite."""
    results = {}
    results["file_io"] = _bench_file_io()
    results["sqlite"] = _bench_sqlite()

    passed = sum(1 for v in results.values() if v.get("ok"))
    return {"status": "ok", "passed": passed, "total": len(results), "results": results}


def on_startup():
    print("  [benchmark] Initialized: system performance checker")


def on_shutdown():
    pass
