"""
Brain Tool Executor — Исполнение tool calls из ответов LLM.
Расширение V2.1: добавлены memory tools для агента.
"""
import os
import re
import shutil
from pathlib import Path

WORKSPACE = str(Path(__file__).parent.parent.parent / "workspace")

TOOL_DEFINITIONS = {
    "files/ls": "Список файлов в папке",
    "files/read": "Чтение файла",
    "files/write": "Запись в файл",
    "files/mkdir": "Создание папки",
    "files/rm": "Удаление файла",
    "files/mv": "Перемещение/переименование",
    "files/cp": "Копирование",
    "files/search": "Поиск по содержимому",
    "memory/remember": "Запомнить факт",
    "memory/recall": "Вспомнить факты по запросу",
    "memory/forget": "Забыть факт",
    "web/search": "Поиск в интернете через DuckDuckGo",
    "web/fetch": "Чтение содержимого веб-страницы по URL",
}


def _safe_path(path: str) -> str:
    workspace = Path(WORKSPACE).resolve()
    p = Path(path)
    if p.is_absolute() or path.startswith(("/", "\\")):
        resolved = p.resolve()
        if str(resolved).startswith(str(workspace)):
            return str(resolved)
        return str(workspace / p.name)
    return str((workspace / p).resolve())


def parse_tool_calls(text: str) -> list[str]:
    pattern = r'<<<TOOL_CALL>>>(.*?)<<<END_TOOL_CALL>>>'
    return re.findall(pattern, text, re.DOTALL)


def execute_tool_call(tool_str: str, memory_engine=None) -> dict:
    lines = tool_str.strip().split("\n")
    params = {}
    content_lines = []
    in_content = False

    for line in lines:
        if in_content:
            content_lines.append(line)
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            if key == "content":
                in_content = True
                content_lines.append(val)
            elif key == "tool":
                params["tool"] = val
            else:
                params[key] = val

    tool = params.get("tool", "")
    result = {"tool": tool, "status": "error", "error": f"Unknown tool: {tool}"}

    try:
        if tool == "files/ls":
            target = _safe_path(params.get("path", WORKSPACE))
            items = []
            for item in sorted(Path(target).iterdir()):
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": stat.st_size if item.is_file() else 0,
                })
            result = {"tool": tool, "status": "ok", "items": items, "path": target}

        elif tool == "files/read":
            filepath = _safe_path(params.get("path", ""))
            if not os.path.exists(filepath):
                result = {"tool": tool, "status": "error", "error": f"Not found: {filepath}"}
            else:
                ext = Path(filepath).suffix.lower()
                if ext == ".pdf":
                    import pdfplumber
                    with pdfplumber.open(filepath) as pdf:
                        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                    result = {"tool": tool, "status": "ok", "type": "pdf", "text": text[:30000]}
                elif ext == ".docx":
                    from docx import Document
                    doc = Document(filepath)
                    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                    result = {"tool": tool, "status": "ok", "type": "docx", "text": text[:30000]}
                elif ext in [".xlsx", ".xls"]:
                    import pandas as pd
                    df = pd.read_excel(filepath, dtype=str).fillna("")
                    result = {"tool": tool, "status": "ok", "type": "excel",
                              "columns": list(df.columns), "rows": len(df),
                              "data": df.head(100).to_dict(orient="records")}
                elif ext == ".csv":
                    import pandas as pd
                    df = pd.read_csv(filepath, encoding="utf-8", dtype=str).fillna("")
                    result = {"tool": tool, "status": "ok", "type": "csv",
                              "columns": list(df.columns), "rows": len(df),
                              "data": df.head(100).to_dict(orient="records")}
                else:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                    result = {"tool": tool, "status": "ok", "type": "text", "text": text[:30000]}

        elif tool == "files/write":
            filepath = _safe_path(params.get("path", ""))
            if not filepath or filepath == str(Path(WORKSPACE).resolve()):
                result = {"tool": tool, "status": "error", "error": "path parameter required. Use workspace/filename.md"}
            else:
                content = "\n".join(content_lines)
                os.makedirs(os.path.dirname(filepath) or WORKSPACE, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                result = {"tool": tool, "status": "ok", "path": filepath, "bytes": len(content.encode())}

        elif tool == "files/mkdir":
            path = _safe_path(params.get("path", ""))
            os.makedirs(path, exist_ok=True)
            result = {"tool": tool, "status": "ok", "path": path}

        elif tool == "files/rm":
            path = _safe_path(params.get("path", ""))
            confirm = params.get("confirm", "").lower()
            if confirm != "yes":
                p = Path(path)
                return {
                    "tool": tool, "status": "confirm_required",
                    "path": path, "message": f"Подтвердите удаление: {path}",
                }
            p = Path(path)
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            result = {"tool": tool, "status": "ok", "path": path}

        elif tool == "files/mv":
            src = _safe_path(params.get("src", ""))
            dst = _safe_path(params.get("dst", ""))
            shutil.move(src, dst)
            result = {"tool": tool, "status": "ok", "src": src, "dst": dst}

        elif tool == "files/cp":
            src = _safe_path(params.get("src", ""))
            dst = _safe_path(params.get("dst", ""))
            shutil.copy2(src, dst)
            result = {"tool": tool, "status": "ok", "src": src, "dst": dst}

        elif tool == "files/search":
            query = params.get("query", "")
            search_path = _safe_path(params.get("path", WORKSPACE))
            results = []
            for f in Path(search_path).rglob("*"):
                if not f.is_file() or f.stat().st_size > 1_000_000:
                    continue
                try:
                    with open(f, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read(100_000)
                    if query.lower() in content.lower():
                        results.append({"path": str(f), "name": f.name})
                        if len(results) >= 10:
                            break
                except Exception:
                    continue
            result = {"tool": tool, "status": "ok", "results": results, "query": query}

        elif tool == "memory/remember":
            key = params.get("key", "")
            value = params.get("value", params.get("content", ""))
            if memory_engine and key and value:
                memory_engine.extract_user_preference(key, value)
                result = {"tool": tool, "status": "ok", "key": key, "value": value}
            else:
                result = {"tool": tool, "status": "error", "error": "key and value required"}

        elif tool == "memory/recall":
            query = params.get("query", params.get("key", ""))
            if memory_engine:
                facts = memory_engine.get_user_facts("user")
                matching = [f for f in facts if query.lower() in f["key"].lower() or query.lower() in f["value"].lower()]
                result = {"tool": tool, "status": "ok", "facts": matching, "query": query}
            else:
                result = {"tool": tool, "status": "error", "error": "memory not available"}

        elif tool == "memory/forget":
            key = params.get("key", "")
            if memory_engine:
                memory_engine.delete_fact("user", key)
                result = {"tool": tool, "status": "ok", "key": key}
            else:
                result = {"tool": tool, "status": "error", "error": "memory not available"}

        elif tool == "web/search":
            query = params.get("query", "")
            try:
                max_results = int(params.get("max_results", "5"))
            except (ValueError, TypeError):
                max_results = 5
            if not query:
                result = {"tool": tool, "status": "error", "error": "query required"}
            else:
                try:
                    from plugins.web.handler import search_ddg
                    results = search_ddg(query, max_results)
                    result = {"tool": tool, "status": "ok", "results": results, "query": query}
                except Exception as e:
                    result = {"tool": tool, "status": "error", "error": str(e)}

        elif tool == "web/fetch":
            url = params.get("url", "")
            if not url:
                result = {"tool": tool, "status": "error", "error": "url required"}
            else:
                try:
                    from plugins.web.handler import fetch_page
                    page = fetch_page(url)
                    result = {"tool": tool, "status": "ok", **page}
                except Exception as e:
                    result = {"tool": tool, "status": "error", "error": str(e)}

    except Exception as e:
        result = {"tool": tool, "status": "error", "error": str(e)}

    return result


def get_tool_descriptions() -> str:
    return "\n".join(f"- {name}: {desc}" for name, desc in TOOL_DEFINITIONS.items())
