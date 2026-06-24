"""
Wizard Plugin — First-Run setup wizard for Jarvis V3.1.
Checks system requirements, configures services, verifies connectivity.
"""
import os
import shutil
import httpx
import subprocess
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent


def _check_python():
    import sys
    v = sys.version_info
    return {
        "ok": v >= (3, 10),
        "version": f"{v.major}.{v.minor}.{v.micro}",
        "message": f"Python {v.major}.{v.minor}" if v >= (3, 10) else "Нужен Python 3.10+",
    }


def _check_ollama():
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        has_qwen = any("qwen" in m for m in models)
        has_embed = any("nomic" in m for m in models)
        return {
            "ok": has_qwen and has_embed,
            "models": models,
            "message": f"Ollama: {len(models)} моделей" if models else "Ollama: нет моделей",
            "has_chat_model": has_qwen,
            "has_embed_model": has_embed,
        }
    except Exception:
        return {"ok": False, "models": [], "message": "Ollama не запущен", "has_chat_model": False, "has_embed_model": False}


def _check_chromadb():
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(PROJECT_ROOT / "data" / "chroma_db"))
        col = client.get_or_create_collection("health_check")
        return {"ok": True, "message": "ChromaDB доступен"}
    except Exception as e:
        return {"ok": False, "message": f"ChromaDB: {e}"}


def _check_disk():
    usage = shutil.disk_usage("/")
    free_gb = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    used_pct = (usage.used / usage.total) * 100
    return {
        "ok": free_gb > 5,
        "free_gb": round(free_gb, 1),
        "total_gb": round(total_gb, 1),
        "used_pct": round(used_pct, 1),
        "message": f"Свободно: {round(free_gb, 1)} GB",
    }


def _check_config():
    config_path = PROJECT_ROOT / "core" / "config.yaml"
    if not config_path.exists():
        return {"ok": False, "message": "config.yaml не найден"}
    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)
    plugins_enabled = sum(1 for v in config.get("plugins", {}).values() if isinstance(v, dict) and v.get("enabled"))
    return {
        "ok": True,
        "plugins_enabled": plugins_enabled,
        "message": f"Конфиг: {plugins_enabled} плагинов включено",
    }


def _check_rag():
    try:
        r = httpx.get("http://localhost:8003/rag/health", timeout=3, headers={"X-Auth-Key": "jarvis-v3.1"})
        data = r.json()
        return {"ok": data.get("status") == "ok", "documents": data.get("documents", 0), "message": f"RAG: {data.get('documents', 0)} документов"}
    except Exception:
        return {"ok": False, "message": "RAG недоступен"}


@router.get("/health")
def health():
    return {"status": "ok", "message": "Wizard plugin loaded"}


@router.get("/check")
def system_check():
    checks = {
        "python": _check_python(),
        "ollama": _check_ollama(),
        "chromadb": _check_chromadb(),
        "disk": _check_disk(),
        "config": _check_config(),
        "rag": _check_rag(),
    }
    all_ok = all(c["ok"] for c in checks.values())
    return {"all_ok": all_ok, "checks": checks}


@router.get("/steps")
def wizard_steps():
    return {
        "steps": [
            {"id": 1, "title": "Python 3.10+", "description": "Проверка версии Python", "check": "python"},
            {"id": 2, "title": "Ollama", "description": "Проверка Ollama + моделей (qwen2.5, nomic-embed-text)", "check": "ollama"},
            {"id": 3, "title": "ChromaDB", "description": "Проверка векторной БД", "check": "chromadb"},
            {"id": 4, "title": "Диск", "description": "Проверка свободного места (минимум 5GB)", "check": "disk"},
            {"id": 5, "title": "Конфигурация", "description": "Проверка config.yaml", "check": "config"},
            {"id": 6, "title": "RAG", "description": "Проверка базы знаний", "check": "rag"},
        ]
    }


@router.post("/setup")
async def auto_setup():
    results = []

    ollama = _check_ollama()
    if not ollama["ok"] and not ollama.get("has_chat_model"):
        results.append({"step": "ollama", "status": "warning", "message": "Скачайте модель: ollama pull qwen2.5:7b"})
    if not ollama.get("has_embed_model"):
        results.append({"step": "embed", "status": "warning", "message": "Скачайте embeddings: ollama pull nomic-embed-text"})

    os.makedirs(PROJECT_ROOT / "data", exist_ok=True)
    os.makedirs(PROJECT_ROOT / "workspace", exist_ok=True)
    results.append({"step": "dirs", "status": "ok", "message": "Директории созданы"})

    return {"status": "ok", "results": results}


def on_startup():
    print("  [wizard] Initialized: first-run checker")


def on_shutdown():
    pass
