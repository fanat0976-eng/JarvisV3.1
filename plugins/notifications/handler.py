"""
Notifications plugin — stores and delivers notifications.
Adapted from V2.1 for V3.1.
"""
import json
import time
import threading
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

_bus = None
_bus_lock = threading.Lock()


def _get_bus():
    global _bus
    if _bus is None:
        with _bus_lock:
            if _bus is None:
                try:
                    from core.event_bus import event_bus
                    _bus = event_bus
                except Exception:
                    pass
    return _bus


def get_db():
    from core.db import get_memory_conn
    return get_memory_conn()


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            priority TEXT DEFAULT 'info',
            source TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            read_at TEXT,
            data TEXT DEFAULT '{}'
        );
    """)


COOLDOWN = {}
COOLDOWN_SECONDS = 300
_MAX_COOLDOWN_ENTRIES = 1000


def _check_cooldown(title: str) -> bool:
    now = time.time()
    if len(COOLDOWN) > _MAX_COOLDOWN_ENTRIES:
        cutoff = now - COOLDOWN_SECONDS * 2
        expired = [k for k, v in COOLDOWN.items() if v < cutoff]
        for k in expired:
            del COOLDOWN[k]
    last = COOLDOWN.get(title, 0)
    if now - last < COOLDOWN_SECONDS:
        return False
    COOLDOWN[title] = now
    return True


@router.get("/health")
def health():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as c FROM notifications").fetchone()["c"]
    unread = conn.execute("SELECT COUNT(*) as c FROM notifications WHERE read_at IS NULL").fetchone()["c"]
    return {"status": "ok", "total": total, "unread": unread}


@router.post("/send")
async def send_notification(request: Request):
    data = await request.json()
    title = data.get("title", "")
    body = data.get("body", "")
    priority = data.get("priority", "info")
    source = data.get("source", "")
    notif_data = data.get("data", {})
    if not title:
        return JSONResponse({"error": "title required"}, status_code=400)
    if not _check_cooldown(title):
        return {"status": "ok", "deduplicated": True}
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO notifications (title, body, priority, source, created_at, data) VALUES (?, ?, ?, ?, ?, ?)",
        (title, body, priority, source, now, json.dumps(notif_data))
    )
    conn.commit()
    bus = _get_bus()
    if bus:
        bus.emit("notification.new", {"title": title, "body": body, "priority": priority, "source": source}, source="notifications")
    return {"status": "ok", "priority": priority}


@router.get("/list")
def list_notifications(limit: int = 20, unread_only: bool = False):
    conn = get_db()
    if unread_only:
        rows = conn.execute("SELECT * FROM notifications WHERE read_at IS NULL ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"notifications": [dict(r) for r in rows]}


@router.post("/read")
async def mark_read(request: Request):
    data = await request.json()
    notif_id = data.get("id")
    conn = get_db()
    if notif_id:
        conn.execute("UPDATE notifications SET read_at = ? WHERE id = ?", (datetime.now(timezone.utc).isoformat(), notif_id))
    else:
        conn.execute("UPDATE notifications SET read_at = ? WHERE read_at IS NULL", (datetime.now(timezone.utc).isoformat(),))
    conn.commit()
    return {"status": "ok"}


@router.get("/unread")
def get_unread():
    conn = get_db()
    rows = conn.execute("SELECT * FROM notifications WHERE read_at IS NULL ORDER BY created_at DESC LIMIT 10").fetchall()
    return {"notifications": [dict(r) for r in rows], "count": len(rows)}


@router.post("/clear")
def clear_all():
    conn = get_db()
    conn.execute("DELETE FROM notifications")
    conn.commit()
    return {"status": "ok"}


def on_startup():
    init_db()
    print("  [notifications] Initialized")


def on_shutdown():
    print("  [notifications] Shutdown complete")
