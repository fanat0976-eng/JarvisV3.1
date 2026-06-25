"""
Brain Context Manager — Управление контекстом разговора.
Sliding window + compression для длинных сессий.
"""


class ContextManager:
    def __init__(self, db_path: str, max_tokens: int = 4096):
        self.db_path = db_path
        self.max_tokens = max_tokens

    def _get_conn(self):
        from core.db import get_memory_conn
        return get_memory_conn()

    def load_recent(self, n_messages: int = 20, sessions_back: int = 2) -> list[dict]:
        conn = self._get_conn()
        session_ids = [r["id"] for r in conn.execute(
            "SELECT id FROM sessions ORDER BY started_at DESC LIMIT ?", (sessions_back,)
        ).fetchall()]

        if not session_ids:
            return []

        placeholders = ",".join(["?" for _ in session_ids])
        rows = conn.execute(
            f"SELECT role, content, timestamp FROM messages "
            f"WHERE session_id IN ({placeholders}) ORDER BY id DESC LIMIT ?",
            (*session_ids, n_messages)
        ).fetchall()

        messages = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
        return self._trim_to_tokens(messages)

    def _trim_to_tokens(self, messages: list[dict]) -> list[dict]:
        total_chars = 0
        char_budget = self.max_tokens * 4
        result = []
        for msg in reversed(messages):
            msg_chars = len(msg["content"])
            if total_chars + msg_chars > char_budget:
                break
            result.append(msg)
            total_chars += msg_chars
        result.reverse()
        return result

    def build_messages(
        self,
        user_message: str,
        system_prompt: str = "",
        facts: list[str] | None = None,
        n_context: int = 20,
    ) -> list[dict]:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        context = self.load_recent(n_context)
        messages.extend(context)

        messages.append({"role": "user", "content": user_message})

        return messages
