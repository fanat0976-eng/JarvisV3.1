"""
Todo plugin — task list with priorities and status.
"""
import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

_todos = []
_next_id = 1


@router.get("/health")
def health():
    return {"status": "ok", "plugin": "todo", "active": len([t for t in _todos if not t["done"]])}


@router.post("/add")
async def add(request: Request):
    global _next_id
    data = await request.json()
    text = data.get("text", "")
    priority = data.get("priority", "medium")

    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)

    todo = {
        "id": _next_id,
        "text": text,
        "priority": priority,
        "done": False,
        "created_at": time.time(),
    }
    _next_id += 1
    _todos.append(todo)
    return {"status": "ok", "id": todo["id"]}


@router.get("/list")
def list_todos(show_done: bool = False):
    items = _todos if show_done else [t for t in _todos if not t["done"]]
    items.sort(key=lambda t: {"high": 0, "medium": 1, "low": 2}.get(t["priority"], 1))
    return {"todos": items, "count": len(items)}


@router.post("/done")
async def mark_done(request: Request):
    data = await request.json()
    tid = data.get("id")
    for t in _todos:
        if t["id"] == tid:
            t["done"] = True
            return {"status": "ok"}
    return JSONResponse({"error": "not found"}, status_code=404)


@router.post("/delete")
async def delete(request: Request):
    data = await request.json()
    tid = data.get("id")
    global _todos
    before = len(_todos)
    _todos = [t for t in _todos if t["id"] != tid]
    return {"status": "ok", "removed": before - len(_todos)}


@router.post("/clear")
def clear():
    _todos.clear()
    return {"status": "ok"}


def on_startup():
    print("  [todo] Started")


def on_shutdown():
    pass
