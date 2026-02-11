import time
import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger("frontwall.shield.rate_limiter")


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


class RateLimiter:
    """Per-IP and per-endpoint token bucket rate limiter."""

    def __init__(
        self,
        global_requests: int = 60,
        global_window: int = 60,
        cleanup_interval: int = 300,
    ):
        self.global_capacity = global_requests
        self.global_refill_rate = global_requests / global_window
        self.cleanup_interval = cleanup_interval

        self._buckets: dict[str, TokenBucket] = {}
        self._endpoint_buckets: dict[str, dict[str, TokenBucket]] = defaultdict(dict)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.monotonic()

    async def check_global(self, client_ip: str) -> bool:
        async with self._lock:
            await self._maybe_cleanup()
            if client_ip not in self._buckets:
                self._buckets[client_ip] = TokenBucket(
                    capacity=self.global_capacity,
                    refill_rate=self.global_refill_rate,
                )
            return self._buckets[client_ip].consume()

    async def check_endpoint(
        self,
        client_ip: str,
        endpoint: str,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> bool:
        async with self._lock:
            ep_buckets = self._endpoint_buckets[endpoint]
            if client_ip not in ep_buckets:
                ep_buckets[client_ip] = TokenBucket(
                    capacity=max_requests,
                    refill_rate=max_requests / window_seconds,
                )
            return ep_buckets[client_ip].consume()

    async def _maybe_cleanup(self):
        now = time.monotonic()
        if now - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = now

        stale_threshold = now - self.cleanup_interval
        self._buckets = {
            ip: bucket for ip, bucket in self._buckets.items()
            if bucket.last_refill > stale_threshold
        }
        for endpoint in list(self._endpoint_buckets.keys()):
            self._endpoint_buckets[endpoint] = {
                ip: bucket for ip, bucket in self._endpoint_buckets[endpoint].items()
                if bucket.last_refill > stale_threshold
            }
            if not self._endpoint_buckets[endpoint]:
                del self._endpoint_buckets[endpoint]
