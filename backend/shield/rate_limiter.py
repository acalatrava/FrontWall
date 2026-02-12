import time
import asyncio
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("frontwall.shield.rate_limiter")

SHARD_COUNT = 16


@dataclass
class TokenBucket:
    capacity: int
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.monotonic)
    refill_rate: float = 1.0

    def __post_init__(self):
        self.tokens = float(self.capacity)

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class _Shard:
    """A single shard holding a subset of IP buckets behind its own lock."""

    __slots__ = ("buckets", "lock")

    def __init__(self):
        self.buckets: dict[str, TokenBucket] = {}
        self.lock = asyncio.Lock()

    def cleanup(self, stale_threshold: float) -> None:
        self.buckets = {
            ip: b for ip, b in self.buckets.items()
            if b.last_refill > stale_threshold
        }


class RateLimiter:
    """Per-IP token bucket rate limiter with sharded locks.

    Instead of a single global lock, IPs are hashed into N shards
    so concurrent requests to different IPs never contend.
    """

    def __init__(
        self,
        global_requests: int = 60,
        global_window: int = 60,
        cleanup_interval: int = 300,
    ):
        self.global_capacity = global_requests
        self.global_refill_rate = global_requests / global_window
        self.cleanup_interval = cleanup_interval
        self._last_cleanup = time.monotonic()

        self._shards = [_Shard() for _ in range(SHARD_COUNT)]
        self._endpoint_shards: dict[str, list[_Shard]] = {}

    def _shard_for(self, ip: str) -> _Shard:
        return self._shards[hash(ip) % SHARD_COUNT]

    async def check_global(self, client_ip: str) -> bool:
        shard = self._shard_for(client_ip)
        async with shard.lock:
            self._maybe_cleanup_shard(shard)
            bucket = shard.buckets.get(client_ip)
            if bucket is None:
                bucket = TokenBucket(
                    capacity=self.global_capacity,
                    refill_rate=self.global_refill_rate,
                )
                shard.buckets[client_ip] = bucket
            return bucket.consume()

    async def check_endpoint(
        self,
        client_ip: str,
        endpoint: str,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> bool:
        if endpoint not in self._endpoint_shards:
            self._endpoint_shards[endpoint] = [_Shard() for _ in range(SHARD_COUNT)]
        shards = self._endpoint_shards[endpoint]
        shard = shards[hash(client_ip) % SHARD_COUNT]
        async with shard.lock:
            bucket = shard.buckets.get(client_ip)
            if bucket is None:
                bucket = TokenBucket(
                    capacity=max_requests,
                    refill_rate=max_requests / window_seconds,
                )
                shard.buckets[client_ip] = bucket
            return bucket.consume()

    def _maybe_cleanup_shard(self, shard: _Shard) -> None:
        now = time.monotonic()
        if now - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = now
        stale = now - self.cleanup_interval
        for s in self._shards:
            s.cleanup(stale)
        for ep_shards in self._endpoint_shards.values():
            for s in ep_shards:
                s.cleanup(stale)
