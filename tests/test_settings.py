from __future__ import annotations

from dataclasses import replace
from typing import Any, cast

import pytest

from msentraauth_template.settings import AppSettings, ProxyHops, SettingsError


def valid_env() -> dict[str, str]:
    return {
        "APP_ENV": "development",
        "APP_SECRET_KEY": "a" * 32,
        "APP_BASE_URL": "http://localhost:5000",
        "APP_TRUSTED_HOSTS": "localhost,127.0.0.1,localhost",
        "APP_LOG_LEVEL": "debug",
        "APP_LOG_FORMAT": "json",
        "MS_ENTRA_CLIENT_ID": "client-id",
        "MS_ENTRA_CLIENT_SECRET": "b" * 32,
        "MS_ENTRA_TENANT_ID": "tenant-id",
        "MS_ENTRA_REDIRECT_URI": "http://localhost:5000/auth/callback",
        "MS_ENTRA_SCOPES": "User.Read, Mail.Read,User.Read",
        "REDIS_URL": "redis://:secret@localhost:6379/0",
        "REDIS_TLS_REQUIRED": "false",
        "REDIS_CONNECT_TIMEOUT_SECONDS": "1.25",
        "REDIS_READ_TIMEOUT_SECONDS": "2.5",
        "REDIS_HEALTH_CHECK_INTERVAL_SECONDS": "20",
        "SESSION_LIFETIME_SECONDS": "7200",
        "SESSION_REFRESH_EACH_REQUEST": "false",
        "SESSION_COOKIE_SECURE": "false",
        "SESSION_COOKIE_SAMESITE": "strict",
        "GRAPH_CONNECT_TIMEOUT_SECONDS": "1.5",
        "GRAPH_READ_TIMEOUT_SECONDS": "4",
        "PROXY_X_FOR": "1",
        "PROXY_X_PROTO": "1",
        "TESTING": "true",
        "WTF_CSRF_ENABLED": "false",
    }


def production_env() -> dict[str, str]:
    env = valid_env()
    env.update(
        APP_ENV="production",
        APP_BASE_URL="https://app.example.test",
        APP_TRUSTED_HOSTS="app.example.test",
        MS_ENTRA_REDIRECT_URI="https://app.example.test/auth/callback",
        REDIS_URL="rediss://:secret@redis.example.test:6380/0",
        REDIS_TLS_REQUIRED="true",
        SESSION_COOKIE_SECURE="true",
        TESTING="false",
        WTF_CSRF_ENABLED="true",
    )
    return env


def test_loads_and_normalizes_environment() -> None:
    settings = AppSettings.from_env(valid_env())
    settings.validate()
    assert settings.environment == "development"
    assert settings.trusted_hosts == ("localhost", "127.0.0.1")
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"
    assert settings.scopes == ("User.Read", "Mail.Read")
    assert settings.redis_socket_connect_timeout == 1.25
    assert settings.redis_socket_timeout == 2.5
    assert settings.redis_health_check_interval == 20
    assert settings.redis_tls_required is False
    assert settings.session_lifetime_seconds == 7200
    assert settings.session_refresh_each_request is False
    assert settings.cookie_samesite == "Strict"
    assert settings.proxy_hops.any_enabled is True
    assert settings.testing is True
    assert settings.csrf_enabled is False
    config = settings.flask_config()
    assert config["SESSION_COOKIE_NAME"] == "msentra_session"
    assert config["SESSION_REFRESH_EACH_REQUEST"] is False
    assert config["MS_ENTRA_REQUIRE_ATOMIC_STORAGE"] is True
    assert config["MS_ENTRA_STRICT_SECURITY"] is False
    assert config["MAX_CONTENT_LENGTH"] == 1024 * 1024


def test_defaults_and_redis_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    env = valid_env()
    for key in (
        "APP_ENV",
        "APP_LOG_LEVEL",
        "APP_LOG_FORMAT",
        "MS_ENTRA_SCOPES",
        "REDIS_TLS_REQUIRED",
        "REDIS_CONNECT_TIMEOUT_SECONDS",
        "REDIS_READ_TIMEOUT_SECONDS",
        "REDIS_HEALTH_CHECK_INTERVAL_SECONDS",
        "SESSION_LIFETIME_SECONDS",
        "SESSION_REFRESH_EACH_REQUEST",
        "SESSION_COOKIE_SECURE",
        "SESSION_COOKIE_SAMESITE",
        "GRAPH_CONNECT_TIMEOUT_SECONDS",
        "GRAPH_READ_TIMEOUT_SECONDS",
        "PROXY_X_FOR",
        "PROXY_X_PROTO",
        "TESTING",
        "WTF_CSRF_ENABLED",
    ):
        env.pop(key)
    env.update(
        APP_BASE_URL="https://app.example.test",
        APP_TRUSTED_HOSTS="app.example.test",
        MS_ENTRA_REDIRECT_URI="https://app.example.test/auth/callback",
        REDIS_URL="rediss://:secret@redis.example.test:6380/0",
    )
    captured: dict[str, object] = {}

    def fake_from_url(url: str, **kwargs: object) -> object:
        captured.update(url=url, **kwargs)
        return object()

    monkeypatch.setattr("msentraauth_template.settings.Redis.from_url", fake_from_url)
    settings = AppSettings.from_env(env)
    assert settings.environment == "production"
    assert settings.log_format == "json"
    assert settings.cookie_secure is True
    assert settings.csrf_enabled is True
    assert settings.redis_tls_required is True
    assert settings.proxy_hops == ProxyHops()
    assert settings.create_redis_client() is not None
    assert captured == {
        "url": "rediss://:secret@redis.example.test:6380/0",
        "decode_responses": False,
        "socket_connect_timeout": 3.0,
        "socket_timeout": 3.0,
        "health_check_interval": 30,
    }


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("APP_ENV", "staging", "one of"),
        ("APP_LOG_LEVEL", "verbose", "one of"),
        ("APP_LOG_FORMAT", "xml", "one of"),
        ("APP_SECRET_KEY", "short", "32"),
        ("MS_ENTRA_CLIENT_SECRET", "replace-me-please-but-long-enough", "placeholder"),
        ("SESSION_COOKIE_SECURE", "maybe", "boolean"),
        ("SESSION_LIFETIME_SECONDS", "abc", "integer"),
        ("SESSION_LIFETIME_SECONDS", "0", "positive"),
        ("PROXY_X_FOR", "-1", "negative"),
        ("PROXY_X_FOR", "6", "exceed"),
        ("GRAPH_READ_TIMEOUT_SECONDS", "abc", "numeric"),
        ("GRAPH_READ_TIMEOUT_SECONDS", "0", "positive"),
        ("GRAPH_READ_TIMEOUT_SECONDS", "nan", "finite"),
        ("GRAPH_READ_TIMEOUT_SECONDS", "inf", "finite"),
        ("REDIS_CONNECT_TIMEOUT_SECONDS", "-inf", "finite"),
        ("SESSION_COOKIE_SAMESITE", "wild", "SAMESITE"),
        ("APP_BASE_URL", "relative", "absolute"),
        ("APP_BASE_URL", "https://user:pass@example.test", "safe"),
        ("APP_BASE_URL", "https://example.test/#fragment", "fragment"),
        ("APP_BASE_URL", "http://localhost:5000?tenant=x", "query"),
        ("APP_BASE_URL", "http://localhost:5000/%0Apath", "control"),
        (r"APP_BASE_URL", r"http://localhost:5000\path", "backslash"),
        ("APP_BASE_URL", "http://localhost:invalid", "invalid port"),
        ("APP_BASE_URL", "http://localhost:0", "invalid port"),
        ("MS_ENTRA_SCOPES", "Mail.Read", "User.Read"),
        ("REDIS_URL", "https://example.test", "absolute"),
        ("GRAPH_BASE_URL", "http://localhost:5000/v1.0", "HTTPS"),
        ("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0?tenant=x", "query"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth/call;back", "unsupported"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth/%3Ccallback%3E", "unsupported"),
        (r"MS_ENTRA_REDIRECT_URI", r"http://localhost:5000/auth\callback", "unsupported"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth/%0Acallback", "control"),
    ],
)
def test_rejects_invalid_values(name: str, value: str, message: str) -> None:
    env = valid_env()
    env[name] = value
    with pytest.raises(SettingsError, match=message):
        AppSettings.from_env(env)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (
            "APP_SECRET_KEY",
            "substitua-por-uma-chave-aleatoria-de-pelo-menos-32-caracteres",
        ),
        ("MS_ENTRA_CLIENT_ID", "substitua-pelo-client-id"),
        ("MS_ENTRA_CLIENT_SECRET", "substitua-pelo-client-secret"),
        ("MS_ENTRA_TENANT_ID", "substitua-pelo-tenant-id"),
    ],
)
def test_rejects_documented_placeholders(name: str, value: str) -> None:
    env = valid_env()
    env[name] = value
    with pytest.raises(SettingsError, match="placeholder"):
        AppSettings.from_env(env)


def test_requires_values_and_non_empty_csv() -> None:
    env = valid_env()
    env.pop("MS_ENTRA_CLIENT_ID")
    with pytest.raises(SettingsError, match="required"):
        AppSettings.from_env(env)
    env = valid_env()
    env["MS_ENTRA_SCOPES"] = ", ,"
    with pytest.raises(SettingsError, match="at least one"):
        AppSettings.from_env(env)


def test_production_requires_https_secure_cookie_tls_csrf_and_non_testing() -> None:
    env = valid_env() | {"APP_ENV": "production"}
    env.pop("REDIS_TLS_REQUIRED")
    with pytest.raises(SettingsError, match="rediss"):
        AppSettings.from_env(env)

    env["REDIS_URL"] = "rediss://redis.example.test:6380/0"
    with pytest.raises(SettingsError, match="HTTPS"):
        AppSettings.from_env(env)

    env.update(
        APP_BASE_URL="https://app.example.test",
        APP_TRUSTED_HOSTS="app.example.test",
        MS_ENTRA_REDIRECT_URI="https://app.example.test/auth/callback",
        SESSION_COOKIE_SECURE="false",
    )
    with pytest.raises(SettingsError, match="must be true"):
        AppSettings.from_env(env)

    env = production_env()
    env["REDIS_TLS_REQUIRED"] = "false"
    env["REDIS_URL"] = "redis://redis.example.test:6379/0"
    with pytest.raises(SettingsError, match="REDIS_TLS_REQUIRED"):
        AppSettings.from_env(env)

    env = production_env()
    env["TESTING"] = "true"
    with pytest.raises(SettingsError, match="TESTING"):
        AppSettings.from_env(env)

    env = production_env()
    env["WTF_CSRF_ENABLED"] = "false"
    with pytest.raises(SettingsError, match="WTF_CSRF_ENABLED"):
        AppSettings.from_env(env)


def test_redirect_origin_trusted_host_and_samesite_are_validated() -> None:
    env = valid_env()
    env["MS_ENTRA_REDIRECT_URI"] = "http://app.example.test/auth/callback"
    with pytest.raises(SettingsError, match="HTTPS"):
        AppSettings.from_env(env)

    env = valid_env()
    env["MS_ENTRA_REDIRECT_URI"] = "http://127.0.0.1:5000/auth/callback"
    with pytest.raises(SettingsError, match="same origin"):
        AppSettings.from_env(env)

    env = valid_env()
    env["APP_TRUSTED_HOSTS"] = "example.test"
    with pytest.raises(SettingsError, match="include"):
        AppSettings.from_env(env)

    env = valid_env()
    env["SESSION_COOKIE_SAMESITE"] = "None"
    with pytest.raises(SettingsError, match="SECURE"):
        AppSettings.from_env(env)


def test_redirect_uri_limits_idn_and_single_tenant_query_support() -> None:
    query = valid_env()
    query["MS_ENTRA_REDIRECT_URI"] = "http://localhost:5000/auth/callback?source=corporate"
    assert AppSettings.from_env(query).redirect_uri.endswith("?source=corporate")

    too_long = valid_env()
    too_long["MS_ENTRA_REDIRECT_URI"] = "http://localhost:5000/" + ("a" * 240)
    with pytest.raises(SettingsError, match="256"):
        AppSettings.from_env(too_long)

    for hostname in ("tést.example", "xn--tst-bma.example"):
        internationalized = valid_env()
        internationalized["MS_ENTRA_REDIRECT_URI"] = f"https://{hostname}/auth/callback"
        with pytest.raises(SettingsError, match="internationalized"):
            AppSettings.from_env(internationalized)


def test_subdomain_trust_default_ports_redis_credentials_and_loopback_are_supported() -> None:
    env = valid_env()
    env.update(
        APP_BASE_URL="https://app.example.test",
        APP_TRUSTED_HOSTS=".example.test",
        MS_ENTRA_REDIRECT_URI="https://app.example.test:443/auth/callback",
        REDIS_URL="rediss://service-user:secret@redis.example.test:6380/0",
        REDIS_TLS_REQUIRED="true",
        SESSION_COOKIE_SECURE="true",
    )
    settings = AppSettings.from_env(env)
    assert settings.redis_url.startswith("rediss://service-user:")

    loopback = valid_env()
    loopback.update(
        APP_BASE_URL="http://127.0.0.2:5000",
        APP_TRUSTED_HOSTS="127.0.0.2",
        MS_ENTRA_REDIRECT_URI="http://127.0.0.2:5000/auth/callback",
    )
    assert AppSettings.from_env(loopback).base_url == "http://127.0.0.2:5000"


def test_directly_constructed_settings_are_validated(settings: AppSettings) -> None:
    unsafe_production = replace(
        settings,
        environment="production",
        base_url="https://app.example.test",
        redirect_uri="https://app.example.test/auth/callback",
        trusted_hosts=("app.example.test",),
        cookie_secure=True,
        testing=False,
        csrf_enabled=True,
        redis_url="redis://redis.example.test:6379/0",
        redis_tls_required=False,
    )
    with pytest.raises(SettingsError, match="REDIS_TLS_REQUIRED"):
        unsafe_production.flask_config()

    non_finite = replace(settings, graph_read_timeout=float("nan"))
    with pytest.raises(SettingsError, match="finite"):
        non_finite.flask_config()

    insufficient_scope = replace(settings, scopes=("Mail.Read",))
    with pytest.raises(SettingsError, match=r"User\.Read"):
        insufficient_scope.flask_config()


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"environment": "staging"}, "APP_ENV"),
        ({"secret_key": "short"}, "APP_SECRET_KEY"),
        ({"trusted_hosts": ()}, "APP_TRUSTED_HOSTS"),
        ({"trusted_hosts": "localhost"}, "APP_TRUSTED_HOSTS"),
        ({"trusted_hosts": ("",)}, "APP_TRUSTED_HOSTS"),
        ({"log_level": "verbose"}, "APP_LOG_LEVEL"),
        ({"log_level": "info"}, "normalized"),
        ({"log_format": "xml"}, "APP_LOG_FORMAT"),
        ({"client_id": 1}, "MS_ENTRA_CLIENT_ID"),
        ({"client_id": "replace-me"}, "placeholder"),
        ({"client_secret": "short"}, "MS_ENTRA_CLIENT_SECRET"),
        ({"tenant_id": ""}, "MS_ENTRA_TENANT_ID"),
        ({"scopes": []}, "MS_ENTRA_SCOPES"),
        ({"redis_tls_required": "false"}, "REDIS_TLS_REQUIRED"),
        ({"redis_health_check_interval": True}, "REDIS_HEALTH_CHECK_INTERVAL_SECONDS"),
        ({"redis_health_check_interval": "30"}, "REDIS_HEALTH_CHECK_INTERVAL_SECONDS"),
        ({"redis_health_check_interval": -1}, "REDIS_HEALTH_CHECK_INTERVAL_SECONDS"),
        ({"session_lifetime_seconds": 0}, "SESSION_LIFETIME_SECONDS"),
        ({"session_refresh_each_request": "true"}, "SESSION_REFRESH_EACH_REQUEST"),
        ({"cookie_secure": "false"}, "SESSION_COOKIE_SECURE"),
        ({"cookie_samesite": "wild"}, "SESSION_COOKIE_SAMESITE"),
        ({"graph_connect_timeout": "1"}, "GRAPH_CONNECT_TIMEOUT_SECONDS"),
        ({"graph_connect_timeout": True}, "GRAPH_CONNECT_TIMEOUT_SECONDS"),
        ({"base_url": "http://localhost:5000?tenant=x"}, "query"),
        ({"graph_base_url": "https://graph.microsoft.com/v1.0?tenant=x"}, "query"),
        ({"redirect_uri": "http://localhost:5000/auth/call;back"}, "unsupported"),
        ({"proxy_hops": object()}, "proxy_hops"),
        ({"proxy_hops": ProxyHops(x_for=-1)}, "PROXY_X_FOR"),
        ({"proxy_hops": ProxyHops(x_for=6)}, "PROXY_X_FOR"),
        ({"testing": "false"}, "TESTING"),
        ({"csrf_enabled": "true"}, "WTF_CSRF_ENABLED"),
    ],
)
def test_direct_settings_reject_invalid_runtime_values(
    settings: AppSettings,
    changes: dict[str, object],
    message: str,
) -> None:
    invalid = replace(settings, **cast(Any, changes))
    with pytest.raises(SettingsError, match=message):
        invalid.validate()


def test_testing_defaults_and_production_flask_config(settings: AppSettings) -> None:
    testing_env = valid_env()
    testing_env["APP_ENV"] = "testing"
    testing_env.pop("TESTING")
    testing_env.pop("WTF_CSRF_ENABLED")
    testing = AppSettings.from_env(testing_env)
    assert testing.testing is True
    assert testing.csrf_enabled is False

    production = replace(
        settings,
        environment="production",
        base_url="https://app.example.test",
        redirect_uri="https://app.example.test/auth/callback",
        trusted_hosts=("app.example.test",),
        redis_url="rediss://redis.example.test:6380/0",
        redis_tls_required=True,
        cookie_secure=True,
        testing=False,
        csrf_enabled=True,
    )
    config = production.flask_config()
    assert config["MS_ENTRA_STRICT_SECURITY"] is True
    assert config["SESSION_COOKIE_NAME"] == "__Host-msentra_session"
    assert config["PREFERRED_URL_SCHEME"] == "https"
