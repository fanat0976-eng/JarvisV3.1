# NOMAD Knowledge Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend NOMAD plugin with Wikipedia ZIM adapter for ingesting Russian Wikipedia into RAG.

**Architecture:** Add source-specific adapters to NOMAD plugin. Each adapter handles download, parse, chunk, and ingest for a specific content format. Wikipedia adapter uses libzim for ZIM file parsing.

**Tech Stack:** Python 3.10+, libzim, beautifulsoup4, lxml, httpx

---

## Task 1: Create Text Chunker

**Covers:** [S5] Chunking Strategy

**Files:**
- Create: `plugins/nomad/chunker.py`
- Create: `tests/test_chunker.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for text chunker."""
import pytest
from plugins.nomad.chunker import chunk_text


def test_chunk_text_basic():
    text = "A" * 2000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 0
    assert all(len(c) <= 600 for c in chunks)


def test_chunk_text_small():
    text = "Short text"
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_overlap():
    text = "A" * 1000
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_chunker.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'plugins.nomad.chunker'"

- [ ] **Step 3: Write minimal implementation**

```python
# plugins/nomad/chunker.py
"""Text chunking utilities for NOMAD pipeline."""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: Input text
        chunk_size: Approximate number of characters per chunk
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    
    return chunks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_chunker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/nomad/chunker.py tests/test_chunker.py
git commit -m "feat: add text chunker for NOMAD pipeline"
```

---

## Task 2: Create Pipeline Orchestrator

**Covers:** [S2] Solution Overview, [S7] Error Handling

**Files:**
- Create: `plugins/nomad/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for pipeline orchestrator."""
import pytest
from plugins.nomad.pipeline import Pipeline


def test_pipeline_status():
    pipeline = Pipeline("test_source")
    status = pipeline.get_status()
    assert status["source"] == "test_source"
    assert status["status"] == "idle"


def test_pipeline_update_status():
    pipeline = Pipeline("test_source")
    pipeline.update_status("downloading", progress=50)
    status = pipeline.get_status()
    assert status["status"] == "downloading"
    assert status["progress"] == 50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_pipeline.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal implementation**

```python
# plugins/nomad/pipeline.py
"""Pipeline orchestration for NOMAD sources."""
import json
from pathlib import Path
from datetime import datetime


class Pipeline:
    def __init__(self, source_name: str, data_dir: str = "data/knowledge"):
        self.source_name = source_name
        self.data_dir = Path(data_dir) / source_name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.data_dir / "status.json"
    
    def get_status(self) -> dict:
        """Get current pipeline status."""
        if self.status_file.exists():
            with open(self.status_file) as f:
                return json.load(f)
        return {
            "source": self.source_name,
            "status": "idle",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def update_status(self, status: str, **kwargs):
        """Update pipeline status."""
        current = self.get_status()
        current["status"] = status
        current["updated_at"] = datetime.utcnow().isoformat()
        current.update(kwargs)
        with open(self.status_file, "w") as f:
            json.dump(current, f, indent=2)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_pipeline.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/nomad/pipeline.py tests/test_pipeline.py
git commit -m "feat: add pipeline orchestrator for NOMAD sources"
```

---

## Task 3: Create Wikipedia Adapter - Download

**Covers:** [S3] Wikipedia ZIM Adapter, [S6] Dependencies

**Files:**
- Create: `plugins/nomad/sources/__init__.py`
- Create: `plugins/nomad/sources/wikipedia.py`
- Create: `tests/test_wikipedia.py`

- [ ] **Step 1: Create sources directory**

```bash
mkdir -p plugins/nomad/sources
touch plugins/nomad/sources/__init__.py
```

- [ ] **Step 2: Write failing test**

```python
"""Tests for Wikipedia adapter."""
import pytest
from plugins.nomad.sources.wikipedia import WikipediaAdapter


def test_wikipedia_adapter_init():
    adapter = WikipediaAdapter()
    assert adapter.language == "ru"
    assert adapter.mirror == "auto"


def test_wikipedia_get_mirror():
    adapter = WikipediaAdapter(language="ru")
    mirror = adapter.get_mirror()
    assert mirror.startswith("https://")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_wikipedia.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 4: Write minimal implementation**

```python
# plugins/nomad/sources/wikipedia.py
"""Wikipedia ZIM adapter for NOMAD pipeline."""
import os
import httpx
from pathlib import Path
from ..pipeline import Pipeline
from ..chunker import chunk_text


class WikipediaAdapter:
    def __init__(self, language: str = "ru", mirror: str = "auto"):
        self.language = language
        self.mirror = mirror
        self.pipeline = Pipeline(f"wikipedia_{language}")
        self.mirrors = [
            "https://mirror.clarkson.edu/wikipedia/",
            "https://ftp.acc.umu.se/mirror/wikimedia.org/wikipedia/",
            "https://dumps.wikimedia.org/wikipedia/",
        ]
    
    def get_mirror(self) -> str:
        """Get available mirror URL."""
        if self.mirror == "auto":
            for mirror in self.mirrors:
                try:
                    r = httpx.head(mirror, timeout=5)
                    if r.status_code == 200:
                        return mirror
                except Exception:
                    continue
            return self.mirrors[0]
        return self.mirror
    
    def get_zim_url(self) -> str:
        """Get ZIM file URL for download."""
        mirror = self.get_mirror()
        return f"{mirror}{self.language}wiki/latest/{self.language}wiki-latestArticles_expert.zim"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_wikipedia.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add plugins/nomad/sources/ tests/test_wikipedia.py
git commit -m "feat: add Wikipedia adapter with mirror selection"
```

---

## Task 4: Wikipedia Adapter - Process

**Covers:** [S3] Wikipedia ZIM Adapter, [S5] Chunking Strategy

**Files:**
- Modify: `plugins/nomad/sources/wikipedia.py`
- Modify: `tests/test_wikipedia.py`

- [ ] **Step 1: Write failing test**

```python
def test_wikipedia_parse_article():
    adapter = WikipediaAdapter()
    html = "<html><body><h1>Test</h1><p>Article content here.</p></body></html>"
    text = adapter.parse_article(html)
    assert "Test" in text
    assert "Article content here" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_wikipedia.py::test_wikipedia_parse_article -v`
Expected: FAIL with "AttributeError: 'WikipediaAdapter' object has no attribute 'parse_article'"

- [ ] **Step 3: Write minimal implementation**

Add to `plugins/nomad/sources/wikipedia.py`:

```python
from bs4 import BeautifulSoup


class WikipediaAdapter:
    # ... existing code ...
    
    def parse_article(self, html: str) -> str:
        """Parse HTML article to clean text."""
        soup = BeautifulSoup(html, "lxml")
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer"]):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_wikipedia.py::test_wikipedia_parse_article -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/nomad/sources/wikipedia.py tests/test_wikipedia.py
git commit -m "feat: add article parsing to Wikipedia adapter"
```

---

## Task 5: Wikipedia Adapter - Ingest

**Covers:** [S3] Wikipedia ZIM Adapter, [S4] API Endpoints

**Files:**
- Modify: `plugins/nomad/sources/wikipedia.py`
- Modify: `plugins/nomad/handler.py`

- [ ] **Step 1: Write failing test**

```python
def test_wikipedia_chunk_article():
    adapter = WikipediaAdapter()
    text = "A" * 2000
    chunks = adapter.chunk_article(text, title="Test", url="http://test.com")
    assert len(chunks) > 0
    assert chunks[0]["title"] == "Test"
    assert chunks[0]["source"] == "wikipedia"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_wikipedia.py::test_wikipedia_chunk_article -v`
Expected: FAIL with "AttributeError"

- [ ] **Step 3: Write minimal implementation**

Add to `plugins/nomad/sources/wikipedia.py`:

```python
class WikipediaAdapter:
    # ... existing code ...
    
    def chunk_article(self, text: str, title: str, url: str) -> list[dict]:
        """Chunk article text with metadata."""
        chunks = chunk_text(text, chunk_size=2000, overlap=200)
        return [
            {
                "text": chunk,
                "metadata": {
                    "source": "wikipedia",
                    "language": self.language,
                    "title": title,
                    "url": url,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            }
            for i, chunk in enumerate(chunks)
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_wikipedia.py::test_wikipedia_chunk_article -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/nomad/sources/wikipedia.py
git commit -m "feat: add article chunking to Wikipedia adapter"
```

---

## Task 6: Update NOMAD Handler with Wikipedia Endpoints

**Covers:** [S4] API Endpoints

**Files:**
- Modify: `plugins/nomad/handler.py`
- Create: `tests/test_nomad_wikipedia.py`

- [ ] **Step 1: Write failing test**

```python
"""Tests for NOMAD Wikipedia endpoints."""
import pytest
import httpx

BASE_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


def test_wikipedia_status():
    r = httpx.get(f"{BASE_URL}/nomad/sources/wikipedia/status", headers=get_headers())
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_nomad_wikipedia.py -v`
Expected: FAIL with 404 (endpoint not found)

- [ ] **Step 3: Write minimal implementation**

Add to `plugins/nomad/handler.py`:

```python
from .sources.wikipedia import WikipediaAdapter

# Wikipedia adapter instance
wiki_adapter = WikipediaAdapter()


@router.get("/sources/wikipedia/status")
async def wikipedia_status():
    """Get Wikipedia download/processing status."""
    return wiki_adapter.pipeline.get_status()


@router.post("/sources/wikipedia/download")
async def wikipedia_download(request: Request):
    """Start downloading Wikipedia ZIM."""
    data = await request.json()
    language = data.get("language", "ru")
    
    # Update adapter language
    wiki_adapter.language = language
    
    # Start download in background
    # For now, just return status
    return {
        "status": "downloading",
        "language": language,
        "url": wiki_adapter.get_zim_url()
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_nomad_wikipedia.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/nomad/handler.py tests/test_nomad_wikipedia.py
git commit -m "feat: add Wikipedia status and download endpoints"
```

---

## Task 7: End-to-End Test

**Covers:** [S8] Testing

**Files:**
- Create: `tests/test_nomad_e2e.py`

- [ ] **Step 1: Write E2E test**

```python
"""End-to-end test for NOMAD Knowledge Pipeline."""
import pytest
import httpx

BASE_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"


def get_headers():
    return {"X-Auth-Key": AUTH_KEY}


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
```

- [ ] **Step 2: Run E2E test**

Run: `cd C:\Users\badge\JarvisV3.1 && python -m pytest tests/test_nomad_e2e.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_nomad_e2e.py
git commit -m "test: add E2E test for NOMAD Knowledge Pipeline"
```

---

## Summary

After completing all tasks:
1. Text chunker for splitting content into RAG-ready chunks
2. Pipeline orchestrator for managing source status
3. Wikipedia adapter with mirror selection, article parsing, and chunking
4. API endpoints for Wikipedia status and download
5. End-to-end test verifying the full workflow

**Next steps (future tasks):**
- Implement actual ZIM file download (background task)
- Add libzim dependency and implement ZIM parsing
- Process Wikipedia articles and ingest into RAG
- Add StackOverflow adapter
- Add Python/Rust docs adapter