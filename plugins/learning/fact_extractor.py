"""
Fact Extractor — Автоматическое извлечение фактов из диалогов.
Парсит ответы пользователя на паттерны: "я работаю над X", "мне нравится X" и т.д.
"""
import re
from datetime import datetime, timezone


FACT_PATTERNS = [
    (r"я работаю над\s+(.+)", "project"),
    (r"я использую\s+(.+)", "tool"),
    (r"мне нравится\s+(.+)", "preference"),
    (r"я пишу на\s+(.+)", "language"),
    (r"мой проект\s+[«\"]?(.+?)[»\"]?\s*$", "project"),
    (r"я изучаю\s+(.+)", "learning"),
    (r"я хочу\s+(.+)", "goal"),
    (r"мне нужно\s+(.+)", "need"),
]

STOP_WORDS = {"я", "ты", "мы", "он", "она", "вы", "это", "вот", "тут", "там",
              "да", "нет", "ок", "хорошо", "плохо", "может", "быть", "будет",
              "было", "был", "была", "были", "есть", "нет", "или", "и", "а",
              "но", "что", "как", "где", "когда", "почему", "зачем"}


def _clean_value(value: str) -> str:
    value = value.strip().strip(".,;:!?")
    value = re.sub(r'\s+', ' ', value)
    words = value.split()
    words = [w for w in words if w.lower() not in STOP_WORDS]
    return " ".join(words).strip()


def extract_facts(text: str) -> list[dict]:
    facts = []
    text_lower = text.lower()
    for pattern, category in FACT_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            raw_value = match.group(1)
            value = _clean_value(raw_value)
            if len(value) > 2 and len(value) < 200:
                facts.append({"category": category, "value": value})
    return facts


def store_extracted_facts(facts: list[dict], source: str = "auto"):
    if not facts:
        return
    from core.db import get_memory_conn
    conn = get_memory_conn()
    now = datetime.now(timezone.utc).isoformat()
    for fact in facts:
        conn.execute(
            "INSERT INTO facts (entity, key, value, confidence, source, created_at, updated_at) "
            "VALUES ('user', ?, ?, 0.6, ?, ?, ?) "
            "ON CONFLICT(entity, key) DO UPDATE SET "
            "access_count = access_count + 1, updated_at = ?",
            (fact["category"], fact["value"], source, now, now, now)
        )
    conn.commit()


def process_message(user_text: str, message_id: str = "") -> list[dict]:
    facts = extract_facts(user_text)
    if facts:
        store_extracted_facts(facts)
    return facts
