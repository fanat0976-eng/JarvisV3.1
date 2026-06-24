"""
Memory V2 Plugin — Долгосрочная память Jarvis V3.1.
Facts, entities, relations, consolidation.
"""
import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


def _get_conn():
    from core.db import get_memory_conn
    return get_memory_conn()


# ── Health ──

@router.get("/health")
def health():
    conn = _get_conn()
    facts = conn.execute("SELECT COUNT(*) as c FROM facts").fetchone()["c"]
    sessions = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    messages = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
    return {"status": "ok", "facts": facts, "sessions": sessions, "messages": messages}


# ── Facts CRUD ──

@router.post("/facts")
async def add_fact(request: Request):
    data = await request.json()
    entity = data.get("entity", "user")
    key = data.get("key", "")
    value = data.get("value", "")
    confidence = data.get("confidence", 1.0)
    source = data.get("source", "")

    if not key or not value:
        return JSONResponse({"error": "key and value required"}, status_code=400)

    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO facts (entity, key, value, confidence, source, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(entity, key) DO UPDATE SET "
        "value = excluded.value, confidence = excluded.confidence, "
        "source = excluded.source, updated_at = excluded.updated_at, access_count = access_count + 1",
        (entity, key, value, confidence, source, now, now)
    )
    conn.commit()
    return {"status": "ok", "entity": entity, "key": key, "value": value}


@router.post("/facts/get")
async def get_facts(request: Request):
    data = await request.json()
    entity = data.get("entity", "")
    key = data.get("key", "")
    limit = data.get("limit", 50)

    conn = _get_conn()
    if entity and key:
        row = conn.execute(
            "SELECT * FROM facts WHERE entity = ? AND key = ?", (entity, key)
        ).fetchone()
        if row:
            return {"found": True, "fact": dict(row)}
        return {"found": False}

    if entity:
        rows = conn.execute(
            "SELECT * FROM facts WHERE entity = ? ORDER BY access_count DESC LIMIT ?",
            (entity, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM facts ORDER BY access_count DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"facts": [dict(r) for r in rows], "count": len(rows)}


@router.post("/facts/delete")
async def delete_fact(request: Request):
    data = await request.json()
    entity = data.get("entity", "")
    key = data.get("key", "")

    if not key:
        return JSONResponse({"error": "key required"}, status_code=400)

    conn = _get_conn()
    if entity:
        conn.execute("DELETE FROM facts WHERE entity = ? AND key = ?", (entity, key))
    else:
        conn.execute("DELETE FROM facts WHERE key = ?", (key,))
    conn.commit()
    return {"status": "ok", "key": key}


# ── Entities ──

@router.post("/entities")
async def add_entity(request: Request):
    data = await request.json()
    source = data.get("source", "")
    target = data.get("target", "")
    relation = data.get("relation", "")
    metadata = json.dumps(data.get("metadata", {}))

    if not source or not target or not relation:
        return JSONResponse({"error": "source, target, relation required"}, status_code=400)

    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO relations (source_entity, target_entity, relation_type, metadata, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (source, target, relation, metadata, now)
    )
    conn.commit()
    return {"status": "ok", "source": source, "target": target, "relation": relation}


@router.post("/entities/get")
async def get_entities(request: Request):
    data = await request.json()
    entity = data.get("entity", "")
    limit = data.get("limit", 50)

    conn = _get_conn()
    if entity:
        rows = conn.execute(
            "SELECT * FROM relations WHERE source_entity = ? OR target_entity = ? LIMIT ?",
            (entity, entity, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM relations ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return {"relations": [dict(r) for r in rows], "count": len(rows)}


# ── Sessions ──

@router.post("/session/start")
async def session_start(request: Request):
    data = await request.json()
    session_id = data.get("id", f"ses_{int(time.time() * 1000)}")
    title = data.get("title", "")

    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO sessions (id, started_at, title) VALUES (?, ?, ?)",
        (session_id, datetime.now(timezone.utc).isoformat(), title)
    )
    conn.commit()
    return {"status": "ok", "session_id": session_id}


@router.post("/session/end")
async def session_end(request: Request):
    data = await request.json()
    session_id = data.get("id", "")

    conn = _get_conn()
    conn.execute(
        "UPDATE sessions SET ended_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), session_id)
    )
    conn.commit()
    return {"status": "ok"}


@router.get("/sessions")
def list_sessions(limit: int = 20):
    conn = _get_conn()
    rows = conn.execute("""
        SELECT s.id, s.started_at, s.ended_at, s.title,
               COUNT(m.id) as message_count
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        GROUP BY s.id
        ORDER BY s.started_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return {"sessions": [dict(r) for r in rows]}


# ── History ──

@router.post("/history")
async def get_history(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "")
    limit = data.get("limit", 50)
    sessions_back = data.get("sessions", 1)

    conn = _get_conn()
    if session_id:
        rows = conn.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
    else:
        session_ids = [r["id"] for r in conn.execute(
            "SELECT id FROM sessions ORDER BY started_at DESC LIMIT ?", (sessions_back,)
        ).fetchall()]
        if not session_ids:
            return {"messages": [], "sessions": []}
        placeholders = ",".join(["?" for _ in session_ids])
        rows = conn.execute(
            f"SELECT role, content, timestamp, session_id FROM messages WHERE session_id IN ({placeholders}) ORDER BY id DESC LIMIT ?",
            (*session_ids, limit)
        ).fetchall()

    messages = [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in reversed(rows)]
    return {"messages": messages}


# ── Search ──

@router.post("/search")
async def search_messages(request: Request):
    data = await request.json()
    query = data.get("query", "")
    limit = data.get("limit", 20)

    if not query:
        return JSONResponse({"error": "No query"}, status_code=400)

    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content, timestamp, session_id FROM messages WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
        (f"%{query}%", limit)
    ).fetchall()

    results = [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"], "session_id": r["session_id"]} for r in rows]
    return {"results": results, "query": query, "count": len(results)}


# ── Notes ──

@router.post("/note/set")
async def set_note(request: Request):
    data = await request.json()
    key = data.get("key", "")
    content = data.get("content", "")

    if not key or not content:
        return JSONResponse({"error": "key and content required"}, status_code=400)

    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO notes (key, content, updated_at) VALUES (?, ?, ?)",
        (key, content, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    return {"status": "ok"}


@router.post("/note/get")
async def get_note(request: Request):
    data = await request.json()
    key = data.get("key", "")

    conn = _get_conn()
    row = conn.execute("SELECT content, updated_at FROM notes WHERE key = ?", (key,)).fetchone()
    if not row:
        return {"found": False}
    return {"found": True, "content": row["content"], "updated_at": row["updated_at"]}


@router.get("/notes")
def list_notes():
    conn = _get_conn()
    rows = conn.execute("SELECT key, content, updated_at FROM notes ORDER BY updated_at DESC").fetchall()
    return {"notes": [dict(r) for r in rows]}


# ── Patterns ──

@router.get("/patterns")
def get_patterns(pattern_type: str = None, limit: int = 20):
    conn = _get_conn()
    if pattern_type:
        rows = conn.execute(
            "SELECT pattern_type, pattern_key, count, last_seen, first_seen FROM patterns WHERE pattern_type = ? ORDER BY count DESC LIMIT ?",
            (pattern_type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT pattern_type, pattern_key, count, last_seen, first_seen FROM patterns ORDER BY count DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return {"patterns": [dict(r) for r in rows]}


@router.get("/patterns/top")
def get_top_patterns():
    conn = _get_conn()
    keywords = [dict(r) for r in conn.execute(
        "SELECT pattern_key as key, count FROM patterns WHERE pattern_type = 'keyword' ORDER BY count DESC LIMIT 10"
    ).fetchall()]
    commands = [dict(r) for r in conn.execute(
        "SELECT pattern_key as key, count FROM patterns WHERE pattern_type = 'command' ORDER BY count DESC LIMIT 10"
    ).fetchall()]
    return {"keywords": keywords, "commands": commands}


# ── Insights ──

@router.get("/insights")
def get_insights():
    conn = _get_conn()
    total_messages = conn.execute("SELECT COUNT(*) as c FROM messages WHERE role = 'user'").fetchone()["c"]
    total_sessions = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    total_facts = conn.execute("SELECT COUNT(*) as c FROM facts").fetchone()["c"]
    top_keyword = conn.execute(
        "SELECT pattern_key, count FROM patterns WHERE pattern_type = 'keyword' ORDER BY count DESC LIMIT 1"
    ).fetchone()
    active_days = conn.execute(
        "SELECT COUNT(DISTINCT DATE(timestamp)) as c FROM messages"
    ).fetchone()["c"]

    insights = []
    if top_keyword:
        insights.append(f"Most used word: '{top_keyword['pattern_key']}' ({top_keyword['count']} times)")
    if total_sessions > 0:
        avg = total_messages / total_sessions
        insights.append(f"Average {avg:.0f} messages per session")

    return {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
        "total_facts": total_facts,
        "active_days": active_days,
        "insights": insights,
    }


# ── Export ──

@router.get("/export")
def export_data():
    conn = _get_conn()
    facts = [dict(r) for r in conn.execute("SELECT * FROM facts ORDER BY entity, key").fetchall()]
    sessions = [dict(r) for r in conn.execute("SELECT * FROM sessions ORDER BY started_at").fetchall()]
    messages = [dict(r) for r in conn.execute("SELECT * FROM messages ORDER BY id").fetchall()]
    notes = [dict(r) for r in conn.execute("SELECT * FROM notes ORDER BY updated_at").fetchall()]
    relations = [dict(r) for r in conn.execute("SELECT * FROM relations ORDER BY created_at").fetchall()]
    return {"facts": facts, "sessions": sessions, "messages": messages, "notes": notes, "relations": relations}


def on_startup():
    print("  [memory_v2] Initialized: facts + entities + consolidation")


def on_shutdown():
    print("  [memory_v2] Shutdown complete")
