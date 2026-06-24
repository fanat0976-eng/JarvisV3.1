# RAG Enable + Brain Integration + NOMAD Knowledge Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable RAG in Jarvis V3.1, integrate with Brain for context-aware responses, and start NOMAD Knowledge pipeline for content ingestion.

**Architecture:** RAG plugin already exists with ChromaDB + Ollama nomic-embed-text. Need to: (1) verify it works, (2) add RAG context retrieval to Brain's chat flow, (3) build content ingestion pipeline for Wikipedia/StackOverflow/docs.

**Tech Stack:** ChromaDB, Ollama (nomic-embed-text), FastAPI, Python 3.10+

---

## Task 1: Test RAG Endpoints

**Covers:** Verify RAG plugin functionality

**Files:**
- Create: `tests/test_rag.py`
- Modify: `plugins/rag/handler.py` (if bugs found)

- [ ] **Step 1: Create test file**

```python
"""Tests for RAG plugin endpoints."""
import pytest
import httpx
import time

BASE_URL = "http://localhost:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


def test_rag_health():
    r = httpx.get(f"{BASE_URL}/rag/health", headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "documents" in data
    assert "model_available" in data


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


def test_rag_search():
    query = {"query": "Python programming", "n_results": 3}
    r = httpx.post(f"{BASE_URL}/rag/search", json=query, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert "total" in data


def test_rag_ask():
    question = {"question": "What is Python?", "n_context": 2}
    r = httpx.post(f"{BASE_URL}/rag/ask", json=question, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "context" in data
    assert "sources" in data


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
```

- [ ] **Step 2: Run tests**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_rag.py -v`
Expected: Tests may fail if server not running or ChromaDB not initialized

- [ ] **Step 3: Start server and re-run tests**

Run: `cd C:\Users\badge\JarvisV3.1 && python core/server.py`
Then in another terminal: `python -m pytest tests/test_rag.py -v`
Expected: All tests PASS

- [ ] **Step 4: Fix any bugs found**

If tests fail, fix issues in `plugins/rag/handler.py`

- [ ] **Step 5: Commit**

```bash
git add tests/test_rag.py
git commit -m "test: add RAG endpoint tests"
```

---

## Task 2: Integrate RAG with Brain

**Covers:** Brain uses RAG context for responses

**Files:**
- Modify: `plugins/brain/handler.py` (add RAG context retrieval)
- Modify: `plugins/brain/router.py` (add RAG retrieval step)
- Create: `tests/test_brain_rag.py`

- [ ] **Step 1: Create test for Brain+RAG integration**

```python
"""Tests for Brain + RAG integration."""
import pytest
import httpx

BASE_URL = "http://localhost:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


def test_chat_with_rag_context():
    # First, ensure there's data in RAG
    doc = {
        "text": "Jarvis V3.1 is an AI OS with plugins for brain, memory, RAG, and tools.",
        "metadata": {"source": "docs", "topic": "jarvis"}
    }
    httpx.post(f"{BASE_URL}/rag/add", json=doc, headers=get_headers())
    
    # Now chat and verify RAG context is used
    chat_msg = {"message": "Что такое Jarvis V3.1?"}
    r = httpx.post(f"{BASE_URL}/brain/chat", json=chat_msg, headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    # Response should mention Jarvis V3.1 if RAG context was used
    assert "Jarvis" in data["response"] or "jarvis" in data["response"].lower()
```

- [ ] **Step 2: Modify Brain handler to use RAG**

In `plugins/brain/handler.py`, add RAG context retrieval before generating response:

```python
# Add at top of file
import httpx

# Add helper function
def get_rag_context(query: str, n_results: int = 3) -> str:
    """Retrieve relevant context from RAG."""
    try:
        r = httpx.post(
            "http://localhost:8003/rag/ask",
            json={"question": query, "n_context": n_results},
            headers={"X-Auth-Key": "jarvis-v3.1"},
            timeout=5
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("context", "")
    except Exception:
        pass
    return ""


# Modify chat endpoint to include RAG context
# In the chat function, before calling Ollama:
# rag_context = get_rag_context(message)
# if rag_context:
#     system_prompt += f"\n\nRelevant knowledge:\n{rag_context}"
```

- [ ] **Step 3: Run integration tests**

Run: `python -m pytest tests/test_brain_rag.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add plugins/brain/handler.py tests/test_brain_rag.py
git commit -m "feat: integrate RAG context into Brain chat"
```

---

## Task 3: NOMAD Knowledge Pipeline - Basic

**Covers:** Content ingestion into RAG

**Files:**
- Create: `plugins/nomad/__init__.py`
- Create: `plugins/nomad/handler.py`
- Create: `tests/test_nomad.py`

- [ ] **Step 1: Create NOMAD plugin structure**

```python
# plugins/nomad/__init__.py
# Empty init file
```

```python
# plugins/nomad/handler.py
"""
NOMAD Knowledge Pipeline - Content ingestion for RAG.
"""
import os
import httpx
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

BASE_URL = "http://localhost:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


@router.post("/ingest/file")
async def ingest_file(request: Request):
    """Ingest a single file into RAG."""
    data = await request.json()
    filepath = data.get("path", "")
    
    if not filepath or not os.path.exists(filepath):
        return JSONResponse({"error": f"File not found: {filepath}"}, status_code=404)
    
    try:
        # Use RAG's index_file endpoint
        r = httpx.post(
            f"{BASE_URL}/rag/index_file",
            json={"path": filepath},
            headers=get_headers(),
            timeout=60
        )
        return r.json()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/ingest/text")
async def ingest_text(request: Request):
    """Ingest raw text into RAG."""
    data = await request.json()
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    
    if not text:
        return JSONResponse({"error": "No text provided"}, status_code=400)
    
    try:
        r = httpx.post(
            f"{BASE_URL}/rag/add",
            json={"text": text, "metadata": metadata},
            headers=get_headers()
        )
        return r.json()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/ingest/directory")
async def ingest_directory(request: Request):
    """Ingest all files in a directory into RAG."""
    data = await request.json()
    dirpath = data.get("path", "")
    extensions = data.get("extensions", [".txt", ".md", ".py", ".json"])
    
    if not dirpath or not os.path.isdir(dirpath):
        return JSONResponse({"error": f"Directory not found: {dirpath}"}, status_code=404)
    
    results = []
    for ext in extensions:
        for filepath in Path(dirpath).rglob(f"*{ext}"):
            try:
                r = httpx.post(
                    f"{BASE_URL}/rag/index_file",
                    json={"path": str(filepath)},
                    headers=get_headers(),
                    timeout=60
                )
                results.append({"file": str(filepath), "status": r.json()})
            except Exception as e:
                results.append({"file": str(filepath), "error": str(e)})
    
    return {"status": "ok", "processed": len(results), "results": results}
```

- [ ] **Step 2: Create test file**

```python
# tests/test_nomad.py
"""Tests for NOMAD Knowledge Pipeline."""
import pytest
import httpx
import tempfile
import os

BASE_URL = "http://localhost:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


def test_ingest_text():
    data = {
        "text": "NOMAD is the knowledge pipeline for Jarvis V3.1.",
        "metadata": {"source": "test", "topic": "nomad"}
    }
    r = httpx.post(f"{BASE_URL}/nomad/ingest/text", json=data, headers=get_headers())
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


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
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_nomad.py -v`
Expected: PASS (after server restart)

- [ ] **Step 4: Commit**

```bash
git add plugins/nomad/ tests/test_nomad.py
git commit -m "feat: add NOMAD Knowledge Pipeline plugin"
```

---

## Task 4: Enable NOMAD in config.yaml

**Covers:** Configuration update

**Files:**
- Modify: `core/config.yaml`

- [ ] **Step 1: Add NOMAD plugin to config**

Add to `core/config.yaml` under plugins:

```yaml
  nomad:
    enabled: true
    description: "NOMAD Knowledge Pipeline - content ingestion for RAG"
```

- [ ] **Step 2: Verify server loads NOMAD**

Run: `python core/server.py`
Expected: Server starts, NOMAD plugin listed in loaded plugins

- [ ] **Step 3: Commit**

```bash
git add core/config.yaml
git commit -m "config: enable NOMAD Knowledge Pipeline plugin"
```

---

## Task 5: Create Sample Knowledge Base

**Covers:** Initial content for RAG

**Files:**
- Create: `data/knowledge/README.md`
- Create: `data/knowledge/jarvis_v3.1.md`
- Create: `data/knowledge/nasti_core.md`

- [ ] **Step 1: Create knowledge directory and docs**

```markdown
# data/knowledge/README.md
# Jarvis V3.1 Knowledge Base

This directory contains documents for RAG ingestion.

## Adding Content

1. Place .txt, .md, .py, or .json files here
2. Use NOMAD pipeline to ingest: POST /nomad/ingest/directory
3. Or ingest single files: POST /nomad/ingest/file
```

```markdown
# data/knowledge/jarvis_v3.1.md
# Jarvis V3.1 - AI OS

Jarvis V3.1 is an AI Operating System with the following components:

## Core
- FastAPI server on port 8003
- Plugin system with auto-discovery
- EventBus for inter-plugin communication
- TTL Cache

## Brain Plugin
- Router: routes tasks to appropriate models
- Context: sliding window management
- Personality: adaptive system prompts
- Tool Executor: executes tool calls

## Memory V2 Plugin
- Facts extraction and storage
- Entity linking
- Session management
- Pattern learning

## RAG Plugin
- ChromaDB vector storage
- Ollama embeddings (nomic-embed-text)
- File indexing (txt, md, pdf, docx)
- Semantic search

## Other Plugins
- Files: file operations
- Web: DuckDuckGo search
- TTS: edge-tts (Dmitry, Svetlana voices)
- STT: Whisper speech-to-text
- Notifications: system notifications
- Watchers: disk/network monitoring
- Android: WebSocket bridge
```

```markdown
# data/knowledge/nasti_core.md
# nasti-core - Shared Library

nasti-core is a shared Python library for all Nasti AI projects.

## Modules

### ai
- Ollama API wrappers (sync/stream/async)
- LiteLLM integration

### event
- EventBus with wildcard subscriptions
- Thread-safe publish/subscribe

### cache
- TTLCache with lazy eviction
- Time-based expiration

### crypto
- Argon2id key derivation
- XChaCha20-Poly1305 encryption
- BLAKE2b HMAC
- Binary header format (79 bytes)

### rag
- RAGEngine (ChromaDB + SentenceTransformer)
- Document ingestion and retrieval

### osint
- detect_target_type (regex cascade)
- run_wsl (WSL command execution)
- TOOL_REGISTRY (18+ tools)

## Usage
```python
from nasti_core.ai.ollama import OllamaClient
from nasti_core.event.bus import EventBus
from nasti_core.cache.ttl import TTLCache
```
```

- [ ] **Step 2: Ingest knowledge base**

Run: `curl -X POST http://localhost:8003/nomad/ingest/directory -H "Content-Type: application/json" -H "X-Auth-Key: jarvis-v3.1" -d '{"path": "data/knowledge", "extensions": [".md", ".txt"]}'`

Expected: All files ingested into RAG

- [ ] **Step 3: Commit**

```bash
git add data/knowledge/
git commit -m "docs: add initial knowledge base for RAG"
```

---

## Task 6: End-to-End Test

**Covers:** Full workflow verification

**Files:**
- Create: `tests/test_e2e_rag.py`

- [ ] **Step 1: Create end-to-end test**

```python
# tests/test_e2e_rag.py
"""End-to-end test: ingest → search → chat with RAG context."""
import pytest
import httpx

BASE_URL = "http://localhost:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


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
    chat = {"message": "Какую базу данных использует Jarvis?"}
    r = httpx.post(f"{BASE_URL}/brain/chat", json=chat, headers=get_headers())
    assert r.status_code == 200
    response = r.json()["response"]
    assert "ChromaDB" in response or "chromadb" in response.lower()
```

- [ ] **Step 2: Run end-to-end test**

Run: `python -m pytest tests/test_e2e_rag.py -v`
Expected: PASS

- [ ] **Step 3: Final commit**

```bash
git add tests/test_e2e_rag.py
git commit -m "test: add end-to-end RAG workflow test"
```

---

## Summary

After completing all tasks:
1. RAG plugin tested and working
2. Brain integrates RAG context for responses
3. NOMAD Knowledge Pipeline ready for content ingestion
4. Sample knowledge base created
5. End-to-end workflow verified

**Next steps (future tasks):**
- Ingest Wikipedia ZIM files
- Ingest StackOverflow data
- Ingest Python/Rust documentation
- Build web UI for knowledge management