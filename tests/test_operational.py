from __future__ import annotations

from dataclasses import replace
from runpy import run_path

import pytest
from werkzeug.middleware.proxy_fix import ProxyFix

from conftest import FakeMsalClient, GraphResponse, GraphTransportDouble, RedisDouble
from msentraauth_template import create_app
from msentraauth_template.settings import AppSettings, ProxyHops


def test_proxy_hsts_invalid_ready_and_graph_error(
    settings: AppSettings,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    secure = replace(
        settings,
        environment="production",
        base_url="https://localhost",
        redirect_uri="https://localhost/auth/callback",
        cookie_secure=True,
        redis_url="rediss://redis.example.test:6380/0",
        redis_tls_required=True,
        testing=False,
        csrf_enabled=True,
        proxy_hops=ProxyHops(x_for=1, x_proto=1),
    )
    transport = GraphTransportDouble()
    app = create_app(
        secure,
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=transport,
    )
    assert isinstance(app.wsgi_app, ProxyFix)
    client = app.test_client()
    response = client.get("/health/live", base_url="https://localhost")
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

    app.extensions["template_redis"] = object()
    assert client.get("/health/ready", base_url="https://localhost").status_code == 503

    # Restore Redis and complete authentication before exercising Graph's handler.
    app.extensions["template_redis"] = redis_double
    login = client.get("/auth/login", base_url="https://localhost")
    location = login.headers["Location"]
    state = location.split("state=", 1)[1]
    callback = client.get(
        "/auth/callback",
        query_string={"code": "code", "state": state},
        base_url="https://localhost",
    )
    assert callback.status_code == 302
    transport.response = GraphResponse(500, {})
    graph = client.get("/profile", base_url="https://localhost")
    assert graph.status_code == 503
    assert "Microsoft Graph indisponível" in graph.text


def test_graph_unauthorized_and_invalid_response_handlers(
    settings: AppSettings,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    transport = GraphTransportDouble()
    app = create_app(
        settings,
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=transport,
    )
    client = app.test_client()
    login = client.get("/auth/login")
    state = login.headers["Location"].split("state=", 1)[1]
    assert (
        client.get("/auth/callback", query_string={"code": "code", "state": state}).status_code
        == 302
    )

    transport.response = GraphResponse(401, {})
    unauthorized = client.get("/profile")
    assert unauthorized.status_code == 502
    assert "recusou o acesso" in unauthorized.text

    transport.response = GraphResponse(400, {})
    invalid = client.get("/profile")
    assert invalid.status_code == 502
    assert "Resposta inválida" in invalid.text


def test_static_assets_keep_cache_policy(
    settings: AppSettings,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    app = create_app(
        settings,
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=GraphTransportDouble(),
    )
    response = app.test_client().get("/static/app.css")
    assert response.status_code == 200
    assert response.headers.get("Cache-Control") != "no-store, max-age=0"
    assert "Pragma" not in response.headers


def test_gunicorn_access_log_omits_callback_query_string() -> None:
    config = run_path("gunicorn.conf.py")
    access_format = config["access_log_format"]

    assert config["bind"] == "0.0.0.0:8000"
    assert config["workers"] == 2
    assert config["threads"] == 4
    assert "%(U)s" in access_format
    assert "%(q)s" not in access_format
    assert "%(r)s" not in access_format


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("PORT", "0"),
        ("PORT", "65536"),
        ("WEB_CONCURRENCY", "abc"),
        ("GUNICORN_THREADS", "-1"),
        ("GUNICORN_TIMEOUT", "3601"),
        ("GUNICORN_KEEPALIVE", "-1"),
        ("GUNICORN_MAX_REQUESTS", "10000001"),
    ],
)
def test_gunicorn_rejects_invalid_integer_configuration(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    for variable in (
        "PORT",
        "WEB_CONCURRENCY",
        "GUNICORN_THREADS",
        "GUNICORN_TIMEOUT",
        "GUNICORN_GRACEFUL_TIMEOUT",
        "GUNICORN_KEEPALIVE",
        "GUNICORN_MAX_REQUESTS",
        "GUNICORN_MAX_REQUESTS_JITTER",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match=name):
        run_path("gunicorn.conf.py")


def test_gunicorn_accepts_bounded_integer_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("WEB_CONCURRENCY", "3")
    monkeypatch.setenv("GUNICORN_THREADS", "8")
    monkeypatch.setenv("GUNICORN_MAX_REQUESTS", "0")
    monkeypatch.setenv("GUNICORN_MAX_REQUESTS_JITTER", "0")

    config = run_path("gunicorn.conf.py")
    assert config["bind"] == "0.0.0.0:9000"
    assert config["workers"] == 3
    assert config["threads"] == 8
    assert config["max_requests"] == 0
