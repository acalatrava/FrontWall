"""In-memory LRU cache for fully-built HTTP responses.

Stores the top N most-requested paths as pre-built Response objects so
the entire request path (lookup + response construction) becomes a single
dict lookup + object return — zero allocations on the hot path.
"""

import time
import logging
from collections import OrderedDict
from starlette.responses import Response

logger = logging.getLogger("frontwall.shield.hot_cache")

DEFAULT_MAX_ENTRIES = 2048
DEFAULT_MAX_MEMORY = 128 * 1024 * 1024  # 128 MB


class HotResponseCache:
    """Thread-safe (GIL-protected) LRU cache for pre-built responses.

    Since Python's GIL protects dict operations and we only care about
    approximate LRU semantics, we skip asyncio locks entirely.
    """

    __slots__ = ("_cache", "_max_entries", "_max_memory", "_memory_used",
                 "_hits", "_misses")

    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES, max_memory: int = DEFAULT_MAX_MEMORY):
        self._cache: OrderedDict[str, tuple[Response, int]] = OrderedDict()
        self._max_entries = max_entries
        self._max_memory = max_memory
        self._memory_used = 0
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Response | None:
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        self._hits += 1
        self._cache.move_to_end(key)
        return entry[0]

    def put(self, key: str, response: Response, body_size: int) -> None:
        if body_size > self._max_memory // 4:
            return

        if key in self._cache:
            _, old_size = self._cache.pop(key)
            self._memory_used -= old_size

        while (self._memory_used + body_size > self._max_memory or
               len(self._cache) >= self._max_entries):
            if not self._cache:
                break
            _, (_, evicted_size) = self._cache.popitem(last=False)
            self._memory_used -= evicted_size

        self._cache[key] = (response, body_size)
        self._memory_used += body_size

    def invalidate(self, key: str) -> None:
        entry = self._cache.pop(key, None)
        if entry:
            self._memory_used -= entry[1]

    def clear(self) -> None:
        self._cache.clear()
        self._memory_used = 0

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "entries": len(self._cache),
            "memory_mb": round(self._memory_used / 1048576, 2),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 1) if total else 0.0,
        }
