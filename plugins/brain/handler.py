"""
Brain Plugin — Ядро мышления Jarvis V3.1.
Маршрутизация, контекст, personality, tool execution.
"""
import json
import os
import re
import time
from pathlib import Path
from datetime import datetime, timezone

import httpx as httpx_lib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from plugins.brain.router import BrainRouter
from plugins.brain.context import ContextManager
from plugins.brain.personality import PersonalityEngine
from plugins.brain.tool_executor import parse_tool_calls, execute_tool_call, get_tool_descriptions

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.language import detect_language, get_supported_languages, get_greeting

try:
    from plugins.learning.fact_extractor import process_message as _learn_facts
    from plugins.learning.router_learner import record_outcome as _learn_outcome
    _LEARNING_AVAILABLE = True
except ImportError:
    _LEARNING_AVAILABLE = False

router = APIRouter()

DATA_DIR = str(Path(__file__).parent.parent.parent / "data")
DB_PATH = os.path.join(DATA_DIR, "memory.db")

brain_router = BrainRouter()
context_manager = ContextManager(DB_PATH)
personality = PersonalityEngine(DB_PATH)


def _get_conn():
    from core.db import get_memory_conn
    return get_memory_conn()


def _init_brain_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            title TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tokens INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        );
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY,
            entity TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            access_count INTEGER DEFAULT 0,
            UNIQUE(entity, key)
        );
        CREATE TABLE IF NOT EXISTS relations (
            id INTEGER PRIMARY KEY,
            source_entity TEXT NOT NULL,
            target_entity TEXT NOT NULL,
            relation_type TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS consolidated (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            summary TEXT NOT NULL,
            facts_extracted INTEGER DEFAULT 0,
            consolidated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            pattern_key TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            last_seen TEXT NOT NULL,
            first_seen TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            UNIQUE(pattern_type, pattern_key)
        );
        CREATE TABLE IF NOT EXISTS hourly_usage (
            hour INTEGER PRIMARY KEY,
            total_messages INTEGER DEFAULT 0,
            total_sessions INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
        CREATE INDEX IF NOT EXISTS idx_facts_entity ON facts(entity);
    """)


async def get_rag_context(query: str, n_results: int = 3) -> str:
    """Retrieve relevant context from RAG."""
    try:
        from plugins.rag.handler import ask_rag
        result = await ask_rag(query, n_results)
        return result.get("context", "")
    except Exception:
        pass
    return ""


def _save_message(session_id: str, role: str, content: str):
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, now)
    )
    conn.commit()


def _track_patterns(content: str):
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    words = content.lower().split()
    stop = {"я", "ты", "мы", "он", "она", "вы", "как", "что", "где", "когда",
            "покажи", "сделай", "дай", "найди", "прочитай", "открой", "запусти"}
    for w in words[:5]:
        if len(w) > 2 and w not in stop:
            conn.execute(
                "INSERT INTO patterns (pattern_type, pattern_key, count, last_seen, first_seen) "
                "VALUES ('keyword', ?, 1, ?, ?) "
                "ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET count = count + 1, last_seen = ?",
                (w, now, now, now)
            )
    hour = datetime.now(timezone.utc).hour
    conn.execute(
        "INSERT INTO hourly_usage (hour, total_messages) VALUES (?, 1) "
        "ON CONFLICT(hour) DO UPDATE SET total_messages = total_messages + 1",
        (hour,)
    )
    conn.commit()


# ── Health ──

@router.get("/health")
async def health():
    ollama_ok = False
    models = []
    try:
        async with httpx_lib.AsyncClient(trust_env=False, timeout=3) as client:
            r = await client.get("http://localhost:11434/api/tags")
            ollama_ok = r.status_code == 200
            models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return {"status": "ok", "ollama": ollama_ok, "models": models, "router": brain_router.default_model}


# ── Chat (main endpoint) ──

@router.post("/chat")
async def chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    session_id = data.get("session_id", f"ses_{int(time.time() * 1000)}")
    use_memory = data.get("use_memory", True)

    user_text = messages[-1].get("content", "") if messages else ""
    lang = data.get("language") or detect_language(user_text)

    route = brain_router.route(user_text)

    system_prompt = personality.build_system_prompt(query=user_text, language=lang) if use_memory else ""

    rag_context = await get_rag_context(user_text)
    if rag_context:
        system_prompt += f"\n\nRelevant knowledge:\n{rag_context}"

    context_messages = context_manager.build_messages(
        user_text, system_prompt=system_prompt, n_context=20
    )

    payload = {
        "model": route["model"],
        "messages": context_messages,
        "stream": False,
        "options": {"temperature": route["temperature"], "top_p": 0.9, "num_predict": 2048},
    }

    try:
        async with httpx_lib.AsyncClient(trust_env=False, timeout=300) as client:
            r = await client.post("http://localhost:11434/api/chat", json=payload)
            r.raise_for_status()
            reply = r.json().get("message", {}).get("content", "")

        tool_calls = parse_tool_calls(reply)
        tool_results = []
        for tc in tool_calls:
            result = execute_tool_call(tc, memory_engine=personality)
            tool_results.append(result)

        clean_reply = re.sub(r'<<<TOOL_CALL>>>.*?<<<END_TOOL_CALL>>>', '', reply, flags=re.DOTALL).strip()

        _save_message(session_id, "user", user_text)
        _save_message(session_id, "assistant", clean_reply)
        _track_patterns(user_text)

        if _LEARNING_AVAILABLE:
            try:
                _learn_facts(user_text)
                _learn_outcome(route["model"], route["task_type"], len(clean_reply) > 10)
            except Exception:
                pass

        return {
            "reply": clean_reply,
            "model": route["model"],
            "task_type": route["task_type"],
            "tool_calls": len(tool_calls),
            "tool_results": tool_results,
            "session_id": session_id,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Chat with streaming ──

@router.post("/chat/stream")
async def chat_stream(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    session_id = data.get("session_id", f"ses_{int(time.time() * 1000)}")
    use_memory = data.get("use_memory", True)

    user_text = messages[-1].get("content", "") if messages else ""
    lang = data.get("language") or detect_language(user_text)

    route = brain_router.route(user_text)

    system_prompt = personality.build_system_prompt(query=user_text, language=lang) if use_memory else ""

    rag_context = await get_rag_context(user_text)
    if rag_context:
        system_prompt += f"\n\nRelevant knowledge:\n{rag_context}"

    context_messages = context_manager.build_messages(
        user_text, system_prompt=system_prompt, n_context=20
    )

    payload = {
        "model": route["model"],
        "messages": context_messages,
        "stream": True,
        "options": {"temperature": route["temperature"], "top_p": 0.9, "num_predict": 2048},
    }

    async def generate():
        full_text = ""
        try:
            async with httpx_lib.AsyncClient(trust_env=False, timeout=300) as client:
                async with client.stream("POST", "http://localhost:11434/api/chat", json=payload) as r:
                    async for line in r.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    full_text += content
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        tool_calls = parse_tool_calls(full_text)
        tool_results = []
        for tc in tool_calls:
            result = execute_tool_call(tc, memory_engine=personality)
            tool_results.append(result)
        if tool_results:
            yield f"data: {json.dumps({'tool_results': tool_results})}\n\n"

        clean_reply = re.sub(r'<<<TOOL_CALL>>>.*?<<<END_TOOL_CALL>>>', '', full_text, flags=re.DOTALL).strip()
        _save_message(session_id, "user", user_text)
        _save_message(session_id, "assistant", clean_reply)
        _track_patterns(user_text)

        if _LEARNING_AVAILABLE:
            try:
                _learn_facts(user_text)
                _learn_outcome(route["model"], route["task_type"], len(clean_reply) > 10)
            except Exception:
                pass

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Agent mode (with tool execution loop) ──

@router.post("/agent")
async def agent_chat(request: Request):
    data = await request.json()
    messages = data.get("messages", [])
    session_id = data.get("session_id", f"ses_{int(time.time() * 1000)}")
    max_iterations = min(data.get("max_iterations", 3), 10)

    user_text = messages[-1].get("content", "") if messages else ""
    lang = data.get("language") or detect_language(user_text)

    route = brain_router.route(user_text, has_tool_context=True)

    system_prompt = personality.build_system_prompt(query=user_text, language=lang)
    tool_descriptions = get_tool_descriptions()
    system_prompt += f"\n\nДОСТУПНЫЕ ИНСТРУМЕНТЫ:\n{tool_descriptions}\n\nДля вызова инструмента ответь в формате (каждый параметр на новой строке):\n<<<TOOL_CALL>>>\ntool: <название>\n<параметр1>: <значение>\n<параметр2>: <значение>\n<<<END_TOOL_CALL>>>\n\nПримеры:\n<<<TOOL_CALL>>>\ntool: web/search\nquery: проблемы ИИ 2026\nmax_results: 3\n<<<END_TOOL_CALL>>>\n\n<<<TOOL_CALL>>>\ntool: files/write\npath: workspace/report.md\ncontent: # Отчёт\nТекст отчёта...\n<<<END_TOOL_CALL>>>\n\nВАЖНО: параметр path ОБЯЗАТЕЛЕН для files/write и files/read. Используй workspace/ как базовую папку."

    all_messages = messages.copy()
    all_tool_results = []
    iteration = 0

    while iteration < max_iterations:
        context_messages = context_manager.build_messages(
            user_text, system_prompt=system_prompt, n_context=20
        )
        context_messages.extend(all_messages)

        payload = {
            "model": route["model"],
            "messages": context_messages,
            "stream": False,
            "options": {"temperature": route["temperature"], "top_p": 0.9, "num_predict": 4096},
        }

        try:
            async with httpx_lib.AsyncClient(trust_env=False, timeout=300) as client:
                r = await client.post("http://localhost:11434/api/chat", json=payload)
                r.raise_for_status()
                reply = r.json().get("message", {}).get("content", "")
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

        tool_calls = parse_tool_calls(reply)
        if not tool_calls:
            clean_reply = reply.strip()
            break

        for tc in tool_calls:
            result = execute_tool_call(tc, memory_engine=personality)
            all_tool_results.append(result)

        tool_summary = "\n".join(
            f"[{tr['tool']}] {'OK' if tr.get('status') == 'ok' else 'ERROR'}: "
            + str(tr.get('text', tr.get('error', tr.get('path', tr.get('items', '')))))[:500]
            for tr in all_tool_results
        )

        all_messages.append({"role": "assistant", "content": reply})
        all_messages.append({"role": "user", "content": f"Результаты инструментов:\n{tool_summary}\n\nПродолжи работу."})

        iteration += 1

    clean_reply = re.sub(r'<<<TOOL_CALL>>>.*?<<<END_TOOL_CALL>>>', '', reply, flags=re.DOTALL).strip()

    _save_message(session_id, "user", user_text)
    _save_message(session_id, "assistant", clean_reply)
    _track_patterns(user_text)

    if _LEARNING_AVAILABLE:
        try:
            _learn_facts(user_text)
            _learn_outcome(route["model"], route["task_type"], len(clean_reply) > 10)
        except Exception:
            pass

    return {
        "reply": clean_reply,
        "model": route["model"],
        "task_type": route["task_type"],
        "tool_calls": len(all_tool_results),
        "tool_results": all_tool_results,
        "iterations": iteration,
        "session_id": session_id,
    }


# ── Personality ──

@router.get("/personality")
def get_personality():
    facts = personality.get_user_facts("user")
    return {"facts": facts, "count": len(facts)}


@router.post("/personality/remember")
async def remember_fact(request: Request):
    data = await request.json()
    key = data.get("key", "")
    value = data.get("value", "")
    confidence = data.get("confidence", 0.8)
    if not key or not value:
        return JSONResponse({"error": "key and value required"}, status_code=400)
    personality.extract_user_preference(key, value, confidence)
    return {"status": "ok", "key": key, "value": value}


# ── Context ──

@router.get("/context")
def get_context(limit: int = 20):
    messages = context_manager.load_recent(limit)
    return {"messages": messages, "count": len(messages)}


# ── Language ──

@router.get("/languages")
def languages():
    return {"languages": get_supported_languages()}


@router.post("/detect")
async def detect(request: Request):
    data = await request.json()
    text = data.get("text", "")
    lang = detect_language(text)
    return {"language": lang, "greeting": get_greeting(lang)}


# ── Stats ──

@router.get("/stats")
def get_stats():
    conn = _get_conn()
    sessions = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()[0]
    messages = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()[0]
    facts = conn.execute("SELECT COUNT(*) as c FROM facts").fetchone()[0]
    patterns = conn.execute("SELECT COUNT(*) as c FROM patterns").fetchone()[0]
    return {"sessions": sessions, "messages": messages, "facts": facts, "patterns": patterns}


def on_startup():
    _init_brain_db()
    print("  [brain] Initialized: router + context + personality + multilingual")


def on_shutdown():
    print("  [brain] Shutdown complete")
