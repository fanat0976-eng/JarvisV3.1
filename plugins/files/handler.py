"""
Files plugin — Enhanced filesystem operations.
Adapted from V2.1 for V3.1.
"""
import os
import base64
import shutil
import hashlib
import threading
from pathlib import Path
from difflib import unified_diff
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

WORKSPACE = str(Path(__file__).parent.parent.parent / "workspace")
os.makedirs(WORKSPACE, exist_ok=True)

_bus = None
_bus_lock = threading.Lock()


def _is_safe_path(filepath: str) -> bool:
    try:
        resolved = str(Path(filepath).resolve())
        workspace_resolved = str(Path(WORKSPACE).resolve())
        return resolved.startswith(workspace_resolved)
    except Exception:
        return False


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
        bus.emit(topic, data, source="files")


@router.get("/health")
def health():
    return {"status": "ok", "workspace": WORKSPACE}


@router.post("/ls")
async def ls(request: Request):
    data = await request.json()
    path = data.get("path", WORKSPACE)
    if not _is_safe_path(path):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        items = []
        target = Path(path) if path else Path(WORKSPACE)
        for item in sorted(target.iterdir()):
            stat = item.stat()
            items.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime,
            })
        return {"items": items, "path": str(target)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/read")
async def read_file(request: Request):
    data = await request.json()
    filepath = data.get("path", "")
    if not _is_safe_path(filepath):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    if not os.path.exists(filepath):
        return JSONResponse({"error": f"File not found: {filepath}"}, status_code=404)
    ext = Path(filepath).suffix.lower()
    try:
        if ext in [".xlsx", ".xls"]:
            import pandas as pd
            df = pd.read_excel(filepath, dtype=str).fillna("")
            return {"type": "excel", "rows": len(df), "columns": list(df.columns),
                    "data": df.head(200).to_dict(orient="records")}
        elif ext == ".csv":
            import pandas as pd
            df = pd.read_csv(filepath, encoding="utf-8", dtype=str).fillna("")
            return {"type": "csv", "rows": len(df), "columns": list(df.columns),
                    "data": df.head(200).to_dict(orient="records")}
        elif ext == ".pdf":
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            return {"type": "pdf", "text": text[:50000]}
        elif ext == ".docx":
            from docx import Document
            doc = Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return {"type": "docx", "text": text[:50000]}
        else:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return {"type": "text", "text": text[:50000]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/write")
async def write_file(request: Request):
    data = await request.json()
    filepath = data.get("path", "")
    content = data.get("content", "")
    if not _is_safe_path(filepath):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        os.makedirs(os.path.dirname(filepath) or WORKSPACE, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        _emit("file.changed", {"action": "write", "path": filepath, "size": len(content)})
        return {"status": "ok", "path": filepath}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/mkdir")
async def mkdir(request: Request):
    data = await request.json()
    path = data.get("path", "")
    if not _is_safe_path(path):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        os.makedirs(path, exist_ok=True)
        _emit("file.changed", {"action": "mkdir", "path": path})
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/rm")
async def rm(request: Request):
    data = await request.json()
    path = data.get("path", "")
    if not _is_safe_path(path):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        _emit("file.changed", {"action": "delete", "path": path})
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/mv")
async def mv(request: Request):
    data = await request.json()
    src, dst = data.get("src", ""), data.get("dst", "")
    if not _is_safe_path(src) or not _is_safe_path(dst):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        shutil.move(src, dst)
        _emit("file.changed", {"action": "move", "src": src, "dst": dst})
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/cp")
async def cp(request: Request):
    data = await request.json()
    src, dst = data.get("src", ""), data.get("dst", "")
    if not _is_safe_path(src) or not _is_safe_path(dst):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        shutil.copy2(src, dst)
        _emit("file.changed", {"action": "copy", "src": src, "dst": dst})
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/search")
async def search_files(request: Request):
    data = await request.json()
    query = data.get("query", "")
    path = data.get("path", WORKSPACE)
    if not _is_safe_path(path):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    if not query:
        return JSONResponse({"error": "No query"}, status_code=400)
    results = []
    query_lower = query.lower()
    for f in Path(path).rglob("*"):
        if not f.is_file() or f.stat().st_size > 1_000_000:
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read(100_000)
            if query_lower in content.lower():
                lines = content.split("\n")
                matches = []
                for i, line in enumerate(lines, 1):
                    if query_lower in line.lower():
                        matches.append({"line": i, "text": line.strip()[:200]})
                        if len(matches) >= 3:
                            break
                results.append({"path": str(f), "name": f.name, "matches": matches})
        except Exception:
            continue
        if len(results) >= 20:
            break
    return {"results": results, "query": query, "count": len(results)}


@router.post("/diff")
async def diff_files(request: Request):
    data = await request.json()
    file_a, file_b = data.get("file_a", ""), data.get("file_b", "")
    if not _is_safe_path(file_a) or not _is_safe_path(file_b):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        with open(file_a, "r", encoding="utf-8", errors="replace") as f:
            lines_a = f.readlines()
        with open(file_b, "r", encoding="utf-8", errors="replace") as f:
            lines_b = f.readlines()
        diff = list(unified_diff(lines_a, lines_b, fromfile=Path(file_a).name, tofile=Path(file_b).name))
        return {"diff": "".join(diff), "lines_added": sum(1 for l in diff if l.startswith("+")),
                "lines_removed": sum(1 for l in diff if l.startswith("-"))}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/open")
async def open_file(request: Request):
    data = await request.json()
    filepath = data.get("path", "")
    if not _is_safe_path(filepath):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    if not os.path.exists(filepath):
        return JSONResponse({"error": f"File not found: {filepath}"}, status_code=404)
    try:
        os.startfile(filepath)
        return {"status": "ok", "opened": filepath}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/hash")
async def file_hash(request: Request):
    data = await request.json()
    filepath = data.get("path", "")
    if not _is_safe_path(filepath):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return {"hash": h.hexdigest(), "path": filepath}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/tree")
async def file_tree(request: Request):
    data = await request.json()
    path = data.get("path", WORKSPACE)
    max_depth = data.get("max_depth", 2)
    if not _is_safe_path(path):
        return JSONResponse({"error": "Access denied: path outside workspace"}, status_code=403)

    def build_tree(directory, depth=0):
        if depth > max_depth:
            return []
        items = []
        try:
            for item in sorted(Path(directory).iterdir()):
                node = {"name": item.name, "path": str(item), "is_dir": item.is_dir()}
                if item.is_dir() and depth < max_depth:
                    node["children"] = build_tree(item, depth + 1)
                else:
                    node["size"] = item.stat().st_size if item.is_file() else 0
                items.append(node)
        except PermissionError:
            pass
        return items

    return {"tree": build_tree(path), "root": path}
