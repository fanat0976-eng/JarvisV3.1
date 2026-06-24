# ZIM Loader for RAG — Design Specification

> [!NOTE]
> This document may not reflect the current implementation.
> See the final report for up-to-date state:
> [Final Report](../reports/zim-loader.md)

## [S1] Problem

Jarvis V3.1 нуждается в оффлайн базе знаний. Project N.O.M.A.D. (Crosstalk Solutions, 31.6k stars) использует Kiwix ZIM файлы для оффлайн контента: медицина, выживание, образование, DIY, кулинария, программирование.

Нужен полный пайплайн: скачать ZIM файл с Kiwix → распарсить → нарезать на чанки → загрузить в RAG.

## [S2] Solution Overview

Расширить существующий WikipediaAdapter в ZimAdapter с поддержкой любых ZIM файлов из Project N.O.M.A.D. коллекций.

### Архитектура

```
ZIM Loader Pipeline
    │
    ├── KiwixAdapter (sources/zim.py)
    │   ├── download_from_kiwix(url) → zim_path
    │   ├── parse_zim(zim_path) → articles[]
    │   ├── extract_articles(zim_path) → chunks[]
    │   └── ingest_to_rag(zim_path) → RAG
    │
    ├── Collections (sources/collections.json)
    │   ├── Medicine (67MB - 2GB)
    │   ├── Survival & Preparedness
    │   ├── Education & Reference
    │   ├── DIY & Repair
    │   ├── Agriculture & Food
    │   └── Computing & Technology
    │
    └── API Endpoints
        ├── POST /nomad/zim/download
        ├── POST /nomad/zim/parse
        └── GET /nomad/zim/status
```

## [S3] Components

### 1. ZimAdapter (plugins/nomad/sources/zim.py)

Расширение существующего WikipediaAdapter:

```python
class ZimAdapter:
    def __init__(self, language: str = "en"):
        self.language = language
        self.pipeline = Pipeline("zim_loader")
    
    def download_from_kiwix(self, url: str) -> Path:
        """Скачать ZIM файл по URL."""
        
    def parse_zim(self, zim_path: Path) -> list[dict]:
        """Распарсить ZIM архив, извлечь статьи."""
        
    def extract_articles(self, zim_path: Path) -> list[dict]:
        """Извлечь статьи из ZIM файла."""
        
    def ingest_to_rag(self, zim_path: Path) -> dict:
        """Полный пайплайн: parse → chunk → RAG."""
        
    def get_collection(self, category: str) -> list[dict]:
        """Получить список ZIM файлов по категории."""
```

### 2. Collections (plugins/nomad/sources/collections.json)

Встроенный список ZIM файлов из Project N.O.M.A.D.:

```json
{
  "categories": [
    {
      "name": "Medicine",
      "slug": "medicine",
      "resources": [
        {"id": "zimgit-medicine_en", "title": "Medical Library", "url": "...", "size_mb": 67},
        {"id": "nhs.uk_en_medicines", "title": "NHS Medicines A to Z", "url": "...", "size_mb": 16},
        {"id": "fas-military-medicine_en", "title": "Military Medicine", "url": "...", "size_mb": 78},
        {"id": "wwwnc.cdc.gov_en_all", "title": "CDC Health Information", "url": "...", "size_mb": 170},
        {"id": "medlineplus.gov_en_all", "title": "MedlinePlus", "url": "...", "size_mb": 1800}
      ]
    },
    // ... другие категории
  ]
}
```

### 3. API Endpoints (plugins/nomad/handler.py)

Новые эндпоинты в NOMAD handler:

```python
@router.post("/zim/download")
async def zim_download(request: Request):
    """Скачать ZIM файл по URL."""
    
@router.post("/zim/parse")
async def zim_parse(request: Request):
    """Распарсить локальный ZIM файл."""
    
@router.get("/zim/status")
async def zim_status():
    """Статус загрузки/парсинга."""
    
@router.get("/zim/collections")
async def zim_collections():
    """Список доступных коллекций."""
```

## [S4] Data Flow

```
1. User selects ZIM file from collection
2. POST /nomad/zim/download {url: "..."}
3. ZimAdapter.download_from_kiwix(url)
4. Download ZIM to data/knowledge/zim/
5. POST /nomad/zim/parse {path: "data/knowledge/zim/file.zim"}
6. ZimAdapter.parse_zim(path)
7. Extract articles → chunk_text() → embed() → RAG
8. GET /nomad/zim/status → {status: "ready", documents: 1234}
```

## [S5] Error Handling

- **Download failed**: Retry 3 times, then report error
- **Parse failed**: Log error, skip corrupted entries
- **RAG unavailable**: Queue for later ingestion
- **Disk space**: Check available space before download

## [S6] Testing

1. Unit tests for ZimAdapter methods
2. Integration test with small ZIM file
3. E2E test: download → parse → RAG search

## [S7] Success Criteria

1. ✅ ZimAdapter can download any ZIM file from Kiwix
2. ✅ ZimAdapter can parse ZIM files and extract articles
3. ✅ Articles are chunked and loaded into RAG
4. ✅ All 6 categories from Project N.O.M.A.D. are supported
5. ✅ API endpoints work correctly
6. ✅ Status tracking works during download/parse
