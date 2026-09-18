import threading
from urllib.parse import quote

import pytest
import requests

from app.services import bark_service


class FakeResponse:
    def __init__(self, payload=None, text="", status_code=200, http_error=None):
        self.payload = payload
        self.text = text
        self.status_code = status_code
        self.http_error = http_error
        self.raise_for_status_calls = 0

    def raise_for_status(self):
        self.raise_for_status_calls += 1
        if self.http_error is not None:
            raise self.http_error

    def json(self):
        if isinstance(self.payload, BaseException):
            raise self.payload
        return self.payload


class RecordingSession:
    instances = []
    pending_responses = []

    def __init__(self):
        self.mounts = {}
        self.calls = []
        self.responses = list(type(self).pending_responses)
        type(self).pending_responses.clear()
        self.closed = False
        type(self).instances.append(self)

    def mount(self, prefix, adapter):
        self.mounts[prefix] = adapter

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.responses:
            response = self.responses.pop(0)
        else:
            response = FakeResponse(payload={"code": 200, "message": "success"})
        if isinstance(response, BaseException):
            raise response
        return response

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def clean_bark_http_sessions(monkeypatch):
    bark_service.stop_bark_scheduler(timeout=0.1)
    bark_service.close_bark_http_sessions()
    RecordingSession.instances.clear()
    RecordingSession.pending_responses.clear()
    yield
    bark_service.stop_bark_scheduler(timeout=0.1)
    bark_service.close_bark_http_sessions()


def use_recording_sessions(monkeypatch):
    monkeypatch.setattr(bark_service.requests, "Session", RecordingSession)


def test_send_bark_push_reuses_thread_session_and_keeps_timeout_and_encoding(monkeypatch):
    use_recording_sessions(monkeypatch)
    key = "device/key?with spaces"
    title = "库存 / 今日"
    body = "剩余 10 & 20"

    first = bark_service.send_bark_push("https://bark.example/", key, title, body)
    second = bark_service.send_bark_push("https://bark.example/", key, title, body)

    assert first["code"] == 200
    assert second["code"] == 200
    assert len(RecordingSession.instances) == 1
    session = RecordingSession.instances[0]
    assert len(session.calls) == 2
    expected_url = (
        "https://bark.example/"
        f"{quote(key, safe='')}/{quote(title, safe='')}/{quote(body, safe='')}"
    )
    assert session.calls[0] == (
        expected_url,
        {"params": {"group": "库存监控", "isArchive": "1"}, "timeout": 15},
    )
    assert session.mounts["https://"].max_retries.total == 0
    assert session.mounts["http://"].max_retries.total == 0


def test_manual_push_does_not_depend_on_scheduler_start(monkeypatch):
    use_recording_sessions(monkeypatch)
    assert bark_service._scheduler_thread is None
    assert bark_service._scheduler_started is False

    result = bark_service.send_bark_push(
        "https://bark.example", "manual-device-key", "title", "body"
    )

    assert result == {"code": 200, "message": "success"}
    assert len(RecordingSession.instances) == 1


def test_scheduler_loop_closes_its_thread_session(monkeypatch):
    use_recording_sessions(monkeypatch)
    stop_event = threading.Event()

    def push_once():
        bark_service.send_bark_push(
            "https://bark.example", "scheduler-device-key", "title", "body"
        )
        stop_event.set()

    monkeypatch.setattr(bark_service, "maybe_run_scheduled_push", push_once)

    bark_service._scheduler_loop(stop_event)

    assert len(RecordingSession.instances) == 1
    assert RecordingSession.instances[0].closed is True


def test_shutdown_closes_manual_session_even_without_scheduler(monkeypatch):
    use_recording_sessions(monkeypatch)
    bark_service.send_bark_push(
        "https://bark.example", "manual-device-key", "title", "body"
    )
    session = RecordingSession.instances[0]
    assert session.closed is False

    assert bark_service.stop_bark_scheduler(timeout=0.1) is True

    assert session.closed is True
    assert bark_service._http_sessions == {}


def test_http_error_does_not_expose_device_key(monkeypatch):
    use_recording_sessions(monkeypatch)
    key = "device/key with secret"
    encoded_key = quote(key, safe="")
    response = FakeResponse(status_code=403)
    response.http_error = requests.HTTPError(
        f"403 Client Error: denied for url: https://bark.example/{encoded_key}/title/body",
        response=response,
    )
    RecordingSession.pending_responses = [response]

    with pytest.raises(requests.HTTPError) as exc_info:
        bark_service.send_bark_push("https://bark.example", key, "title", "body")

    assert key not in str(exc_info.value)
    assert encoded_key not in str(exc_info.value)
    assert "403" in str(exc_info.value)


def test_bark_error_payload_does_not_expose_device_key(monkeypatch):
    use_recording_sessions(monkeypatch)
    key = "device/key with secret"
    encoded_key = quote(key, safe="")
    RecordingSession.pending_responses = [
        FakeResponse(payload={"code": 400, "message": f"bad key {encoded_key}"})
    ]

    with pytest.raises(RuntimeError) as exc_info:
        bark_service.send_bark_push("https://bark.example", key, "title", "body")

    assert key not in str(exc_info.value)
    assert encoded_key not in str(exc_info.value)
    assert "bad key" in str(exc_info.value)
