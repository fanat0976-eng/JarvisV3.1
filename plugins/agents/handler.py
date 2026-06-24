"""
Agents Plugin — Multi-agent orchestration API.
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from plugins.agents.registry import list_agents, get_agent, classify_task
from plugins.agents.orchestrator import run_agent, orchestrate

router = APIRouter()

_tasks: dict[str, dict] = {}


def _get_conn():
    from core.db import get_memory_conn
    return get_memory_conn()


def _init_agents_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id TEXT PRIMARY KEY,
            agent TEXT NOT NULL,
            task TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
    """)


def _load_tasks_from_db():
    global _tasks
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, agent, task, status, result, created_at, completed_at "
        "FROM agent_tasks WHERE status IN ('running', 'pending') ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    for row in rows:
        _tasks[row["id"]] = {
            "id": row["id"],
            "agent": row["agent"],
            "task": row["task"],
            "status": row["status"],
            "result": row["result"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
        }


def _save_task_to_db(task_id: str):
    task = _tasks.get(task_id)
    if not task:
        return
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO agent_tasks (id, agent, task, status, result, created_at, completed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (task["id"], task["agent"], task["task"], task["status"],
         str(task.get("result", "")), task["created_at"], task.get("completed_at"))
    )
    conn.commit()


def on_startup():
    _init_agents_db()
    _load_tasks_from_db()
    print(f"  [agents] Initialized: orchestrator + code + research + file_ops ({len(_tasks)} active tasks)")


@router.get("/health")
def health():
    return {"status": "ok", "agents": len(list_agents())}


@router.get("/list")
def agents_list():
    return {"agents": list_agents()}


@router.get("/{name}")
def agent_info(name: str):
    agent = get_agent(name)
    if not agent:
        return JSONResponse({"error": f"Agent '{name}' not found"}, status_code=404)
    return {
        "name": agent.name,
        "model": agent.model,
        "description": agent.description,
        "tools": agent.tools,
        "max_iterations": agent.max_iterations,
    }


@router.post("/spawn")
async def spawn_agent(request: Request):
    data = await request.json()
    agent_name = data.get("agent", "")
    task = data.get("task", "")
    context = data.get("context", [])

    if not task:
        return JSONResponse({"error": "task required"}, status_code=400)

    if not agent_name:
        agent_name = classify_task(task)

    task_id = f"task_{int(time.time() * 1000)}"

    _tasks[task_id] = {
        "id": task_id,
        "agent": agent_name,
        "task": task,
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_task_to_db(task_id)

    result = await run_agent(agent_name, task, context)

    _tasks[task_id]["status"] = result.get("status", "error")
    _tasks[task_id]["result"] = result
    _tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    _save_task_to_db(task_id)

    return {"task_id": task_id, **result}


@router.post("/orchestrate")
async def orchestrate_task(request: Request):
    data = await request.json()
    task = data.get("task", "")
    context = data.get("context", [])

    if not task:
        return JSONResponse({"error": "task required"}, status_code=400)

    result = await orchestrate(task, context)
    return result


@router.get("/task/{task_id}")
def task_status(task_id: str):
    if task_id in _tasks:
        return _tasks[task_id]
    conn = _get_conn()
    row = conn.execute("SELECT * FROM agent_tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return dict(row)


@router.post("/task/{task_id}/cancel")
def cancel_task(task_id: str):
    if task_id in _tasks:
        _tasks[task_id]["status"] = "cancelled"
        _save_task_to_db(task_id)
    else:
        conn = _get_conn()
        conn.execute("UPDATE agent_tasks SET status = 'cancelled' WHERE id = ?", (task_id,))
        conn.commit()
    return {"status": "ok", "task_id": task_id}


def on_shutdown():
    print("  [agents] Shutdown complete")
