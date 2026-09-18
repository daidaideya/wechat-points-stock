import threading
import time

import pytest
import requests

from app.services import qinglong_open_service as service


class FakeResponse:
    def __init__(self, body, status_code=200):
        self._body = body
        self.status_code = status_code

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class RecordingSession:
    def __init__(self, instances):
        self.calls = []
        self.mounts = {}
        self.closed = False
        instances.append(self)

    def mount(self, prefix, adapter):
        self.mounts[prefix] = adapter

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("/open/auth/token"):
            return FakeResponse(
                {
                    "code": 200,
                    "data": {"token": "token-value", "expiration": time.time() + 3600},
                }
            )
        return FakeResponse({"code": 200, "data": {"data": [{"id": 7}]}})

    def put(self, url, **kwargs):
        self.calls.append(("PUT", url, kwargs))
        return FakeResponse({"code": 200})

    def close(self):
        self.closed = True


@pytest.fixture
def recording_sessions(monkeypatch):
    service.stop_qinglong_scheduler(timeout=0.1)
    service.close_qinglong_http_sessions()
    service._TOKEN_CACHE.clear()
    instances = []
    monkeypatch.setattr(
        service.requests,
        "Session",
        lambda: RecordingSession(instances),
    )
    yield instances
    service.close_qinglong_http_sessions()
    service._TOKEN_CACHE.clear()


def test_openapi_calls_reuse_one_session_and_keep_request_contract(recording_sessions):
    base_url = "https://qinglong.example/"
    client_secret = "client-secret-value"
    token = service.get_token(base_url, "client-id", client_secret)
    assert token == "token-value"
    assert service.list_crons(base_url, token) == [{"id": 7}]
    service.update_cron_schedule(
        base_url,
        token,
        cron_id=7,
        schedule="0 8 * * *",
        name="points",
        command="python points.py",
    )

    assert len(recording_sessions) == 1
    session = recording_sessions[0]
    assert [call[0] for call in session.calls] == ["GET", "GET", "PUT"]

    auth_method, auth_url, auth_kwargs = session.calls[0]
    assert auth_method == "GET"
    assert auth_url == "https://qinglong.example/open/auth/token"
    assert auth_kwargs["params"] == {
        "client_id": "client-id",
        "client_secret": client_secret,
    }
    assert auth_kwargs["timeout"] == 15

    list_method, list_url, list_kwargs = session.calls[1]
    assert list_method == "GET"
    assert list_url == "https://qinglong.example/open/crons"
    assert list_kwargs["headers"] == {"Authorization": "Bearer token-value"}
    assert list_kwargs["params"] == {"page": 0, "size": 0}
    assert list_kwargs["timeout"] == 30

    update_method, update_url, update_kwargs = session.calls[2]
    assert update_method == "PUT"
    assert update_url == "https://qinglong.example/open/crons"
    assert update_kwargs["headers"] == {"Authorization": "Bearer token-value"}
    assert update_kwargs["json"] == {
        "id": 7,
        "name": "points",
        "command": "python points.py",
        "schedule": "0 8 * * *",
    }
    assert update_kwargs["timeout"] == 20

    for adapter in session.mounts.values():
        assert adapter.max_retries.total == 0
        assert adapter.poolmanager.connection_pool_kw["maxsize"] == 2


def test_put_request_is_not_retried_and_error_does_not_expose_token(monkeypatch):
    token = "bearer-token-value"

    class FailingSession(RecordingSession):
        def put(self, url, **kwargs):
            self.calls.append(("PUT", url, kwargs))
            raise requests.ConnectionError(f"upstream failed with {token}")

    service.stop_qinglong_scheduler(timeout=0.1)
    service.close_qinglong_http_sessions()
    instances = []
    monkeypatch.setattr(service.requests, "Session", lambda: FailingSession(instances))
    try:
        with pytest.raises(requests.ConnectionError) as exc_info:
            service.update_cron_schedule(
                "https://qinglong.example",
                token,
                cron_id=7,
                schedule="0 8 * * *",
                name="points",
                command="python points.py",
            )
        assert token not in str(exc_info.value)
        assert len(instances) == 1
        assert len(instances[0].calls) == 1
        assert instances[0].mounts["https://"].max_retries.total == 0
    finally:
        service.close_qinglong_http_sessions()


def test_auth_error_does_not_expose_client_secret(monkeypatch):
    client_secret = "client-secret-value"

    class FailingSession(RecordingSession):
        def get(self, url, **kwargs):
            self.calls.append(("GET", url, kwargs))
            raise requests.ConnectionError(f"cannot connect with secret={client_secret}")

    service.stop_qinglong_scheduler(timeout=0.1)
    service.close_qinglong_http_sessions()
    instances = []
    monkeypatch.setattr(service.requests, "Session", lambda: FailingSession(instances))
    try:
        with pytest.raises(requests.ConnectionError) as exc_info:
            service.get_token(
                "https://qinglong.example",
                "client-id",
                client_secret,
                force_refresh=True,
            )
        assert client_secret not in str(exc_info.value)
    finally:
        service.close_qinglong_http_sessions()


def test_scheduler_stop_closes_pool_and_manual_sync_creates_a_fresh_one(recording_sessions):
    service.get_token("https://qinglong.example", "client-id", "secret")
    first_session = recording_sessions[0]

    assert service.stop_qinglong_scheduler(timeout=0.1) is True
    assert first_session.closed is True
    assert not service._http_sessions

    service.get_token(
        "https://qinglong.example",
        "client-id",
        "secret",
        force_refresh=True,
    )
    assert len(recording_sessions) == 2
    assert recording_sessions[1].closed is False


def test_scheduler_loop_closes_its_thread_local_pool(recording_sessions):
    service.get_token("https://qinglong.example", "client-id", "secret")
    session = recording_sessions[0]
    stop_event = threading.Event()
    stop_event.set()

    service._scheduler_loop(stop_event)

    assert session.closed is True
    assert not service._http_sessions
