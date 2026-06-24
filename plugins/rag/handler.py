"""
RAG plugin — ChromaDB + Ollama embeddings (nomic-embed-text).
No sentence-transformers dependency.
"""
import os
import time
import uuid
import httpx
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

INDEX_DIR = str(Path(__file__).parent.parent.parent / "data" / "chroma_db")
OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "nomic-embed-text"

collection = None


def get_collection():
    global collection
    if collection is None:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=INDEX_DIR)
            collection = client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            return None
    return collection


def embed(texts: list[str] | str) -> list[list[float]]:
    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        return []
    if len(texts) == 1:
        try:
            r = httpx.post(f"{OLLAMA_URL}/api/embeddings", json={"model": EMBED_MODEL, "prompt": texts[0]}, timeout=30)
            r.raise_for_status()
            return [r.json()["embedding"]]
        except Exception as e:
            raise RuntimeError(f"Embedding failed: {e}")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _embed_one(text: str) -> list[float]:
        r = httpx.post(f"{OLLAMA_URL}/api/embeddings", json={"model": EMBED_MODEL, "prompt": text}, timeout=30)
        r.raise_for_status()
        return r.json()["embedding"]

    embeddings = [None] * len(texts)
    with ThreadPoolExecutor(max_workers=4) as pool:
        future_to_idx = {pool.submit(_embed_one, t): i for i, t in enumerate(texts)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            embeddings[idx] = future.result()
    return embeddings


async def aembed(texts: list[str] | str) -> list[list[float]]:
    """Async wrapper for embed() - runs in thread pool to avoid blocking."""
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, embed, texts)


@router.get("/health")
def health():
    try:
        col = get_collection()
        if col is None:
            return {"status": "degraded", "error": "ChromaDB not available"}
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        has_embed = any("nomic" in m for m in models)
        return {"status": "ok", "documents": col.count(), "embed_model": EMBED_MODEL, "model_available": has_embed}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/add")
async def add(request: Request):
    data = await request.json()
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    doc_id = data.get("id", None)
    if not text:
        return JSONResponse({"error": "No text provided"}, status_code=400)
    try:
        col = get_collection()
        if col is None:
            return JSONResponse({"error": "RAG not available"}, status_code=503)
        embedding = (await aembed(text))[0]
        if not doc_id:
            doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        col.add(documents=[text], ids=[doc_id], embeddings=[embedding], metadatas=[metadata])
        return {"status": "ok", "id": doc_id, "count": col.count()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/add_batch")
async def add_batch(request: Request):
    data = await request.json()
    documents = data.get("documents", [])
    if not documents:
        return JSONResponse({"error": "No documents"}, status_code=400)
    try:
        col = get_collection()
        if col is None:
            return JSONResponse({"error": "RAG not available"}, status_code=503)
        texts = [d.get("text", "") for d in documents]
        ids = [d.get("id", f"doc_{uuid.uuid4().hex[:12]}") for d in documents]
        metadatas = [d.get("metadata", {}) for d in documents]
        embeddings = await aembed(texts)
        col.add(documents=texts, ids=ids, embeddings=embeddings, metadatas=metadatas)
        return {"status": "ok", "added": len(texts), "total": col.count()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/search")
async def search(request: Request):
    data = await request.json()
    query = data.get("query", "")
    n_results = data.get("n_results", 5)
    threshold = data.get("threshold", 0.35)
    if not query:
        return JSONResponse({"error": "No query provided"}, status_code=400)
    try:
        col = get_collection()
        if col is None:
            return JSONResponse({"error": "RAG not available"}, status_code=503)
        if col.count() == 0:
            return {"results": [], "total": 0, "message": "Base is empty"}
        q_emb = (await aembed(query))[0]
        results = col.query(query_embeddings=[q_emb], n_results=n_results,
                            include=["documents", "metadatas", "distances"])
        found = []
        for i in range(len(results["ids"][0])):
            dist = results["distances"][0][i]
            if dist <= threshold:
                found.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": dist,
                })
        return {"results": found, "total": col.count()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question", "")
    n_context = data.get("n_context", 3)
    threshold = data.get("threshold", 0.35)
    if not question:
        return JSONResponse({"error": "No question"}, status_code=400)
    try:
        col = get_collection()
        if col is None:
            return JSONResponse({"error": "RAG not available"}, status_code=503)
        if col.count() == 0:
            return {"context": "", "sources": [], "message": "Base is empty"}
        q_emb = (await aembed(question))[0]
        results = col.query(query_embeddings=[q_emb], n_results=n_context,
                            include=["documents", "metadatas", "distances"])
        filtered_docs = []
        filtered_sources = []
        for i in range(len(results["ids"][0])):
            dist = results["distances"][0][i]
            if dist <= threshold:
                filtered_docs.append(results["documents"][0][i])
                filtered_sources.append({
                    "id": results["ids"][0][i],
                    "preview": results["documents"][0][i][:200],
                    "metadata": results["metadatas"][0][i],
                    "distance": dist,
                })
        context = "\n\n---\n\n".join(filtered_docs)
        return {"context": context, "sources": filtered_sources}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/delete")
async def delete(request: Request):
    data = await request.json()
    doc_id = data.get("id", "")
    if not doc_id:
        return JSONResponse({"error": "No id provided"}, status_code=400)
    try:
        col = get_collection()
        if col is None:
            return JSONResponse({"error": "RAG not available"}, status_code=503)
        col.delete(ids=[doc_id])
        return {"status": "ok", "deleted": doc_id, "count": col.count()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/index_file")
async def index_file(request: Request):
    data = await request.json()
    filepath = data.get("path", "")
    chunk_size = data.get("chunk_size", 500)
    chunk_overlap = data.get("overlap", 50)
    if not filepath or not os.path.exists(filepath):
        return JSONResponse({"error": f"File not found: {filepath}"}, status_code=404)
    try:
        ext = Path(filepath).suffix.lower()
        if ext == ".pdf":
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        elif ext == ".docx":
            from docx import Document
            doc = Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        if not chunks:
            return {"error": "No content extracted"}
        col = get_collection()
        if col is None:
            return JSONResponse({"error": "RAG not available"}, status_code=503)
        base_id = Path(filepath).stem
        ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filepath, "chunk": i, "total_chunks": len(chunks)} for i in range(len(chunks))]
        embeddings = await aembed(chunks)
        col.add(documents=chunks, ids=ids, embeddings=embeddings, metadatas=metadatas)
        return {"status": "ok", "chunks_added": len(chunks), "total_docs": col.count()}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def ask_rag(question: str, n_context: int = 3, threshold: float = 0.35) -> dict:
    """Direct function call for RAG ask - used by brain plugin."""
    col = get_collection()
    if col is None or col.count() == 0:
        return {"context": "", "sources": []}
    q_emb = (await aembed(question))[0]
    results = col.query(query_embeddings=[q_emb], n_results=n_context,
                        include=["documents", "metadatas", "distances"])
    filtered_docs = []
    filtered_sources = []
    for i in range(len(results["ids"][0])):
        dist = results["distances"][0][i]
        if dist <= threshold:
            filtered_docs.append(results["documents"][0][i])
            filtered_sources.append({
                "id": results["ids"][0][i],
                "preview": results["documents"][0][i][:200],
                "metadata": results["metadatas"][0][i],
                "distance": dist,
            })
    context = "\n\n---\n\n".join(filtered_docs)
    return {"context": context, "sources": filtered_sources}
