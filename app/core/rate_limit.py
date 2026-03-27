from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, DefaultDict

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def hit(self, key: str, limit: int, per_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - per_seconds
        async with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f'Rate limit exceeded for {key}. Try again later.',
                )
            bucket.append(now)


rate_limiter = InMemoryRateLimiter()


async def limit_request(request: Request, scope: str, limit: int, per_seconds: int) -> None:
    ip = request.client.host if request.client else 'unknown'
    await rate_limiter.hit(f'{scope}:{ip}', limit, per_seconds)
