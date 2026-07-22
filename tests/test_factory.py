from __future__ import annotations

from dataclasses import replace
from urllib.parse import parse_qs, urlsplit

from flask import Flask, session
from flask_ms_entra_auth import AtomicAuthStorage, SecurityReport

from conftest import FakeMsalClient, GraphTransportDouble, RedisDouble
from msentraauth_template import create_app
from msentraauth_template.auth.hooks import LocalUserRegistry
from msentraauth_template.graph.client import GraphClient
from msentraauth_template.settings import AppSettings


def test_factory_registers_extensions_routes_and_security(
    settings: object,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    app = create_app(
        settings,  # type: ignore[arg-type]
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=GraphTransportDouble(),
    )
    assert isinstance(app, Flask)
    assert isinstance(app.extensions["template_entra_auth"].audit_security(app), SecurityReport)
    assert isinstance(app.extensions["template_graph"], GraphClient)
    assert isinstance(app.extensions["template_users"], LocalUserRegistry)
    state = app.extensions["ms_entra_auth"]
    assert isinstance(state.storage.backend, AtomicAuthStorage)
    routes = {rule.rule for rule in app.url_map.iter_rules()}
    assert {
        "/",
        "/profile",
        "/health/live",
        "/health/ready",
        "/auth/login",
        "/auth/callback",
        "/auth/logout",
    } <= routes


def test_factory_registers_existing_app_registration_callback_alias(
    settings: AppSettings,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    legacy_settings = replace(
        settings,
        redirect_uri="http://localhost:5000/getAToken",
    )

    app = create_app(
        legacy_settings,
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=GraphTransportDouble(),
    )

    rules = {rule.rule: rule.endpoint for rule in app.url_map.iter_rules()}
    assert rules["/getAToken"] == "msentraauth_template.callback_alias"
    assert (
        app.view_functions["msentraauth_template.callback_alias"]
        is app.view_functions["ms_entra_auth.callback"]
    )


def test_full_login_graph_and_logout_flow(
    settings: object,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    msal_client, factory = msal_runtime
    graph_transport = GraphTransportDouble()
    app = create_app(
        settings,  # type: ignore[arg-type]
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=graph_transport,
    )
    client = app.test_client()

    anonymous = client.get("/")
    assert anonymous.status_code == 200
    assert "Entrar com Microsoft" in anonymous.text
    assert "Set-Cookie" not in anonymous.headers
    assert list(redis_double.scan_iter(match="msentra-template:session:*")) == []
    protected = client.get("/profile")
    assert protected.status_code == 302

    login = client.get("/auth/login", query_string={"next": "/profile"})
    state = parse_qs(urlsplit(login.headers["Location"]).query)["state"][0]
    callback = client.get("/auth/callback", query_string={"code": "code", "state": state})
    assert callback.status_code == 302
    assert callback.headers["Location"] == "/profile"

    profile = client.get("/profile", headers={"X-Request-ID": "request-12345678"})
    assert profile.status_code == 200
    assert "Template User" in profile.text
    assert "graph-id" in profile.text
    assert profile.headers["X-Request-ID"] == "request-12345678"
    assert graph_transport.calls[0][1]["Authorization"] == "Bearer server-only-token"
    assert app.extensions["template_users"].count() == 1
    assert msal_client.cache is not None

    home = client.get("/")
    assert "Consultar Microsoft Graph" in home.text
    logout = client.post("/auth/logout")
    assert logout.status_code == 302
    assert logout.headers["Location"] == "/logged-out"
    assert "sessão nesta aplicação" in client.get("/logged-out").text


def test_health_and_graph_error_handler(
    settings: object,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    transport = GraphTransportDouble()
    app = create_app(
        settings,  # type: ignore[arg-type]
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=transport,
    )
    client = app.test_client()
    assert client.get("/health/live").json == {"status": "ok"}
    assert client.get("/health/ready").json == {"status": "ready"}
    assert list(redis_double.scan_iter(match="msentra-template:readiness:*")) == []

    redis_double.ping_result = False
    unavailable = client.get("/health/ready")
    assert unavailable.status_code == 503
    assert unavailable.json == {"status": "unavailable"}

    redis_double.ping_result = True
    redis_double.fail = "ping"
    unavailable = client.get("/health/ready")
    assert unavailable.status_code == 503
    assert unavailable.json == {"status": "unavailable"}

    for operation in ("set", "eval"):
        redis_double.fail = operation
        unavailable = client.get("/health/ready")
        assert unavailable.status_code == 503
        assert unavailable.json == {"status": "unavailable"}

    redis_double.return_invalid = True
    redis_double.fail = "delete"
    unavailable = client.get("/health/ready")
    assert unavailable.status_code == 503
    assert unavailable.json == {"status": "unavailable"}

    redis_double.fail = None
    redis_double.return_invalid = True
    unavailable = client.get("/health/ready")
    assert unavailable.status_code == 503
    assert unavailable.json == {"status": "unavailable"}
    redis_double.return_invalid = False

    redis_double.forced_get = b"unexpected-readiness-value"
    unavailable = client.get("/health/ready")
    assert unavailable.status_code == 503
    assert unavailable.json == {"status": "unavailable"}
    redis_double.forced_get = None
    for key in tuple(redis_double.scan_iter(match="msentra-template:readiness:*")):
        redis_double.delete(key.decode())
    assert list(redis_double.scan_iter(match="msentra-template:readiness:*")) == []


def test_transient_session_load_failure_preserves_cookie_and_recovers(
    settings: object,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    app = create_app(
        settings,  # type: ignore[arg-type]
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=GraphTransportDouble(),
    )
    client = app.test_client()

    login = client.get("/auth/login")
    state = parse_qs(urlsplit(login.headers["Location"]).query)["state"][0]
    assert (
        client.get("/auth/callback", query_string={"code": "code", "state": state}).status_code
        == 302
    )

    redis_double.fail = "get"
    unavailable = client.get("/profile")
    assert unavailable.status_code == 503
    assert unavailable.headers["Retry-After"] == "5"
    assert "Sessão temporariamente indisponível" in unavailable.text
    assert "Set-Cookie" not in unavailable.headers
    assert client.get("/health/live").status_code == 200
    assert client.get("/missing").status_code == 404

    redis_double.fail = None
    recovered = client.get("/profile")
    assert recovered.status_code == 200
    assert "Template User" in recovered.text


def test_session_save_failure_replaces_success_response_with_503(
    settings: object,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    app = create_app(
        settings,  # type: ignore[arg-type]
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=GraphTransportDouble(),
    )

    @app.get("/mutate-session")
    def mutate_session() -> str:
        session["value"] = "must-not-be-confirmed"
        return "must-not-leak"

    redis_double.fail = "set"
    response = app.test_client().get("/mutate-session")

    assert response.status_code == 503
    assert response.text == "Service Unavailable\n"
    assert response.headers["Retry-After"] == "5"
    assert response.headers["Cache-Control"] == "no-store, max-age=0"
    assert "must-not-leak" not in response.text
    assert "Set-Cookie" not in response.headers
