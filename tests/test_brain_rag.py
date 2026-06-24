"""Tests for Brain + RAG integration."""
import pytest
import httpx

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


def get_client():
    return httpx.Client(trust_env=False, timeout=120)


@requires_server
def test_chat_with_rag_context():
    client = get_client()

    doc = {
        "text": "Jarvis V3.1 is an AI OS with plugins for brain, memory, RAG, and tools.",
        "metadata": {"source": "docs", "topic": "jarvis"}
    }
    client.post(f"{BASE_URL}/rag/add", json=doc, headers=get_headers())

    chat_msg = {"messages": [{"role": "user", "content": "Что такое Jarvis V3.1?"}]}
    r = client.post(f"{BASE_URL}/brain/chat", json=chat_msg, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data

    client.close()
