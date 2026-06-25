"""
Watchers plugin — background monitoring.
Adapted from V2.1 for V3.1.
"""
import time
import asyncio
import shutil
import threading
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

_bus = None
_bus_lock = threading.Lock()
_watchers_running = False
_watcher_threads = []


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


def _emit(topic, data):
    bus = _get_bus()
    if bus:
        bus.emit(topic, data, source="watchers")


def disk_monitor(interval=300):
    while _watchers_running:
        try:
            usage = shutil.disk_usage("/")
            free_gb = usage.free / (1024**3)
            used_pct = (usage.used / usage.total) * 100
            if used_pct > 95:
                _emit("disk.critical", {"free_gb": round(free_gb, 1), "used_pct": round(used_pct, 1)})
            elif used_pct > 85:
                _emit("disk.warning", {"free_gb": round(free_gb, 1), "used_pct": round(used_pct, 1)})
        except Exception:
            pass
        time.sleep(interval)


def network_monitor(interval=60):
    last_online = None
    while _watchers_running:
        try:
            import urllib.request
            urllib.request.urlopen("https://1.1.1.1", timeout=5)
            online = True
        except Exception:
            online = False
        if last_online is not None and last_online != online:
            if online:
                _emit("network.online", {"status": "online"})
            else:
                _emit("network.offline", {"status": "offline"})
        last_online = online
        time.sleep(interval)


def time_trigger(interval=60):
    last_hour = None
    while _watchers_running:
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        if hour != last_hour:
            if hour == 8:
                _emit("time.morning", {"hour": hour, "weekday": weekday})
            elif hour == 20:
                _emit("time.evening", {"hour": hour, "weekday": weekday})
            elif hour == 0:
                _emit("time.midnight", {"hour": hour, "weekday": weekday})
        last_hour = hour
        time.sleep(interval)


def start_watchers():
    global _watchers_running
    if _watchers_running:
        return
    _watchers_running = True
    threads = [
        threading.Thread(target=disk_monitor, args=(300,), daemon=True),
        threading.Thread(target=network_monitor, args=(60,), daemon=True),
        threading.Thread(target=time_trigger, args=(60,), daemon=True),
    ]
    for t in threads:
        t.start()
        _watcher_threads.append(t)


def stop_watchers():
    global _watchers_running
    _watchers_running = False
    for t in _watcher_threads:
        t.join(timeout=5)
    _watcher_threads.clear()


def on_startup():
    start_watchers()


def on_shutdown():
    stop_watchers()


@router.get("/health")
def health():
    return {"status": "ok", "running": _watchers_running, "threads": len(_watcher_threads)}


@router.get("/status")
def status():
    usage = shutil.disk_usage("/")
    return {
        "disk": {
            "free_gb": round(usage.free / (1024**3), 1),
            "total_gb": round(usage.total / (1024**3), 1),
            "used_pct": round((usage.used / usage.total) * 100, 1),
        },
        "watchers_running": _watchers_running,
    }


@router.post("/restart")
async def restart():
    stop_watchers()
    await asyncio.sleep(1)
    start_watchers()
    return {"status": "ok", "running": _watchers_running}
