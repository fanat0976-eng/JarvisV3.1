# NOMAD Knowledge Pipeline Design

## [S1] Problem

Jarvis V3.1 needs a way to ingest large-scale knowledge from external sources (Wikipedia, documentation, etc.) into its RAG system. The current NOMAD plugin only handles basic file/text ingestion, but lacks source-specific adapters for downloading and processing complex content formats like Wikipedia ZIM files.

## [S2] Solution Overview

Extend the NOMAD plugin with source-specific adapters. Each adapter handles:
1. Downloading content from a specific source
2. Parsing source-specific formats (ZIM, HTML, etc.)
3. Chunking content into appropriate sizes for RAG
4. Ingesting into RAG via existing endpoints

**Architecture:**
```
plugins/nomad/
├── __init__.py
├── handler.py          # Existing API endpoints
├── sources/
│   ├── __init__.py
│   └── wikipedia.py    # Wikipedia ZIM adapter
├── pipeline.py         # Pipeline orchestration
└── chunker.py          # Text chunking utilities
```

## [S3] Wikipedia ZIM Adapter

**Source:** Russian Wikipedia ZIM file from Wikimedia mirrors
**Format:** ZIM (Zeno Internet Movie database format)
**Library:** `libzim` (Python bindings for libzim)

**Processing Flow:**
1. Download ZIM file (~30GB for Russian Wikipedia)
2. Parse ZIM archive
3. Extract articles (HTML content)
4. Clean HTML → plain text
5. Chunk articles into ~500 token segments
6. Ingest into RAG with metadata (title, url, section)

**Storage:**
```
data/knowledge/wikipedia/
├── ruwiki.zim          # Raw ZIM file
├── ruwiki/             # Processed articles (JSON)
└── status.json         # Processing status
```

## [S4] API Endpoints

### POST /nomad/sources/wikipedia/download
Start downloading Wikipedia ZIM file.

**Request:**
```json
{
  "language": "ru",
  "mirror": "auto"
}
```

**Response:**
```json
{
  "status": "downloading",
  "url": "https://mirror.example.com/ruwiki.zim",
  "size": 30000000000,
  "progress": 0
}
```

### POST /nomad/sources/wikipedia/process
Process downloaded ZIM file into RAG-ready chunks.

**Request:**
```json
{
  "chunk_size": 500,
  "overlap": 50,
  "max_articles": null
}
```

**Response:**
```json
{
  "status": "processing",
  "total_articles": 1800000,
  "processed": 0
}
```

### GET /nomad/sources/wikipedia/status
Check download/processing status.

**Response:**
```json
{
  "download_status": "ready",
  "process_status": "processing",
  "total_articles": 1800000,
  "processed": 450000,
  "ingested": 400000,
  "errors": 12
}
```

## [S5] Chunking Strategy

**Parameters:**
- Chunk size: 500 tokens (~2000 characters)
- Overlap: 50 tokens (~200 characters)
- Separation: By sections within articles

**Metadata per chunk:**
```json
{
  "source": "wikipedia",
  "language": "ru",
  "title": "Статья",
  "url": "https://ru.wikipedia.org/wiki/Статья",
  "section": "Основной раздел",
  "chunk_index": 0,
  "total_chunks": 5
}
```

## [S6] Dependencies

- `libzim` - Python bindings for libzim (ZIM file reader)
- `beautifulsoup4` - HTML cleaning
- `lxml` - HTML parsing

## [S7] Error Handling

- Download failures: retry 3 times, then mark as failed
- Parse errors: skip article, log error, continue
- Ingestion errors: retry chunk, log error, continue
- All errors tracked in `status.json`

## [S8] Testing

1. Unit tests for chunker (text splitting logic)
2. Integration tests for Wikipedia adapter (mock ZIM)
3. E2E test: download small ZIM → process → search RAG

## [S9] Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Create chunker.py
- [ ] Create pipeline.py
- [ ] Update handler.py with status tracking

### Phase 2: Wikipedia Adapter
- [ ] Create sources/wikipedia.py
- [ ] Implement download function
- [ ] Implement process function
- [ ] Add status endpoint

### Phase 3: Testing & Polish
- [ ] Unit tests
- [ ] Integration tests
- [ ] Update ROADMAP.md

---

*Design spec v1.0*
*Created: 2026-06-21*