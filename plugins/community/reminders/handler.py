"""
Reminders plugin — one-shot and recurring reminders with notifications.
"""
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
REMINDERS_FILE = DATA_DIR / "reminders.json"
_reminders = []
_lock = threading.Lock()
_running = False
_checker_thread = None


def _load():
    global _reminders
    if REMINDERS_FILE.exists():
        try:
            _reminders = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            _reminders = []


def _save():
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REMINDERS_FILE.write_text(json.dumps(_reminders, indent=2, ensure_ascii=False), encoding="utf-8")


def _check_reminders():
    global _running
    _running = True
    while _running:
        now = time.time()
        with _lock:
            due = [r for r in _reminders if r.get("trigger_at", 0) <= now and not r.get("fired")]
            for r in due:
                r["fired"] = True
                _fire_reminder(r)
            _reminders[:] = [r for r in _reminders if not (r.get("fired") and not r.get("recurring"))]
            for r in _reminders:
                if r.get("recurring") and r.get("fired"):
                    r["fired"] = False
                    interval = r.get("interval_seconds", 86400)
                    r["trigger_at"] = now + interval
            _save()
        time.sleep(5)


def _fire_reminder(reminder):
    try:
        from core.event_bus import event_bus
        event_bus.emit("reminder.fired", {
            "id": reminder.get("id"),
            "text": reminder.get("text"),
            "recurring": reminder.get("recurring", False),
        }, source="plugin:reminders")
    except Exception:
        pass


@router.get("/health")
def health():
    return {"status": "ok", "plugin": "reminders", "active": len([r for r in _reminders if not r.get("fired")])}


@router.post("/add")
async def add_reminder(request: Request):
    data = await request.json()
    text = data.get("text", "")
    trigger_at = data.get("trigger_at")
    interval_seconds = data.get("interval_seconds")
    recurring = data.get("recurring", False)

    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)

    if trigger_at is None:
        return JSONResponse({"error": "trigger_at (unix timestamp) required"}, status_code=400)

    reminder = {
        "id": f"rem_{int(time.time() * 1000)}",
        "text": text,
        "trigger_at": trigger_at,
        "recurring": recurring,
        "interval_seconds": interval_seconds or 86400,
        "fired": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with _lock:
        _reminders.append(reminder)
        _save()

    return {"status": "ok", "id": reminder["id"]}


@router.post("/add/quick")
async def add_quick(request: Request):
    data = await request.json()
    text = data.get("text", "")
    minutes = data.get("minutes", 60)

    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)

    trigger_at = time.time() + minutes * 60
    reminder = {
        "id": f"rem_{int(time.time() * 1000)}",
        "text": text,
        "trigger_at": trigger_at,
        "recurring": False,
        "interval_seconds": 0,
        "fired": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with _lock:
        _reminders.append(reminder)
        _save()

    return {"status": "ok", "id": reminder["id"], "fires_at": datetime.fromtimestamp(trigger_at).isoformat()}


@router.get("/list")
def list_reminders():
    with _lock:
        active = [r for r in _reminders if not r.get("fired")]
    return {"reminders": active, "count": len(active)}


@router.post("/cancel")
async def cancel(request: Request):
    data = await request.json()
    rid = data.get("id", "")
    with _lock:
        before = len(_reminders)
        _reminders[:] = [r for r in _reminders if r.get("id") != rid]
        _save()
        removed = before - len(_reminders)
    return {"status": "ok", "removed": removed}


@router.post("/clear")
def clear():
    with _lock:
        _reminders.clear()
        _save()
    return {"status": "ok"}


def on_startup():
    _load()
    global _checker_thread
    _checker_thread = threading.Thread(target=_check_reminders, daemon=True)
    _checker_thread.start()
    print(f"  [reminders] Started: {len([r for r in _reminders if not r.get('fired')])} active")


def on_shutdown():
    global _running
    _running = False
