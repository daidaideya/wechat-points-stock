import asyncio

from starlette.requests import Request
from starlette.responses import Response

from app import main


def make_request(path: str, request_id: str | None = None) -> Request:
    headers = []
    if request_id is not None:
        headers.append((b"x-request-id", request_id.encode("ascii")))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": headers,
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
        }
    )


def test_request_id_is_preserved_and_returned_in_response_header():
    request = make_request("/health/live", "client-request-42")

    async def call_next(_request):
        return Response(status_code=200)

    response = asyncio.run(main.request_observability_middleware(request, call_next))

    assert request.state.request_id == "client-request-42"
    assert response.headers["X-Request-ID"] == "client-request-42"


def test_invalid_request_id_is_replaced_with_safe_generated_value():
    request = make_request("/api/v1/dashboard", "bad\nrequest-id")

    async def call_next(_request):
        return Response(status_code=200)

    response = asyncio.run(main.request_observability_middleware(request, call_next))

    generated = response.headers["X-Request-ID"]
    assert generated == request.state.request_id
    assert generated != "bad\nrequest-id"
    assert main._REQUEST_ID_RE.fullmatch(generated)
