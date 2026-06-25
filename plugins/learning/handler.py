"""
Learning Plugin — Auto-learning API.
Предоставляет endpoints для просмотра и управления обучением.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from plugins.learning.fact_extractor import process_message, extract_facts
from plugins.learning.command_learner import (
    get_learned_commands, get_pending_suggestions, suggest_command
)
from plugins.learning.router_learner import (
    get_model_scores, get_learning_stats
)

router = APIRouter()


def _get_conn():
    from core.db import get_memory_conn
    return get_memory_conn()


def _init_learning_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS learned_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phrase TEXT UNIQUE NOT NULL,
            command TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS model_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT NOT NULL,
            task_type TEXT NOT NULL,
            successes INTEGER DEFAULT 0,
            failures INTEGER DEFAULT 0,
            last_used TEXT NOT NULL,
            UNIQUE(model, task_type)
        );
        CREATE TABLE IF NOT EXISTS extraction_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            facts_count INTEGER DEFAULT 0,
            timestamp TEXT NOT NULL
        );
    """)


def on_startup():
    _init_learning_db()
    print("  [learning] Initialized: fact_extractor + command_learner + router_learner")


@router.get("/health")
def health():
    conn = _get_conn()
    commands = conn.execute("SELECT COUNT(*) as c FROM learned_commands").fetchone()[0]
    scores = conn.execute("SELECT COUNT(*) as c FROM model_scores").fetchone()[0]
    extractions = conn.execute("SELECT COUNT(*) as c FROM extraction_log").fetchone()[0]
    return {"status": "ok", "commands": commands, "scores": scores, "extractions": extractions}


@router.get("/commands")
def list_commands(limit: int = 20):
    return {"commands": get_learned_commands(limit)}


@router.get("/suggestions")
def list_suggestions():
    return {"suggestions": get_pending_suggestions()}


@router.post("/suggest")
async def create_suggestion(request: Request):
    data = await request.json()
    phrase = data.get("phrase", "")
    command = data.get("command", None)
    if not phrase:
        return JSONResponse({"error": "phrase required"}, status_code=400)
    result = suggest_command(phrase, command)
    return {"status": "ok", **result}


@router.get("/scores")
def model_scores():
    return {"scores": get_model_scores()}


@router.get("/stats")
def stats():
    learning = get_learning_stats()
    conn = _get_conn()
    facts_auto = conn.execute(
        "SELECT COUNT(*) as c FROM facts WHERE source = 'auto'"
    ).fetchone()[0]
    facts_manual = conn.execute(
        "SELECT COUNT(*) as c FROM facts WHERE source != 'auto' OR source IS NULL"
    ).fetchone()[0]
    return {**learning, "facts_auto": facts_auto, "facts_manual": facts_manual}


@router.post("/analyze")
async def analyze_history(request: Request):
    data = await request.json() if request.headers.get("content-length", "0") != "0" else {}
    limit = data.get("limit", 100)

    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, content FROM messages WHERE role = 'user' ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()

    total_facts = 0
    all_facts = []
    for row in rows:
        facts = extract_facts(row["content"])
        if facts:
            process_message(row["content"], str(row["id"]))
            total_facts += len(facts)
            all_facts.extend(facts)

    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO extraction_log (message_id, facts_count, timestamp) VALUES (?, ?, ?)",
        ("batch", total_facts, now)
    )
    conn.commit()

    return {"status": "ok", "messages_analyzed": len(rows), "facts_extracted": total_facts, "facts": all_facts[:20]}


def on_shutdown():
    print("  [learning] Shutdown complete")
