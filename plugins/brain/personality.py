"""
Brain Personality — Адаптивный system prompt.
Формируется на основе накопленных фактов о пользователе + мультиязычность.
"""
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.language import get_system_prompt, detect_language


def _tokenize(text: str) -> set[str]:
    words = re.findall(r'\w{2,}', text.lower())
    stop = {"я", "ты", "мы", "он", "она", "вы", "как", "что", "где", "когда",
            "покажи", "сделай", "дай", "найди", "прочитай", "открой", "запусти",
            "напиши", "создай", "объясни", "про", "для", "это", "все", "всё"}
    return {w for w in words if w not in stop}


def _fact_relevance(fact: dict, query_tokens: set[str]) -> float:
    if not query_tokens:
        return fact.get("confidence", 0.5)
    key_tokens = _tokenize(fact.get("key", ""))
    value_tokens = _tokenize(fact.get("value", ""))
    fact_tokens = key_tokens | value_tokens
    overlap = len(query_tokens & fact_tokens)
    query_boost = min(overlap / max(len(query_tokens), 1), 1.0)
    confidence = fact.get("confidence", 0.5)
    access = min(fact.get("access_count", 0) / 10, 0.3)
    return query_boost * 0.6 + confidence * 0.3 + access * 0.1


class PersonalityEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self):
        from core.db import get_memory_conn
        return get_memory_conn()

    def get_user_facts(self, entity: str = "user") -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT key, value, confidence, access_count FROM facts WHERE entity = ? ORDER BY access_count DESC LIMIT 20",
            (entity,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_project_facts(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT key, value, confidence, access_count FROM facts WHERE entity = 'project' ORDER BY access_count DESC LIMIT 10"
        ).fetchall()
        return [dict(r) for r in rows]

    def _rank_facts(self, facts: list[dict], query: str, limit: int) -> list[dict]:
        if not facts:
            return []
        query_tokens = _tokenize(query) if query else set()
        scored = [(_fact_relevance(f, query_tokens), f) for f in facts]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:limit]]

    def build_system_prompt(self, query: str = "", language: str = None) -> str:
        if not language:
            language = detect_language(query)

        base_prompt = get_system_prompt(language)
        user_facts = self.get_user_facts("user")
        project_facts = self.get_project_facts()

        sections = [base_prompt]

        if user_facts:
            top_user = self._rank_facts(user_facts, query, limit=8)
            facts_text = "\n".join(f"- {f['key']}: {f['value']}" for f in top_user)
            label = "About user:" if language == "en" else "О пользователе:" if language == "ru" else "Туралы:"
            sections.append(f"\n{label}\n{facts_text}")

        if project_facts:
            top_project = self._rank_facts(project_facts, query, limit=5)
            facts_text = "\n".join(f"- {f['key']}: {f['value']}" for f in top_project)
            label = "Active projects:" if language == "en" else "Активные проекты:" if language == "ru" else "Белсенді жобалар:"
            sections.append(f"\n{label}\n{facts_text}")

        return "\n".join(sections)

    def extract_user_preference(self, key: str, value: str, confidence: float = 0.8):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO facts (entity, key, value, confidence, created_at, updated_at) "
            "VALUES ('user', ?, ?, ?, datetime('now'), datetime('now')) "
            "ON CONFLICT(entity, key) DO UPDATE SET "
            "value = excluded.value, confidence = excluded.confidence, "
            "updated_at = datetime('now'), access_count = access_count + 1",
            (key, value, confidence)
        )
        conn.commit()

    def delete_fact(self, entity: str, key: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM facts WHERE entity = ? AND key = ?", (entity, key))
        conn.commit()
