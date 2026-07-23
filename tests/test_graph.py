from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest
import requests
from requests.adapters import HTTPAdapter

from conftest import GraphResponse, GraphTransportDouble
from msentraauth_template.graph.client import (
    GraphClaimsChallenge,
    GraphClient,
    GraphError,
    GraphForbidden,
    GraphRateLimited,
    GraphRedirectRejected,
    GraphResponseTooLarge,
    GraphUnauthorized,
    GraphUnavailable,
)
from msentraauth_template.settings import AppSettings


def client(
    transport: GraphTransportDouble,
    *,
    max_retry_after_seconds: int = 30,
) -> GraphClient:
    return GraphClient(
        base_url="https://graph.microsoft.com/v1.0/",
        connect_timeout=1.0,
        read_timeout=2.0,
        transport=transport,
        max_retry_after_seconds=max_retry_after_seconds,
    )


def test_get_profile_uses_bearer_select_versioned_user_agent_and_timeouts(
    transport: GraphTransportDouble | None = None,
) -> None:
    transport = transport or GraphTransportDouble()
    profile = client(transport).get_profile(" token ")
    assert profile.id == "graph-id"
    assert profile.display_name == "Template User"
    assert profile.user_principal_name == "template@example.test"
    assert profile.mail is None
    url, headers, params, timeout = transport.calls[0]
    assert url == "https://graph.microsoft.com/v1.0/me"
    assert headers["Accept"] == "application/json"
    assert headers["Authorization"] == "Bearer token"
    assert headers["User-Agent"].startswith("msentraauth-flask-template/")
    assert headers["User-Agent"] != "msentraauth-flask-template/1.0"
    assert params == {"$select": "id,displayName,userPrincipalName,mail"}
    assert timeout == (1.0, 2.0)


def test_from_settings_uses_injected_transport(settings: AppSettings) -> None:
    transport = GraphTransportDouble()
    graph = GraphClient.from_settings(settings, transport=transport)
    assert graph.get_profile("token").id == "graph-id"


def test_from_settings_creates_bounded_isolated_requests_session(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MountableTransport(GraphTransportDouble):
        def __init__(self) -> None:
            super().__init__()
            self.mounts: list[tuple[str, object]] = []
            self.trust_env = True
            self.auth: object = object()
            self.verify: object = False

        def mount(self, prefix: str, adapter: object) -> None:
            self.mounts.append((prefix, adapter))

    transport = MountableTransport()
    monkeypatch.setattr("msentraauth_template.graph.client.requests.Session", lambda: transport)
    graph = GraphClient.from_settings(settings)
    assert graph.get_profile("token").id == "graph-id"
    prefix, mounted = transport.mounts[0]
    assert prefix == "https://"
    assert isinstance(mounted, HTTPAdapter)
    assert mounted.max_retries.total == 2
    assert mounted.max_retries.backoff_max == 2.0
    assert mounted.max_retries.respect_retry_after_header is False
    assert transport.trust_env is False
    assert transport.auth is None
    assert transport.verify is True


@pytest.mark.parametrize("token", ["", "   ", None])
def test_requires_non_empty_token(token: object) -> None:
    with pytest.raises(ValueError, match="access_token"):
        client(GraphTransportDouble()).get_profile(token)  # type: ignore[arg-type]


def test_distinguishes_redirect_unauthorized_forbidden_rate_limit_and_server_errors() -> None:
    transport = GraphTransportDouble()
    cases: tuple[tuple[int, type[GraphError]], ...] = (
        (301, GraphRedirectRejected),
        (401, GraphUnauthorized),
        (403, GraphForbidden),
        (429, GraphRateLimited),
        (500, GraphUnavailable),
        (400, GraphError),
    )
    for status, error_type in cases:
        transport.response = GraphResponse(status, {})
        with pytest.raises(error_type):
            client(transport).get_profile("token")


def test_detects_and_sanitizes_claims_challenge() -> None:
    transport = GraphTransportDouble()
    claims = {"access_token": {"xms_cc": {"values": ["cp1"]}}}
    encoded = json.dumps(claims).replace('"', '\\"')
    transport.response = GraphResponse(
        401,
        {},
        headers={
            "WWW-Authenticate": (
                'Bearer authorization_uri="https://login.microsoftonline.com", '
                'error="insufficient_claims", '
                f'claims="{encoded}"'
            )
        },
    )
    with pytest.raises(GraphClaimsChallenge) as raised:
        client(transport).get_profile("token")
    assert json.loads(raised.value.claims) == claims
    assert "xms_cc" not in str(raised.value)


@pytest.mark.parametrize(
    "header",
    [
        'Bearer claims="not-json"',
        'Bearer claims="[]"',
        'Basic realm="example"',
    ],
)
def test_rejects_invalid_claims_challenges_or_falls_back_to_unauthorized(header: str) -> None:
    transport = GraphTransportDouble()
    transport.response = GraphResponse(401, {}, headers={"WWW-Authenticate": header})
    expected = GraphUnauthorized if header.startswith("Basic") else GraphError
    with pytest.raises(expected):
        client(transport).get_profile("token")


def test_rejects_oversized_claims_challenge() -> None:
    transport = GraphTransportDouble()
    oversized = "x" * 5000
    transport.response = GraphResponse(
        401,
        {},
        headers={"WWW-Authenticate": f'Bearer claims="{oversized}"'},
    )
    with pytest.raises(GraphError, match="claims challenge"):
        client(transport).get_profile("token")


def test_retry_after_is_bounded_and_supports_http_dates() -> None:
    transport = GraphTransportDouble()
    transport.response = GraphResponse(429, {}, headers={"Retry-After": "9999"})
    with pytest.raises(GraphRateLimited) as integer:
        client(transport, max_retry_after_seconds=17).get_profile("token")
    assert integer.value.retry_after == 17

    future = format_datetime(datetime.now(UTC) + timedelta(seconds=90), usegmt=True)
    transport.response = GraphResponse(503, {}, headers={"Retry-After": future})
    with pytest.raises(GraphUnavailable) as dated:
        client(transport, max_retry_after_seconds=11).get_profile("token")
    assert dated.value.retry_after == 11

    transport.response = GraphResponse(429, {}, headers={"Retry-After": "invalid"})
    with pytest.raises(GraphRateLimited) as invalid:
        client(transport).get_profile("token")
    assert invalid.value.retry_after is None

    transport.response = GraphResponse(429, {}, headers={"Retry-After": "0"})
    with pytest.raises(GraphRateLimited) as immediate:
        client(transport).get_profile("token")
    assert immediate.value.retry_after == 1


def test_translates_only_expected_transport_errors() -> None:
    transport = GraphTransportDouble()
    transport.error = requests.Timeout("network-secret")
    with pytest.raises(GraphUnavailable) as raised:
        client(transport).get_profile("token")
    assert "network-secret" not in str(raised.value)

    transport.error = RuntimeError("programming-error")
    with pytest.raises(RuntimeError, match="programming-error"):
        client(transport).get_profile("token")


def test_rejects_invalid_status_json_and_payloads() -> None:
    transport = GraphTransportDouble()
    transport.response.status_code = True  # type: ignore[assignment]
    with pytest.raises(GraphError, match="invalid status"):
        client(transport).get_profile("token")

    transport.response = GraphResponse(200, ValueError("raw-json"))
    with pytest.raises(GraphError, match="invalid JSON") as raised:
        client(transport).get_profile("token")
    assert "raw-json" not in str(raised.value)

    payloads: tuple[object, ...] = (
        [],
        {},
        {"id": "id"},
        {"id": 1, "displayName": "Name"},
    )
    for payload in payloads:
        transport.response = GraphResponse(200, payload)
        with pytest.raises(GraphError):
            client(transport).get_profile("token")


def test_profile_fields_have_type_length_and_control_limits() -> None:
    transport = GraphTransportDouble()
    transport.response = GraphResponse(
        200,
        {"id": "id", "displayName": " Name ", "mail": " ", "userPrincipalName": None},
    )
    profile = client(transport).get_profile("token")
    assert profile.display_name == "Name"
    assert profile.mail is None
    assert profile.user_principal_name is None

    invalid_payloads = (
        {"id": "id", "displayName": "Name", "mail": 123},
        {"id": "i" * 129, "displayName": "Name"},
        {"id": "id", "displayName": "n" * 257},
        {"id": "id", "displayName": "Name\nInjected"},
        {"id": "id", "displayName": "Name", "mail": "m" * 321},
    )
    for payload in invalid_payloads:
        transport.response = GraphResponse(200, payload)
        with pytest.raises(GraphError, match="invalid profile"):
            client(transport).get_profile("token")


class StreamingResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        chunks: Iterable[bytes] = (b"{}",),
    ) -> None:
        self.status_code = status_code
        self.headers = dict(headers or {"Content-Type": "application/json"})
        self._chunks = tuple(chunks)
        self.closed = False

    def iter_content(self, *, chunk_size: int) -> Iterable[bytes]:
        assert chunk_size == 8192
        return iter(self._chunks)

    def close(self) -> None:
        self.closed = True


class RequestsSessionDouble:
    def __init__(self, response: StreamingResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []
        self.mounts: list[tuple[str, object]] = []
        self.trust_env = True
        self.auth: object = object()
        self.verify: object = False

    def mount(self, prefix: str, adapter: object) -> None:
        self.mounts.append((prefix, adapter))

    def get(self, url: str, **kwargs: object) -> StreamingResponse:
        self.calls.append({"url": url, **kwargs})
        return self.response


def _graph_with_streaming_response(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
    response: StreamingResponse,
    *,
    maximum: int = 128,
) -> tuple[GraphClient, RequestsSessionDouble]:
    session = RequestsSessionDouble(response)
    monkeypatch.setattr("msentraauth_template.graph.client.requests.Session", lambda: session)
    graph = GraphClient.from_settings(replace(settings, graph_max_response_bytes=maximum))
    return graph, session


def test_requests_transport_disables_redirects_streams_limits_and_closes(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.dumps(
        {"id": "id", "displayName": "Name", "userPrincipalName": None, "mail": None}
    ).encode()
    response = StreamingResponse(
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        chunks=(body[:10], body[10:]),
    )
    graph, session = _graph_with_streaming_response(settings, monkeypatch, response)
    assert graph.get_profile("token").id == "id"
    assert response.closed is True
    call = session.calls[0]
    assert call["allow_redirects"] is False
    assert call["stream"] is True
    assert session.trust_env is False
    assert session.auth is None
    assert session.verify is True


@pytest.mark.parametrize(
    ("response", "error_type"),
    [
        (
            StreamingResponse(
                headers={"Content-Type": "text/html"},
                chunks=(b"{}",),
            ),
            GraphError,
        ),
        (
            StreamingResponse(
                headers={"Content-Type": "application/json", "Content-Length": "invalid"},
                chunks=(b"{}",),
            ),
            GraphError,
        ),
        (
            StreamingResponse(
                headers={"Content-Type": "application/json", "Content-Length": "999"},
                chunks=(b"{}",),
            ),
            GraphResponseTooLarge,
        ),
        (
            StreamingResponse(
                headers={"Content-Type": "application/json"},
                chunks=(b"a" * 80, b"b" * 80),
            ),
            GraphResponseTooLarge,
        ),
    ],
)
def test_requests_transport_rejects_untrusted_or_oversized_bodies(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
    response: StreamingResponse,
    error_type: type[GraphError],
) -> None:
    graph, _ = _graph_with_streaming_response(
        settings,
        monkeypatch,
        response,
        maximum=128,
    )
    with pytest.raises(error_type):
        graph.get_profile("token")
    assert response.closed is True


def test_internal_transport_and_parser_edges(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import msentraauth_template.graph.client as graph_module

    assert graph_module._BufferedResponse(204, {}, None).json() is None

    class RealSessionFailure(requests.Session):
        def get(self, *args: object, **kwargs: object) -> requests.Response:
            del args, kwargs
            raise TypeError("real-session-programming-error")

    raw_transport = graph_module._RequestsTransport(
        RealSessionFailure(),
        max_response_bytes=128,
    )
    with pytest.raises(TypeError, match="programming-error"):
        raw_transport.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={},
            params={},
            timeout=(1.0, 2.0),
        )

    redirect = StreamingResponse(status_code=302, headers={"Location": "https://evil.example"})
    graph, _ = _graph_with_streaming_response(settings, monkeypatch, redirect)
    with pytest.raises(GraphRedirectRejected):
        graph.get_profile("token")
    assert redirect.closed is True

    runtime_json = GraphTransportDouble()
    runtime_json.response = GraphResponse(200, RuntimeError("must-not-leak"))
    with pytest.raises(GraphError, match="invalid JSON") as raised:
        client(runtime_json).get_profile("token")
    assert "must-not-leak" not in str(raised.value)

    no_claims = GraphTransportDouble()
    no_claims.response = GraphResponse(
        401,
        {},
        headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
    )
    with pytest.raises(GraphUnauthorized):
        client(no_claims).get_profile("token")

    naive_date = GraphTransportDouble()
    naive_date.response = GraphResponse(
        429,
        {},
        headers={"Retry-After": "Wed, 21 Oct 2099 07:28:00"},
    )
    with pytest.raises(GraphRateLimited) as rate_limited:
        client(naive_date, max_retry_after_seconds=9).get_profile("token")
    assert rate_limited.value.retry_after == 9


@pytest.mark.parametrize(
    "response",
    [
        StreamingResponse(
            headers={"Content-Type": "application/json", "Content-Length": "-1"},
            chunks=(b"{}",),
        ),
        StreamingResponse(
            headers={"Content-Type": "application/json"},
            chunks=("not-bytes",),  # type: ignore[arg-type]
        ),
        StreamingResponse(
            headers={"Content-Type": "application/json"},
            chunks=(b'{"id":"id","displayName":NaN}',),
        ),
    ],
)
def test_streaming_parser_rejects_negative_length_invalid_chunks_and_json_constants(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
    response: StreamingResponse,
) -> None:
    graph, _ = _graph_with_streaming_response(settings, monkeypatch, response)
    with pytest.raises(GraphError):
        graph.get_profile("token")
    assert response.closed is True
