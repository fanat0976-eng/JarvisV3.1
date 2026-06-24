"""
NOMAD Knowledge Pipeline - Content ingestion for RAG.
"""
import os
import asyncio
import httpx
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .sources.zim import ZimAdapter

router = APIRouter()

zim_adapter = ZimAdapter()

BASE_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"


def _load_config():
    global BASE_URL, AUTH_KEY
    try:
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / "core" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        server = config.get("server", {})
        port = server.get("port", 8003)
        host = server.get("host", "127.0.0.1")
        BASE_URL = f"http://{host}:{port}"
        AUTH_KEY = server.get("auth_key", AUTH_KEY)
    except Exception:
        pass


_load_config()


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
        async with httpx.AsyncClient() as client:
            r = await client.post(
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
        async with httpx.AsyncClient() as client:
            r = await client.post(
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
    async with httpx.AsyncClient() as client:
        for ext in extensions:
            for filepath in Path(dirpath).rglob(f"*{ext}"):
                try:
                    r = await client.post(
                        f"{BASE_URL}/rag/index_file",
                        json={"path": str(filepath)},
                        headers=get_headers(),
                        timeout=60
                    )
                    results.append({"file": str(filepath), "status": r.json()})
                except Exception as e:
                    results.append({"file": str(filepath), "error": str(e)})
    
    return {"status": "ok", "processed": len(results), "results": results}


@router.get("/sources/wikipedia/status")
async def wikipedia_status():
    """Get Wikipedia download/processing status."""
    return zim_adapter.pipeline.get_status()


@router.post("/sources/wikipedia/download")
async def wikipedia_download(request: Request):
    """Start downloading Wikipedia ZIM."""
    data = await request.json()
    language = data.get("language", "ru")
    
    # Use ZimAdapter for Wikipedia
    wiki_url = f"https://download.kiwix.org/zim/wikipedia/wikipedia_{language}_all_nopic_latest.zim"
    
    async def run_download():
        try:
            await asyncio.to_thread(zim_adapter.download_from_kiwix, wiki_url)
            return {"status": "completed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    asyncio.create_task(run_download())
    
    return {"status": "downloading", "language": language, "url": wiki_url}


@router.get("/zim/collections")
async def zim_collections():
    """Get available ZIM collections."""
    return {"collections": zim_adapter.get_collections()}


@router.get("/zim/collections/{slug}")
async def zim_collection(slug: str):
    """Get specific collection by slug."""
    collection = zim_adapter.get_collection(slug)
    if not collection:
        return JSONResponse({"error": f"Collection '{slug}' not found"}, status_code=404)
    return collection


@router.post("/zim/download")
async def zim_download(request: Request):
    """Download ZIM file from Kiwix URL."""
    data = await request.json()
    url = data.get("url", "")
    
    if not url:
        return JSONResponse({"error": "No URL provided"}, status_code=400)
    
    async def run_download():
        try:
            zim_path = await asyncio.to_thread(zim_adapter.download_from_kiwix, url)
            return {"status": "completed", "path": str(zim_path)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    asyncio.create_task(run_download())
    
    return {"status": "downloading", "url": url}


@router.post("/zim/parse")
async def zim_parse(request: Request):
    """Parse local ZIM file."""
    data = await request.json()
    zim_path = data.get("path", "")
    
    if not zim_path or not os.path.exists(zim_path):
        return JSONResponse({"error": f"ZIM file not found: {zim_path}"}, status_code=404)
    
    articles = zim_adapter.parse_zim(Path(zim_path))
    return {"status": "ok", "articles": len(articles)}


@router.post("/zim/ingest")
async def zim_ingest(request: Request):
    """Full pipeline: parse → chunk → RAG."""
    data = await request.json()
    zim_path = data.get("path", "")
    
    if not zim_path or not os.path.exists(zim_path):
        return JSONResponse({"error": f"ZIM file not found: {zim_path}"}, status_code=404)
    
    async def run_ingest():
        try:
            result = await asyncio.to_thread(zim_adapter.ingest_to_rag, Path(zim_path))
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    asyncio.create_task(run_ingest())
    
    return {"status": "ingesting", "path": zim_path}


@router.get("/zim/status")
async def zim_status():
    """Get ZIM loader status."""
    return zim_adapter.pipeline.get_status()
