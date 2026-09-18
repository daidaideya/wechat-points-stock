import threading
import time

from app.maintenance import (
    database_maintenance,
    leave_database_request,
    try_enter_database_request,
)


def test_database_maintenance_drains_in_flight_requests(tmp_path):
    lock_path = str(tmp_path / "database.maintenance.lock")
    entered = threading.Event()
    release = threading.Event()

    def hold_request_briefly():
        assert try_enter_database_request(lock_path)
        entered.set()
        release.wait(timeout=5)
        leave_database_request()

    worker = threading.Thread(target=hold_request_briefly)
    worker.start()
    assert entered.wait(timeout=2)

    def release_later():
        time.sleep(0.05)
        release.set()

    releaser = threading.Thread(target=release_later)
    releaser.start()
    with database_maintenance(lock_path):
        pass

    worker.join(timeout=2)
    releaser.join(timeout=2)
    assert not worker.is_alive()


def test_database_request_gate_rejects_new_requests_during_maintenance(tmp_path):
    lock_path = str(tmp_path / "database.maintenance.lock")

    with database_maintenance(lock_path):
        assert not try_enter_database_request(lock_path)
