from collections import deque
from math import ceil
from threading import Lock
import time
from typing import Deque, Dict, Optional

from starlette.requests import Request


class AccessAttemptLimiter:
    """Small process-local limiter for UI access-key failures.

    The application recommends one Uvicorn worker because it uses SQLite and
    in-process schedulers. Keeping this state in memory avoids adding another
    database write on every failed login; a multi-worker deployment should put
    the same policy at its reverse proxy or replace this with shared state.
    """

    def __init__(
        self,
        *,
        window_seconds: int = 60,
        max_failures: int = 5,
        lockout_seconds: int = 300,
    ):
        self.window_seconds = max(1, int(window_seconds))
        self.max_failures = max(1, int(max_failures))
        self.lockout_seconds = max(1, int(lockout_seconds))
        self._failures: Dict[str, Deque[float]] = {}
        self._blocked_until: Dict[str, float] = {}
        self._lock = Lock()

    def _prune(self, client_id: str, now: float) -> Deque[float]:
        attempts = self._failures.setdefault(client_id, deque())
        threshold = now - self.window_seconds
        while attempts and attempts[0] <= threshold:
            attempts.popleft()
        return attempts

    def retry_after(self, client_id: str, now: Optional[float] = None) -> int:
        current_time = time.time() if now is None else now
        with self._lock:
            blocked_until = self._blocked_until.get(client_id, 0)
            if blocked_until > current_time:
                return max(1, ceil(blocked_until - current_time))
            self._blocked_until.pop(client_id, None)
            attempts = self._prune(client_id, current_time)
            if not attempts:
                self._failures.pop(client_id, None)
            return 0

    def record_failure(self, client_id: str, now: Optional[float] = None) -> None:
        current_time = time.time() if now is None else now
        with self._lock:
            attempts = self._prune(client_id, current_time)
            attempts.append(current_time)
            if len(attempts) >= self.max_failures:
                self._blocked_until[client_id] = current_time + self.lockout_seconds

    def clear(self, client_id: str) -> None:
        with self._lock:
            self._failures.pop(client_id, None)
            self._blocked_until.pop(client_id, None)


ui_access_attempt_limiter = AccessAttemptLimiter()


def get_access_client_id(request: Request) -> str:
    client = request.client
    return str(client.host) if client and client.host else "unknown"
