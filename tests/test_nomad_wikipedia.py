"""Tests for NOMAD Wikipedia endpoints."""
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


@requires_server
def test_wikipedia_status():
    r = httpx.get(f"{BASE_URL}/nomad/sources/wikipedia/status", headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "status" in data


@requires_server
def test_wikipedia_download():
    r = httpx.post(
        f"{BASE_URL}/nomad/sources/wikipedia/download",
        json={"language": "ru"},
        headers=get_headers()
    )
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "language" in data
    assert data["language"] == "ru"
    assert "url" in data
