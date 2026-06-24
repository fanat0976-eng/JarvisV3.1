---
feature: ZIM Loader
status: delivered
specs:
  - docs/compose/specs/2026-06-22-zim-loader-design.md
plans:
  - docs/compose/plans/2026-06-22-zim-loader.md
---

# ZIM Loader — Final Report

## What Was Built

ZIM loader pipeline for downloading and ingesting Kiwix ZIM files into RAG. The system supports any ZIM file from Project N.O.M.A.D. collections, including Medicine, Survival, Education, DIY, Agriculture, and Computing categories.

The pipeline provides a complete workflow: download ZIM files from Kiwix servers → parse ZIM archives using libzim → extract articles → chunk text → load into RAG via ChromaDB + Ollama embeddings.

## Architecture

### Components

1. **ZimAdapter** (`plugins/nomad/sources/zim.py`)
   - `download_from_kiwix(url)` — Download ZIM files from Kiwix servers
   - `parse_zim(zim_path)` — Parse ZIM archives and extract articles
   - `ingest_to_rag(zim_path)` — Full pipeline: parse → chunk → RAG
   - `get_collections()` — Get available ZIM collections
   - `get_collection(slug)` — Get specific collection by slug

2. **Collections Catalog** (`plugins/nomad/sources/collections.json`)
   - 6 categories from Project N.O.M.A.D.
   - 30+ ZIM files with metadata (title, description, URL, size)
   - Categories: Medicine, Survival, Education, DIY, Agriculture, Computing

3. **API Endpoints** (`plugins/nomad/handler.py`)
   - `GET /nomad/zim/collections` — List all collections
   - `GET /nomad/zim/collections/{slug}` — Get specific collection
   - `POST /nomad/zim/download` — Download ZIM by URL
   - `POST /nomad/zim/parse` — Parse local ZIM file
   - `POST /nomad/zim/ingest` — Full pipeline to RAG
   - `GET /nomad/zim/status` — Get loader status

### Data Flow

```
1. User selects ZIM from collection
2. POST /nomad/zim/download {url: "..."}
3. ZimAdapter downloads ZIM to data/knowledge/zim/
4. POST /nomad/zim/parse {path: "..."}
5. libzim extracts articles
6. BeautifulSoup cleans HTML to text
7. chunk_text() splits into 2000-char chunks
8. httpx sends chunks to RAG /rag/add endpoint
9. ChromaDB stores embeddings
10. GET /nomad/zim/status shows progress
```

## Usage

### List Available Collections

```bash
curl http://localhost:8003/nomad/zim/collections
```

### Download a ZIM File

```bash
curl -X POST http://localhost:8003/nomad/zim/download \
  -H "X-Auth-Key: jarvis-v3.1" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://download.kiwix.org/zim/devdocs/devdocs_en_python_2026-02.zim"}'
```

### Ingest to RAG

```bash
curl -X POST http://localhost:8003/nomad/zim/ingest \
  -H "X-Auth-Key: jarvis-v3.1" \
  -H "Content-Type: application/json" \
  -d '{"path": "data/knowledge/zim/devdocs_en_python_2026-02.zim"}'
```

### Check Status

```bash
curl http://localhost:8003/nomad/zim/status
```

## Verification

- All 11 ZIM loader tests pass
- Collections catalog has 6 categories with 30+ ZIM files
- API endpoints respond correctly
- Integration with existing NOMAD pipeline works

## Journey Log

- [lesson] Project N.O.M.A.D. (Crosstalk Solutions, 31.6k stars) uses Kiwix ZIM files for offline content — same approach works for our system
- [lesson] libzim API: use `entry.get_item().content` to get article bytes, `entry.is_redirect` checks redirects
- [pivot] Extended existing WikipediaAdapter to ZimAdapter instead of creating new adapter from scratch

## Source Materials

| File | Role | Notes |
|------|------|-------|
| `docs/compose/specs/2026-06-22-zim-loader-design.md` | Design specification | ZIM loader architecture |
| `docs/compose/plans/2026-06-22-zim-loader.md` | Implementation plan | 6 tasks, completed |
| `plugins/nomad/sources/collections.json` | ZIM catalog | From Project N.O.M.A.D. |
| `plugins/nomad/sources/zim.py` | ZimAdapter | Core implementation |
