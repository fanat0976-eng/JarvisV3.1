"""
Jarvis V3.1 — TTL Cache
Lazy eviction, thread-safe.
"""
import threading
import time
from typing import Any, Optional


class CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.time() + ttl if ttl > 0 else float("inf")

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class Cache:
    def __init__(self):
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._store[key]
                return None
            return entry.value

    def set(self, key: str, value: Any, ttl: float = 300):
        with self._lock:
            self._store[key] = CacheEntry(value, ttl)

    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        with self._lock:
            self._store.clear()

    def cleanup(self):
        with self._lock:
            expired = [k for k, v in self._store.items() if v.is_expired()]
            for k in expired:
                del self._store[k]

    def stats(self) -> dict:
        with self._lock:
            now = time.time()
            total = len(self._store)
            expired = sum(1 for v in self._store.values() if v.is_expired())
            return {"total": total, "active": total - expired, "expired": expired}

    def get_or_set(self, key: str, factory, ttl: float = 300) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if entry is not None and not entry.is_expired():
                return entry.value
        value = factory()
        with self._lock:
            self._store[key] = CacheEntry(value, ttl)
        return value


cache = Cache()
