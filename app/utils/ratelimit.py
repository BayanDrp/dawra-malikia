from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request


class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.time()
        window_start = now - self.window_seconds

        self._requests[key] = [t for t in self._requests[key] if t > window_start]

        if len(self._requests[key]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="طلبات كثيرة جداً. الرجاء الانتظار قليلاً قبل المحاولة مرة أخرى.",
            )

        self._requests[key].append(now)


register_limiter = RateLimiter(max_requests=5, window_seconds=60)


def get_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def check_register_limit(ip: str = Depends(get_ip)) -> None:
    register_limiter.check(ip)
