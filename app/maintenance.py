"""Process-local maintenance state for operations that replace the SQLite file."""

from contextlib import contextmanager
from threading import Lock

_state_lock = Lock()
_database_maintenance = False


def is_database_maintenance() -> bool:
    with _state_lock:
        return _database_maintenance


@contextmanager
def database_maintenance():
    """Reject new API work while a database restore is in progress."""
    global _database_maintenance
    with _state_lock:
        if _database_maintenance:
            raise RuntimeError("database maintenance is already in progress")
        _database_maintenance = True
    try:
        yield
    finally:
        with _state_lock:
            _database_maintenance = False
