"""Tests for RAG plugin endpoints."""
import pytest
import httpx
import time

BASE_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"


def _server_available():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


requires_server = pytest.mark.skipif(not _server_available(), reason="Server not running")


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


@requires_server
def test_rag_health():
    r = httpx.get(f"{BASE_URL}/rag/health", headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "documents" in data
    assert "model_available" in data


@requires_server
def test_rag_add_document():
    doc = {
        "text": "Python is a programming language created by Guido van Rossum.",
        "metadata": {"source": "test", "topic": "python"},
        "id": f"test_doc_{int(time.time())}"
    }
    r = httpx.post(f"{BASE_URL}/rag/add", json=doc, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "id" in data


@requires_server
def test_rag_search():
    query = {"query": "Python programming", "n_results": 3}
    r = httpx.post(f"{BASE_URL}/rag/search", json=query, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert "total" in data


@requires_server
def test_rag_ask():
    question = {"question": "What is Python?", "n_context": 2}
    r = httpx.post(f"{BASE_URL}/rag/ask", json=question, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "context" in data
    assert "sources" in data


@requires_server
def test_rag_add_batch():
    docs = {
        "documents": [
            {"text": "FastAPI is a modern web framework for Python.", "metadata": {"source": "test"}},
            {"text": "ChromaDB is a vector database for embeddings.", "metadata": {"source": "test"}}
        ]
    }
    r = httpx.post(f"{BASE_URL}/rag/add_batch", json=docs, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["added"] == 2


@requires_server
def test_rag_delete():
    doc = {
        "text": "This document will be deleted.",
        "metadata": {"source": "test"},
        "id": f"delete_me_{int(time.time())}"
    }
    r = httpx.post(f"{BASE_URL}/rag/add", json=doc, headers=get_headers())
    assert r.status_code == 200
    doc_id = r.json()["id"]

    r = httpx.post(f"{BASE_URL}/rag/delete", json={"id": doc_id}, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["deleted"] == doc_id


@requires_server
def test_rag_index_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is test content for file indexing. FastAPI makes building APIs easy.", encoding="utf-8")

    r = httpx.post(
        f"{BASE_URL}/rag/index_file",
        json={"path": str(test_file), "chunk_size": 50, "overlap": 10},
        headers=get_headers()
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["chunks_added"] >= 1
