"""Tests for NOMAD Knowledge Pipeline."""
import pytest
import httpx
import tempfile
import os

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
def test_ingest_text():
    data = {
        "text": "NOMAD is the knowledge pipeline for Jarvis V3.1.",
        "metadata": {"source": "test", "topic": "nomad"}
    }
    r = httpx.post(f"{BASE_URL}/nomad/ingest/text", json=data, headers=get_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@requires_server
def test_ingest_file():
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document for NOMAD ingestion.")
        temp_path = f.name
    
    try:
        r = httpx.post(
            f"{BASE_URL}/nomad/ingest/file",
            json={"path": temp_path},
            headers=get_headers()
        )
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
    finally:
        os.unlink(temp_path)