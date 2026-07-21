from __future__ import annotations

import pytest
import requests

from conftest import GraphResponse, GraphTransportDouble
from msentraauth_template.graph.client import (
    GraphClient,
    GraphError,
    GraphUnauthorized,
    GraphUnavailable,
)


def client(transport: GraphTransportDouble) -> GraphClient:
    return GraphClient(
        base_url="https://graph.microsoft.com/v1.0/",
        connect_timeout=1.0,
        read_timeout=2.0,
        transport=transport,
    )


def test_get_profile_uses_bearer_select_and_timeouts(
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
    assert headers == {
        "Accept": "application/json",
        "Authorization": "Bearer token",
        "User-Agent": "msentraauth-flask-template/1.0",
    }
    assert params == {"$select": "id,displayName,userPrincipalName,mail"}
    assert timeout == (1.0, 2.0)


def test_from_settings_uses_injected_transport(settings: object) -> None:
    transport = GraphTransportDouble()
    graph = GraphClient.from_settings(settings, transport=transport)  # type: ignore[arg-type]
    assert graph.get_profile("token").id == "graph-id"


def test_from_settings_creates_requests_session(
    settings: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    class MountableTransport(GraphTransportDouble):
        def __init__(self) -> None:
            super().__init__()
            self.mounts: list[tuple[str, object]] = []

        def mount(self, prefix: str, adapter: object) -> None:
            self.mounts.append((prefix, adapter))

    transport = MountableTransport()
    monkeypatch.setattr(
        "msentraauth_template.graph.client.requests.Session", lambda: transport
    )
    graph = GraphClient.from_settings(settings)  # type: ignore[arg-type]
    assert graph.get_profile("token").id == "graph-id"
    assert transport.mounts[0][0] == "https://"


@pytest.mark.parametrize("token", ["", "   ", None])
def test_requires_non_empty_token(token: object) -> None:
    with pytest.raises(ValueError, match="access_token"):
        client(GraphTransportDouble()).get_profile(token)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, GraphUnauthorized),
        (403, GraphUnauthorized),
        (429, GraphUnavailable),
        (500, GraphUnavailable),
        (400, GraphError),
    ],
)
def test_translates_http_status(status: int, error_type: type[GraphError]) -> None:
    transport = GraphTransportDouble()
    transport.response = GraphResponse(status, {})
    with pytest.raises(error_type):
        client(transport).get_profile("token")


def test_translates_transport_errors() -> None:
    transport = GraphTransportDouble()
    transport.error = requests.Timeout("network-secret")
    with pytest.raises(GraphUnavailable) as raised:
        client(transport).get_profile("token")
    assert "network-secret" not in str(raised.value)
    transport.error = RuntimeError("raw-secret")
    with pytest.raises(GraphUnavailable) as raised:
        client(transport).get_profile("token")
    assert "raw-secret" not in str(raised.value)


def test_rejects_invalid_json_and_payloads() -> None:
    transport = GraphTransportDouble()
    transport.response = GraphResponse(200, ValueError("raw-json"))
    with pytest.raises(GraphError, match="invalid JSON"):
        client(transport).get_profile("token")
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


def test_optional_profile_fields_validate_types_and_blank_values() -> None:
    transport = GraphTransportDouble()
    transport.response = GraphResponse(
        200,
        {"id": "id", "displayName": " Name ", "mail": " ", "userPrincipalName": None},
    )
    profile = client(transport).get_profile("token")
    assert profile.display_name == "Name"
    assert profile.mail is None
    assert profile.user_principal_name is None
    transport.response = GraphResponse(
        200,
        {"id": "id", "displayName": "Name", "mail": 123},
    )
    with pytest.raises(GraphError, match="invalid profile"):
        client(transport).get_profile("token")
