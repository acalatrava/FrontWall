"""Pre-computed file index built at deploy time.

Eliminates all filesystem stat/exists calls during request serving.
Files under a configurable size threshold are loaded entirely into memory.
"""

import mimetypes
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from urllib.parse import quote

logger = logging.getLogger("frontwall.shield.cache_index")

IMMUTABLE_EXTENSIONS = frozenset({
    ".css", ".js", ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico",
    ".mp4", ".webm", ".mp3", ".ogg", ".pdf", ".map",
})

IN_MEMORY_THRESHOLD = 512 * 1024  # 512 KB — files smaller than this are served from RAM
MAX_MEMORY_TOTAL = 256 * 1024 * 1024  # 256 MB total in-memory budget


@dataclass(slots=True, frozen=True)
class CachedEntry:
    disk_path: str
    content_type: str
    content_length: int
    is_immutable: bool
    body: bytes | None  # None = serve from disk (too large)


class CacheIndex:
    """Fully pre-computed mapping from URL paths to cached responses.

    Built once at deploy time. All lookups are O(1) dict access — zero syscalls.
    """

    __slots__ = ("_entries", "_query_entries", "stats")

    def __init__(self):
        self._entries: dict[str, CachedEntry] = {}
        self._query_entries: dict[str, CachedEntry] = {}
        self.stats = {"files": 0, "in_memory": 0, "memory_bytes": 0, "disk_only": 0}

    def lookup(self, path: str, query: str = "") -> CachedEntry | None:
        if query:
            key = f"{path}?{query}"
            entry = self._query_entries.get(key)
            if entry:
                return entry
        return self._entries.get(path)

    def build(self, cache_root: Path) -> None:
        """Scan the cache directory and build the full index."""
        t0 = time.monotonic()
        memory_used = 0

        if not cache_root.exists():
            return

        root_str = str(cache_root.resolve())

        for file_path in cache_root.rglob("*"):
            if not file_path.is_file():
                continue

            resolved = str(file_path.resolve())
            if not resolved.startswith(root_str):
                continue

            rel = file_path.relative_to(cache_root)
            url_path = str(rel).replace("\\", "/")

            ct, _ = mimetypes.guess_type(str(file_path))
            if not ct:
                ct = "application/octet-stream"

            ext = file_path.suffix.lower()
            is_immutable = ext in IMMUTABLE_EXTENSIONS
            size = file_path.stat().st_size

            body = None
            if size <= IN_MEMORY_THRESHOLD and memory_used + size <= MAX_MEMORY_TOTAL:
                try:
                    body = file_path.read_bytes()
                    memory_used += size
                except OSError:
                    body = None

            entry = CachedEntry(
                disk_path=resolved,
                content_type=ct,
                content_length=size,
                is_immutable=is_immutable,
                body=body,
            )

            self._register_entry(url_path, entry, cache_root, rel)

        elapsed = (time.monotonic() - t0) * 1000
        self.stats["files"] = len(self._entries) + len(self._query_entries)
        self.stats["in_memory"] = sum(1 for e in self._entries.values() if e.body is not None) + \
                                  sum(1 for e in self._query_entries.values() if e.body is not None)
        self.stats["memory_bytes"] = memory_used
        self.stats["disk_only"] = self.stats["files"] - self.stats["in_memory"]

        logger.info(
            "Cache index built in %.1fms: %d files (%d in-memory = %.1f MB, %d disk-only)",
            elapsed, self.stats["files"], self.stats["in_memory"],
            memory_used / 1048576, self.stats["disk_only"],
        )

    def add_learned_file(self, cache_root: Path, rel_path: str) -> CachedEntry | None:
        """Hot-add a file that was learned at runtime."""
        file_path = cache_root / rel_path
        if not file_path.exists() or not file_path.is_file():
            return None

        ct, _ = mimetypes.guess_type(str(file_path))
        if not ct:
            ct = "application/octet-stream"

        ext = file_path.suffix.lower()
        size = file_path.stat().st_size
        body = None
        if size <= IN_MEMORY_THRESHOLD:
            try:
                body = file_path.read_bytes()
            except OSError:
                pass

        entry = CachedEntry(
            disk_path=str(file_path.resolve()),
            content_type=ct,
            content_length=size,
            is_immutable=ext in IMMUTABLE_EXTENSIONS,
            body=body,
        )

        url_path = rel_path.replace("\\", "/")
        self._entries[url_path] = entry

        if url_path.endswith("/index.html"):
            dir_path = url_path[:-len("index.html")]
            self._entries[dir_path] = entry
            self._entries[dir_path.rstrip("/")] = entry

        return entry

    def _register_entry(self, url_path: str, entry: CachedEntry, cache_root: Path, rel: Path) -> None:
        """Register an entry under all URL variants it should be reachable at."""
        parts = rel.parts
        filename = parts[-1] if parts else ""

        if "_" in filename and not url_path.startswith("_"):
            idx = filename.rfind("_")
            dot_idx = filename.rfind(".")
            if dot_idx > idx:
                query_encoded = filename[idx + 1:dot_idx]
                clean_name = filename[:idx] + filename[dot_idx:]
                clean_path = "/".join(parts[:-1] + (clean_name,)) if len(parts) > 1 else clean_name
                self._query_entries[f"{clean_path}?{query_encoded}"] = entry

        self._entries[url_path] = entry

        if url_path == "index.html":
            self._entries[""] = entry
            self._entries["/"] = entry

        if url_path.endswith("/index.html"):
            dir_path = url_path[:-len("index.html")]
            self._entries[dir_path] = entry
            bare = dir_path.rstrip("/")
            if bare:
                self._entries[bare] = entry
