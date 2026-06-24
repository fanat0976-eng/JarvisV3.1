"""
Command Learner — Детекция повторяющихся запросов и предложение shortcuts.
Анализирует patterns table и создаёт learned_commands при пороге повторений.
"""
from datetime import datetime, timedelta, timezone


REPEAT_THRESHOLD = 3
WEEK_DAYS = 7


def _get_conn():
    from core.db import get_memory_conn
    return get_memory_conn()


def detect_repeated_queries(threshold: int = REPEAT_THRESHOLD) -> list[dict]:
    conn = _get_conn()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=WEEK_DAYS)).isoformat()

    rows = conn.execute(
        "SELECT pattern_key, count, first_seen, last_seen "
        "FROM patterns "
        "WHERE pattern_type = 'keyword' AND last_seen > ? AND count >= ? "
        "ORDER BY count DESC LIMIT 20",
        (week_ago, threshold)
    ).fetchall()

    candidates = []
    for row in rows:
        key = row["pattern_key"]
        exists = conn.execute(
            "SELECT 1 FROM learned_commands WHERE phrase = ?", (key,)
        ).fetchone()
        if not exists:
            candidates.append({
                "phrase": key,
                "count": row["count"],
                "first_seen": row["first_seen"],
                "last_seen": row["last_seen"],
            })

    return candidates


def suggest_command(phrase: str, command: str = None) -> dict:
    if not command:
        words = phrase.split()[:3]
        command = "/" + "_".join(words)

    conn = _get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO learned_commands (phrase, command, count, first_seen, last_seen) "
        "VALUES (?, ?, 1, ?, ?) "
        "ON CONFLICT(phrase) DO UPDATE SET "
        "command = excluded.command, count = count + 1, last_seen = ?",
        (phrase, command, now, now, now)
    )
    conn.commit()
    return {"phrase": phrase, "command": command}


def get_learned_commands(limit: int = 20) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT phrase, command, count, first_seen, last_seen "
        "FROM learned_commands ORDER BY count DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_pending_suggestions() -> list[dict]:
    candidates = detect_repeated_queries()
    return candidates[:5]
