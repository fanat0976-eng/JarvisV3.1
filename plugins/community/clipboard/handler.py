"""
Clipboard plugin — clipboard history, search, pin items.
"""
import time
from collections import deque
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

_history = deque(maxlen=100)
_pins = []


@router.get("/health")
def health():
    return {"status": "ok", "plugin": "clipboard", "history_size": len(_history), "pins": len(_pins)}


@router.post("/copy")
async def copy_item(request: Request):
    data = await request.json()
    text = data.get("text", "")
    source = data.get("source", "")

    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)

    item = {
        "text": text,
        "source": source,
        "timestamp": time.time(),
    }
    _history.appendleft(item)
    return {"status": "ok", "history_size": len(_history)}


@router.get("/history")
def history(limit: int = 20):
    items = list(_history)[:limit]
    return {"items": items, "total": len(_history)}


@router.post("/search")
async def search(request: Request):
    data = await request.json()
    query = data.get("query", "").lower()
    if not query:
        return JSONResponse({"error": "query required"}, status_code=400)

    results = [item for item in _history if query in item["text"].lower()][:20]
    return {"results": results, "count": len(results)}


@router.post("/pin")
async def pin_item(request: Request):
    data = await request.json()
    text = data.get("text", "")
    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)

    item = {"text": text, "pinned_at": time.time()}
    _pins.append(item)
    return {"status": "ok", "pins": len(_pins)}


@router.get("/pins")
def list_pins():
    return {"pins": _pins, "count": len(_pins)}


@router.post("/clear")
def clear_history():
    _history.clear()
    return {"status": "ok"}


def on_startup():
    print("  [clipboard] Started: history + pins")


def on_shutdown():
    pass
