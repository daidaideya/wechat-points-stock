import asyncio

import pytest

from app import main
from app.services import bark_service, qinglong_open_service


@pytest.fixture(params=(bark_service, qinglong_open_service))
def scheduler_module(request, tmp_path, monkeypatch):
    module = request.param
    stop_name = (
        "stop_bark_scheduler"
        if module is bark_service
        else "stop_qinglong_scheduler"
    )
    getattr(module, stop_name)(timeout=0.1)
    monkeypatch.setattr(
        module,
        "_PROCESS_LOCK_PATH",
        str(tmp_path / f"{module.__name__.rsplit('.', 1)[-1]}.lock"),
    )
    if module is bark_service:
        # The loop itself is under test; avoid database/network work.
        monkeypatch.setattr(module, "maybe_run_scheduled_push", lambda: None)
    yield module
    assert getattr(module, stop_name)(timeout=1.0)


def test_scheduler_start_is_idempotent_and_stop_wakes_thread(scheduler_module):
    module = scheduler_module
    start_name = (
        "start_bark_scheduler"
        if module is bark_service
        else "start_qinglong_scheduler"
    )
    stop_name = (
        "stop_bark_scheduler"
        if module is bark_service
        else "stop_qinglong_scheduler"
    )

    getattr(module, start_name)()
    first_thread = module._scheduler_thread
    assert first_thread is not None
    assert first_thread.is_alive()

    getattr(module, start_name)()
    assert module._scheduler_thread is first_thread

    assert getattr(module, stop_name)(timeout=1.0)
    assert not first_thread.is_alive()
    assert module._process_lock_fh is None
    assert getattr(module, stop_name)(timeout=0.1)


def test_fastapi_lifespan_keeps_startup_and_shutdown_order(monkeypatch):
    calls = []

    class FakeSession:
        def close(self):
            calls.append("db.close")

    monkeypatch.setattr(main.app_settings, "validate_runtime", lambda: calls.append("validate"))
    monkeypatch.setattr(main, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(main.web, "ensure_runtime_schema", lambda _db: calls.append("schema"))
    monkeypatch.setattr(main.web, "ensure_indexes", lambda _db: calls.append("indexes"))
    monkeypatch.setattr(main.bark_service, "start_bark_scheduler", lambda: calls.append("bark.start"))
    monkeypatch.setattr(
        main.qinglong_open_service,
        "start_qinglong_scheduler",
        lambda: calls.append("qinglong.start"),
    )
    monkeypatch.setattr(
        main.qinglong_open_service,
        "stop_qinglong_scheduler",
        lambda: calls.append("qinglong.stop"),
    )
    monkeypatch.setattr(main.bark_service, "stop_bark_scheduler", lambda: calls.append("bark.stop"))

    async def exercise_lifespan():
        async with main.lifespan(main.app):
            assert calls == ["validate", "schema", "indexes", "db.close", "bark.start", "qinglong.start"]

    asyncio.run(exercise_lifespan())
    assert calls[-2:] == ["qinglong.stop", "bark.stop"]
    assert not main.app.router.on_startup
