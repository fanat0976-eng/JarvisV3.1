"""
Router Learner — Трекинг успеха моделей по task_type.
Запоминает, какие модели дают успешные ответы для каждого типа задач.
"""
from datetime import datetime, timezone


def _get_conn():
    from core.db import get_memory_conn
    return get_memory_conn()


def record_outcome(model: str, task_type: str, success: bool):
    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    if success:
        conn.execute(
            "INSERT INTO model_scores (model, task_type, successes, failures, last_used) "
            "VALUES (?, ?, 1, 0, ?) "
            "ON CONFLICT(model, task_type) DO UPDATE SET "
            "successes = successes + 1, last_used = ?",
            (model, task_type, now, now)
        )
    else:
        conn.execute(
            "INSERT INTO model_scores (model, task_type, successes, failures, last_used) "
            "VALUES (?, ?, 0, 1, ?) "
            "ON CONFLICT(model, task_type) DO UPDATE SET "
            "failures = failures + 1, last_used = ?",
            (model, task_type, now, now)
        )
    conn.commit()


def get_model_scores() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT model, task_type, successes, failures, last_used, "
        "ROUND(CAST(successes AS FLOAT) / MAX(successes + failures, 1), 2) as success_rate "
        "FROM model_scores ORDER BY success_rate DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_best_model(task_type: str) -> str | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT model FROM model_scores "
        "WHERE task_type = ? AND (successes + failures) >= 3 "
        "ORDER BY CAST(successes AS FLOAT) / MAX(successes + failures, 1) DESC "
        "LIMIT 1",
        (task_type,)
    ).fetchone()
    return row["model"] if row else None


def get_learning_stats() -> dict:
    conn = _get_conn()
    total_models = conn.execute("SELECT COUNT(DISTINCT model) FROM model_scores").fetchone()[0]
    total_tasks = conn.execute("SELECT COUNT(DISTINCT task_type) FROM model_scores").fetchone()[0]
    total_records = conn.execute("SELECT COUNT(*) FROM model_scores").fetchone()[0]
    best_overall = conn.execute(
        "SELECT model, task_type, "
        "ROUND(CAST(successes AS FLOAT) / MAX(successes + failures, 1), 2) as rate "
        "FROM model_scores WHERE (successes + failures) >= 5 "
        "ORDER BY rate DESC LIMIT 1"
    ).fetchone()
    return {
        "total_models": total_models,
        "total_task_types": total_tasks,
        "total_records": total_records,
        "best_overall": dict(best_overall) if best_overall else None,
    }
