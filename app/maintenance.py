"""Cross-process maintenance state for operations that replace SQLite files."""

import os
import time
from contextlib import contextmanager
from threading import Lock
from typing import Optional
from urllib.parse import unquote, urlparse

from app.config import settings


class DatabaseMaintenanceBusy(RuntimeError):
    """Raised when another process is already restoring the database."""


_state_lock = Lock()
_database_maintenance = False
_FILE_LOCK_TIMEOUT_SECONDS = 30.0
_FILE_LOCK_POLL_SECONDS = 0.05


def _resolve_sqlite_path(database_url: Optional[str]) -> Optional[str]:
    raw = (database_url or "").strip()
    if not raw.startswith("sqlite"):
        return None

    if raw.startswith("sqlite:////"):
        path = raw[len("sqlite:///"):]
    elif raw.startswith("sqlite:///"):
        path = raw[len("sqlite:///"):]
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
    elif raw.startswith("sqlite://"):
        parsed = urlparse(raw)
        path = unquote(parsed.path or "")
        if parsed.netloc and not path:
            path = parsed.netloc
    else:
        path = raw

    path = os.path.expanduser(path)
    if not path or path == ":memory:":
        return None
    return path if os.path.isabs(path) else os.path.abspath(path)


def database_maintenance_lock_path(database_path: Optional[str] = None) -> Optional[str]:
    """Return a sidecar lock path for a SQLite database file."""
    resolved = database_path or _resolve_sqlite_path(settings.DATABASE_URL)
    if not resolved:
        return None
    return f"{os.path.abspath(resolved)}.maintenance.lock"


def _open_lock_file(lock_path: str):
    parent = os.path.dirname(lock_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    handle = open(lock_path, "a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    return handle


def _try_lock(handle) -> bool:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except (OSError, IOError):
            return False
        return True

    import fcntl

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, IOError):
        return False
    return True


def _unlock(handle):
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except (OSError, IOError):
        # Closing the descriptor still releases the OS lock on supported
        # platforms if an explicit unlock is unavailable during shutdown.
        pass


def _acquire_file_lock(lock_path: Optional[str], timeout: float):
    if not lock_path:
        return None

    handle = _open_lock_file(lock_path)
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        if _try_lock(handle):
            return handle
        if timeout <= 0 or time.monotonic() >= deadline:
            handle.close()
            raise DatabaseMaintenanceBusy("database maintenance is already in progress")
        time.sleep(_FILE_LOCK_POLL_SECONDS)


def _release_file_lock(handle):
    if handle is None:
        return
    try:
        _unlock(handle)
    finally:
        handle.close()


def is_database_maintenance(lock_path: Optional[str] = None) -> bool:
    """Return whether this or another process currently owns maintenance."""
    with _state_lock:
        if _database_maintenance:
            return True

    path = lock_path or database_maintenance_lock_path()
    if not path:
        return False

    try:
        handle = _acquire_file_lock(path, timeout=0)
    except DatabaseMaintenanceBusy:
        return True
    except OSError:
        # A filesystem permission problem is not proof that maintenance is in
        # progress. The actual restore path will fail explicitly if it cannot
        # acquire/create the lock file.
        return False

    _release_file_lock(handle)
    return False


@contextmanager
def database_maintenance(lock_path: Optional[str] = None):
    """Reject concurrent restores across threads and worker processes."""
    global _database_maintenance

    with _state_lock:
        if _database_maintenance:
            raise DatabaseMaintenanceBusy("database maintenance is already in progress")

    path = lock_path or database_maintenance_lock_path()
    file_handle = _acquire_file_lock(path, timeout=_FILE_LOCK_TIMEOUT_SECONDS)
    with _state_lock:
        if _database_maintenance:
            _release_file_lock(file_handle)
            raise DatabaseMaintenanceBusy("database maintenance is already in progress")
        _database_maintenance = True

    try:
        yield
    finally:
        with _state_lock:
            _database_maintenance = False
        _release_file_lock(file_handle)
