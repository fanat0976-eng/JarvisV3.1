"""End-to-end test: ingest → search → chat with RAG context."""
import pytest
import httpx

BASE_URL = "http://localhost:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


@pytest.mark.skip(reason="Requires running server on port 8003")
def test_full_rag_workflow():
    # 1. Ingest document
    doc = {
        "text": "Jarvis V3.1 uses ChromaDB for vector storage and Ollama nomic-embed-text for embeddings.",
        "metadata": {"source": "e2e_test", "topic": "rag"}
    }
    r = httpx.post(f"{BASE_URL}/rag/add", json=doc, headers=get_headers())
    assert r.status_code == 200
    
    # 2. Search for relevant content
    search = {"query": "vector storage embeddings", "n_results": 3}
    r = httpx.post(f"{BASE_URL}/rag/search", json=search, headers=get_headers())
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) > 0
    assert any("ChromaDB" in res["text"] for res in results)
    
    # 3. Ask question via RAG
    question = {"question": "What database does Jarvis use?"}
    r = httpx.post(f"{BASE_URL}/rag/ask", json=question, headers=get_headers())
    assert r.status_code == 200
    context = r.json()["context"]
    assert "ChromaDB" in context
    
    # 4. Chat with Brain (should use RAG context)
    chat = {"messages": [{"role": "user", "content": "Какую базу данных использует Jarvis?"}]}
    r = httpx.post(f"{BASE_URL}/brain/chat", json=chat, headers=get_headers())
    assert r.status_code == 200
    response = r.json()["reply"]
    assert "ChromaDB" in response or "chromadb" in response.lower()