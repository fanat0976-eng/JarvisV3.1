"""
Jarvis V3.1 — Event Bus
Pub/sub с wildcard, thread-safe, ring buffer.
"""
import threading
import time
import logging
from collections import deque
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Event:
    topic: str
    data: Any = None
    source: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"topic": self.topic, "data": self.data, "source": self.source, "timestamp": self.timestamp}


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self, history_size: int = 100):
        self._handlers: dict[str, list[Handler]] = {}
        self._history: deque[Event] = deque(maxlen=history_size)
        self._lock = threading.Lock()

    def subscribe(self, topic: str, handler: Handler) -> None:
        with self._lock:
            self._handlers.setdefault(topic, []).append(handler)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        with self._lock:
            if topic in self._handlers:
                self._handlers[topic] = [h for h in self._handlers[topic] if h is not handler]

    def publish(self, event: Event) -> None:
        with self._lock:
            self._history.append(event)
            snapshot = {t: list(handlers) for t, handlers in self._handlers.items()}

        for topic_pattern, handlers in snapshot.items():
            if fnmatch(event.topic, topic_pattern):
                for handler in handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.warning("Event handler error [%s]: %s", event.topic, e)

    def emit(self, topic: str, data: Any = None, source: str = "") -> None:
        self.publish(Event(topic=topic, data=data, source=source))

    def history(self, topic: str | None = None, limit: int = 20) -> list[dict]:
        with self._lock:
            events = list(self._history)
        if topic:
            events = [e for e in events if fnmatch(e.topic, topic)]
        return [e.to_dict() for e in events[-limit:]]

    def get_subscribers(self) -> dict[str, int]:
        with self._lock:
            return {k: len(v) for k, v in self._handlers.items()}


event_bus = EventBus()
