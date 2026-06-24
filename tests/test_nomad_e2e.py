"""End-to-end test for NOMAD Knowledge Pipeline."""
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
def test_nomad_e2e_workflow():
    # 1. Check Wikipedia status
    r = httpx.get(f"{BASE_URL}/nomad/sources/wikipedia/status", headers=get_headers())
    assert r.status_code == 200

    # 2. Start download
    r = httpx.post(
        f"{BASE_URL}/nomad/sources/wikipedia/download",
        json={"language": "ru"},
        headers=get_headers()
    )
    assert r.status_code == 200
    assert r.json()["status"] == "downloading"

    # 3. Ingest test file
    r = httpx.post(
        f"{BASE_URL}/nomad/ingest/text",
        json={"text": "Test knowledge entry", "metadata": {"source": "e2e"}},
        headers=get_headers()
    )
    assert r.status_code == 200

    # 4. Search for it
    r = httpx.post(
        f"{BASE_URL}/rag/search",
        json={"query": "test knowledge", "n_results": 1},
        headers=get_headers()
    )
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0
