"""
System Stats plugin — CPU, RAM, disk, network monitoring.
Requires: psutil
"""
import time
import shutil
from fastapi import APIRouter

router = APIRouter()

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@router.get("/health")
def health():
    return {"status": "ok", "plugin": "system_stats", "psutil": HAS_PSUTIL}


@router.get("/overview")
def overview():
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}

    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()

    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    net = psutil.net_io_counters()

    return {
        "cpu": {
            "percent": cpu_percent,
            "count": cpu_count,
            "freq_mhz": round(cpu_freq.current) if cpu_freq else None,
        },
        "memory": {
            "total_gb": round(mem.total / (1024 ** 3), 1),
            "used_gb": round(mem.used / (1024 ** 3), 1),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024 ** 3), 1),
            "used_gb": round(disk.used / (1024 ** 3), 1),
            "percent": round(disk.used / disk.total * 100, 1),
        },
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
        },
    }


@router.get("/cpu")
def cpu():
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}
    return {
        "percent": psutil.cpu_percent(interval=0.5),
        "count": psutil.cpu_count(),
        "per_cpu": psutil.cpu_percent(interval=0.5, percpu=True),
    }


@router.get("/memory")
def memory():
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 1),
        "used_gb": round(mem.used / (1024 ** 3), 1),
        "available_gb": round(mem.available / (1024 ** 3), 1),
        "percent": mem.percent,
        "swap_percent": swap.percent,
    }


@router.get("/processes")
def top_processes(limit: int = 10):
    if not HAS_PSUTIL:
        return {"error": "psutil not installed"}

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)
    return {"processes": procs[:limit]}


def on_startup():
    status = "psutil available" if HAS_PSUTIL else "psutil not installed (pip install psutil)"
    print(f"  [system_stats] Started: {status}")


def on_shutdown():
    pass
