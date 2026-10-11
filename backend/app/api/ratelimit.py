import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.security import decode_access_token


class RateLimiter:
    """Sliding-window limiter held in memory.

    Exact with a single worker process (how the production container runs).
    Several workers or servers would each count separately: use Redis then.
    """

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._calls = 0

    def reset(self) -> None:
        self._hits.clear()
        self._calls = 0

    def check(self, key: str) -> int | None:
        """Record a hit. Return None if allowed, else the seconds until it is."""
        now = time.monotonic()
        self._calls += 1
        if self._calls % 1000 == 0:
            self._sweep(now)

        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return max(1, int(self.window - (now - hits[0])) + 1)
        hits.append(now)
        return None

    def _sweep(self, now: float) -> None:
        for key in list(self._hits):
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if not hits:
                del self._hits[key]


LOGIN = RateLimiter(limit=10, window_seconds=60)
REGISTER = RateLimiter(limit=10, window_seconds=3600)
REFRESH = RateLimiter(limit=30, window_seconds=60)
ASK_MINUTE = RateLimiter(limit=20, window_seconds=60)
ASK_DAY = RateLimiter(limit=300, window_seconds=86400)
INGEST = RateLimiter(limit=10, window_seconds=60)

ALL_LIMITERS = (LOGIN, REGISTER, REFRESH, ASK_MINUTE, ASK_DAY, INGEST)

# (HTTP method, full path) -> [(limiter, "ip" or "user")]
RULES: dict[tuple[str, str], list[tuple[RateLimiter, str]]] = {
    ("POST", "/api/v1/auth/login"): [(LOGIN, "ip")],
    ("POST", "/api/v1/auth/register"): [(REGISTER, "ip")],
    ("POST", "/api/v1/auth/refresh"): [(REFRESH, "ip")],
    ("POST", "/api/v1/chat/ask"): [(ASK_MINUTE, "user"), (ASK_DAY, "user")],
    ("POST", "/api/v1/documents"): [(INGEST, "user")],
    ("POST", "/api/v1/documents/upload"): [(INGEST, "user")],
}


def _client_key(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


def _user_key(request: Request) -> str:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() == "bearer" and token:
        subject = decode_access_token(token)
        if subject:
            return f"user:{subject}"
    return _client_key(request)  # not signed in: the route will answer 401 anyway


async def enforce_rate_limits(request: Request) -> None:
    rules = RULES.get((request.method, request.url.path))
    if not rules:
        return
    for limiter, scope in rules:
        key = _client_key(request) if scope == "ip" else _user_key(request)
        wait = limiter.check(key)
        if wait is not None:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {wait} seconds.",
                headers={"Retry-After": str(wait)},
            )