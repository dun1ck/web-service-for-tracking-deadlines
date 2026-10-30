"""Хранилище «ключ — значение» с TTL для счётчиков неудачных входов и CAPTCHA.

В Docker используется Redis (п. 4.2.2 ТЗ). Если Redis недоступен (локальный запуск без Docker,
автотесты), автоматически используется хранилище в памяти процесса.
"""

import logging
import threading
import time
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


class KVStore(Protocol):
    def incr(self, key: str, ttl_seconds: int) -> int: ...
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl_seconds: int) -> None: ...
    def delete(self, *keys: str) -> None: ...
    def ttl(self, key: str) -> int: ...


class MemoryKVStore:
    """Потокобезопасное хранилище в памяти с истечением ключей."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def _alive(self, key: str) -> tuple[str, float] | None:
        item = self._data.get(key)
        if item is None:
            return None
        if item[1] <= time.monotonic():
            self._data.pop(key, None)
            return None
        return item

    def incr(self, key: str, ttl_seconds: int) -> int:
        with self._lock:
            item = self._alive(key)
            if item is None:
                self._data[key] = ("1", time.monotonic() + ttl_seconds)
                return 1
            value = int(item[0]) + 1
            self._data[key] = (str(value), item[1])
            return value

    def get(self, key: str) -> str | None:
        with self._lock:
            item = self._alive(key)
            return item[0] if item else None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        with self._lock:
            self._data[key] = (value, time.monotonic() + ttl_seconds)

    def delete(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                self._data.pop(key, None)

    def ttl(self, key: str) -> int:
        with self._lock:
            item = self._alive(key)
            return max(int(item[1] - time.monotonic()), 0) if item else 0


class RedisKVStore:
    """Обёртка над Redis с теми же методами."""

    def __init__(self, url: str) -> None:
        import redis

        self._redis = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)
        self._redis.ping()

    def incr(self, key: str, ttl_seconds: int) -> int:
        pipe = self._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl_seconds, nx=True)
        value, _ = pipe.execute()
        return int(value)

    def get(self, key: str) -> str | None:
        return self._redis.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._redis.set(key, value, ex=ttl_seconds)

    def delete(self, *keys: str) -> None:
        if keys:
            self._redis.delete(*keys)

    def ttl(self, key: str) -> int:
        return max(int(self._redis.ttl(key)), 0)


_store: KVStore | None = None
_store_lock = threading.Lock()


def _build_store() -> KVStore:
    backend = settings.KV_BACKEND.lower()
    if backend == "memory":
        return MemoryKVStore()
    try:
        return RedisKVStore(settings.REDIS_URL)
    except Exception as exc:  # noqa: BLE001
        if backend == "redis":
            raise
        logger.warning("Redis недоступен (%s) — счётчики входа хранятся в памяти процесса", exc)
        return MemoryKVStore()


def get_kv_store() -> KVStore:
    """Зависимость FastAPI: общее хранилище счётчиков."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = _build_store()
    return _store
