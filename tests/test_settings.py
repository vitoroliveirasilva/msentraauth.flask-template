from __future__ import annotations

import base64
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from conftest import cryptographic_key
from msentraauth_template.settings import AppSettings, ProxyHops, SettingsError


def valid_env() -> dict[str, str]:
    return {
        "APP_ENV": "development",
        "APP_SECRET_KEY": "development-secret-key-with-32-chars",
        "APP_BASE_URL": "http://localhost:5000",
        "APP_TRUSTED_HOSTS": "localhost,127.0.0.1,localhost",
        "APP_LOG_LEVEL": "debug",
        "APP_LOG_FORMAT": "json",
        "MS_ENTRA_CLIENT_ID": "client-id",
        "MS_ENTRA_CLIENT_SECRET": "client-secret-with-diversity-123456789",
        "MS_ENTRA_TENANT_ID": "tenant.example.test",
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
        "GRAPH_MAX_RESPONSE_BYTES": "131072",
        "GRAPH_MAX_RETRIES": "1",
        "GRAPH_MAX_RETRY_AFTER_SECONDS": "20",
        "PROXY_X_FOR": "1",
        "PROXY_X_PROTO": "1",
        "TESTING": "true",
        "DEBUG": "false",
        "WTF_CSRF_ENABLED": "false",
    }


def production_env() -> dict[str, str]:
    env = valid_env()
    env.update(
        APP_ENV="production",
        APP_SECRET_KEY=cryptographic_key(10),
        SESSION_SIGNING_KEYS=f"{cryptographic_key(20)},{cryptographic_key(30)}",
        WTF_CSRF_SECRET_KEY=cryptographic_key(40),
        APP_BASE_URL="https://app.example.test",
        APP_TRUSTED_HOSTS="app.example.test",
        MS_ENTRA_CLIENT_ID="11111111-1111-1111-1111-111111111111",
        MS_ENTRA_CLIENT_SECRET="Az9!client-secret-with-diversity-123456789",
        MS_ENTRA_TENANT_ID="22222222-2222-2222-2222-222222222222",
        MS_ENTRA_REDIRECT_URI="https://app.example.test/auth/callback",
        REDIS_URL="rediss://:secret@redis.example.test:6380/0",
        REDIS_TLS_REQUIRED="true",
        SESSION_COOKIE_SECURE="true",
        TESTING="false",
        DEBUG="false",
        WTF_CSRF_ENABLED="true",
    )
    return env


def test_loads_normalizes_and_exports_secure_configuration() -> None:
    settings = AppSettings.from_env(valid_env())
    settings.validate()

    assert settings.environment == "development"
    assert settings.trusted_hosts == ("localhost", "127.0.0.1")
    assert settings.log_level == "DEBUG"
    assert settings.scopes == ("User.Read", "Mail.Read")
    assert settings.session_signing_keys == ()
    assert settings.effective_session_signing_keys == (settings.secret_key,)
    assert settings.effective_csrf_secret_key == settings.secret_key
    assert settings.graph_max_response_bytes == 131072
    assert settings.graph_max_retries == 1
    assert settings.proxy_hops.any_enabled is True

    config = settings.flask_config()
    assert config["DEBUG"] is False
    assert config["SESSION_SIGNING_KEYS"] == (settings.secret_key,)
    assert config["WTF_CSRF_SECRET_KEY"] == settings.secret_key
    assert config["MS_ENTRA_REQUIRE_ATOMIC_STORAGE"] is True
    assert config["MAX_CONTENT_LENGTH"] == 1024 * 1024


def test_production_requires_independent_cryptographic_material() -> None:
    settings = AppSettings.from_env(production_env())
    assert settings.session_signing_keys == (cryptographic_key(20), cryptographic_key(30))
    assert settings.flask_config()["SESSION_COOKIE_NAME"] == "__Host-msentra_session"

    for missing in ("SESSION_SIGNING_KEYS", "WTF_CSRF_SECRET_KEY"):
        env = production_env()
        env.pop(missing)
        with pytest.raises(SettingsError, match=missing):
            AppSettings.from_env(env)

    duplicated = production_env()
    duplicated["WTF_CSRF_SECRET_KEY"] = duplicated["APP_SECRET_KEY"]
    with pytest.raises(SettingsError, match="independent"):
        AppSettings.from_env(duplicated)


def test_secret_sources_support_absolute_utf8_mounts(tmp_path: Path) -> None:
    env = production_env()
    mounted = {
        "APP_SECRET_KEY": cryptographic_key(50),
        "SESSION_SIGNING_KEYS": f"{cryptographic_key(60)}\n{cryptographic_key(70)}",
        "WTF_CSRF_SECRET_KEY": cryptographic_key(80),
        "MS_ENTRA_CLIENT_SECRET": "A9!mounted-client-secret-with-diversity-12345",
        "REDIS_URL": "rediss://:mounted@redis.example.test:6380/0",
    }
    for name, value in mounted.items():
        path = tmp_path / name.lower()
        path.write_text(f"{value}\n", encoding="utf-8")
        env.pop(name)
        env[f"{name}_FILE"] = str(path)

    settings = AppSettings.from_env(env)
    assert settings.secret_key == cryptographic_key(50)
    assert settings.session_signing_keys == (cryptographic_key(60), cryptographic_key(70))
    assert settings.redis_url.startswith("rediss://")


def test_secret_sources_reject_ambiguous_or_unsafe_files(tmp_path: Path) -> None:
    direct_and_file = valid_env()
    secret_file = tmp_path / "secret"
    secret_file.write_text("x" * 40, encoding="utf-8")
    direct_and_file["APP_SECRET_KEY_FILE"] = str(secret_file)
    with pytest.raises(SettingsError, match="cannot be configured together"):
        AppSettings.from_env(direct_and_file)

    relative = valid_env()
    relative.pop("APP_SECRET_KEY")
    relative["APP_SECRET_KEY_FILE"] = "relative-secret"
    with pytest.raises(SettingsError, match="absolute"):
        AppSettings.from_env(relative)

    missing = valid_env()
    missing.pop("APP_SECRET_KEY")
    missing["APP_SECRET_KEY_FILE"] = str(tmp_path / "missing")
    with pytest.raises(SettingsError, match="could not be read"):
        AppSettings.from_env(missing)

    directory = valid_env()
    directory.pop("APP_SECRET_KEY")
    directory["APP_SECRET_KEY_FILE"] = str(tmp_path)
    with pytest.raises(SettingsError, match="regular file"):
        AppSettings.from_env(directory)

    binary = tmp_path / "binary"
    binary.write_bytes(b"\xff")
    invalid_utf8 = valid_env()
    invalid_utf8.pop("APP_SECRET_KEY")
    invalid_utf8["APP_SECRET_KEY_FILE"] = str(binary)
    with pytest.raises(SettingsError, match="UTF-8"):
        AppSettings.from_env(invalid_utf8)

    empty = tmp_path / "empty"
    empty.write_text("\n", encoding="utf-8")
    empty_env = valid_env()
    empty_env.pop("APP_SECRET_KEY")
    empty_env["APP_SECRET_KEY_FILE"] = str(empty)
    with pytest.raises(SettingsError, match="empty"):
        AppSettings.from_env(empty_env)


def test_secret_validation_rejects_weak_invalid_and_oversized_values() -> None:
    cases = (
        ("APP_SECRET_KEY", "short", "32"),
        ("APP_SECRET_KEY", "!" * 40, "base64"),
        ("APP_SECRET_KEY", base64.urlsafe_b64encode(b"a" * 24).decode(), "32 random bytes"),
        ("MS_ENTRA_CLIENT_SECRET", "a" * 40, "diversity"),
        ("SESSION_SIGNING_KEYS", ",".join(cryptographic_key(i) for i in range(6)), "5"),
        (
            "SESSION_SIGNING_KEYS",
            f"{cryptographic_key(1)},{cryptographic_key(1)}",
            "duplicate",
        ),
    )
    for name, value, message in cases:
        env = production_env()
        env[name] = value
        with pytest.raises(SettingsError, match=message):
            AppSettings.from_env(env)


def test_rejects_invalid_environment_values_and_bounds() -> None:
    cases = (
        ("APP_ENV", "staging", "one of"),
        ("APP_LOG_LEVEL", "verbose", "one of"),
        ("APP_LOG_FORMAT", "xml", "one of"),
        ("SESSION_COOKIE_SECURE", "maybe", "boolean"),
        ("SESSION_LIFETIME_SECONDS", "0", "positive"),
        ("SESSION_LIFETIME_SECONDS", "86401", "exceed"),
        ("PROXY_X_FOR", "-1", "negative"),
        ("PROXY_X_FOR", "6", "exceed"),
        ("GRAPH_READ_TIMEOUT_SECONDS", "nan", "finite"),
        ("GRAPH_READ_TIMEOUT_SECONDS", "31", "exceed"),
        ("GRAPH_CONNECT_TIMEOUT_SECONDS", "11", "exceed"),
        ("REDIS_CONNECT_TIMEOUT_SECONDS", "31", "exceed"),
        ("REDIS_HEALTH_CHECK_INTERVAL_SECONDS", "301", "exceed"),
        ("GRAPH_MAX_RESPONSE_BYTES", "262145", "exceed"),
        ("GRAPH_MAX_RETRIES", "4", "exceed"),
        ("GRAPH_MAX_RETRY_AFTER_SECONDS", "121", "exceed"),
        ("SESSION_COOKIE_SAMESITE", "wild", "SAMESITE"),
    )
    for name, value, message in cases:
        env = valid_env()
        env[name] = value
        with pytest.raises(SettingsError, match=message):
            AppSettings.from_env(env)


def test_urls_hosts_tenant_and_graph_are_strictly_canonical() -> None:
    cases = (
        ("APP_BASE_URL", "relative", "absolute"),
        ("APP_BASE_URL", "https://user:pass@example.test", "safe"),
        ("APP_BASE_URL", "https://example.test/base", "only the origin"),
        ("APP_BASE_URL", "http://example.test", "HTTPS"),
        ("APP_BASE_URL", "http://localhost:5000?tenant=x", "query"),
        ("APP_TRUSTED_HOSTS", ".example.test", "wildcards"),
        ("APP_TRUSTED_HOSTS", "*.example.test", "wildcards"),
        ("APP_TRUSTED_HOSTS", "https://example.test", "host names only"),
        ("MS_ENTRA_TENANT_ID", "common", "one tenant"),
        ("MS_ENTRA_TENANT_ID", "organizations", "one tenant"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/", "non-root"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth/callback/", "non-root"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth//callback", "ambiguous"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth/../callback", "ambiguous"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth/callback?x=1", "query"),
        ("MS_ENTRA_REDIRECT_URI", "http://localhost:5000/auth%2Fcallback", "encoded"),
        ("GRAPH_BASE_URL", "http://graph.microsoft.com/v1.0", "HTTPS"),
        ("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0?x=1", "query"),
        ("GRAPH_BASE_URL", "https://evil.example/v1.0", "approved"),
        ("GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0/beta", "approved"),
    )
    for name, value, message in cases:
        env = valid_env()
        env[name] = value
        with pytest.raises(SettingsError, match=message):
            AppSettings.from_env(env)


def test_redirect_origin_and_exact_trusted_host_are_enforced() -> None:
    env = valid_env()
    env["MS_ENTRA_REDIRECT_URI"] = "http://127.0.0.1:5000/auth/callback"
    with pytest.raises(SettingsError, match="same origin"):
        AppSettings.from_env(env)

    env = valid_env()
    env["APP_TRUSTED_HOSTS"] = "example.test"
    with pytest.raises(SettingsError, match="include"):
        AppSettings.from_env(env)

    port = valid_env()
    port.update(
        APP_BASE_URL="http://localhost:5100",
        APP_TRUSTED_HOSTS="localhost:5100",
        MS_ENTRA_REDIRECT_URI="http://localhost:5100/auth/callback",
    )
    assert AppSettings.from_env(port).trusted_hosts == ("localhost:5100",)


def test_redis_factory_preserves_only_safe_url_options(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_from_url(url: str, **kwargs: object) -> object:
        captured.update(url=url, **kwargs)
        return object()

    monkeypatch.setattr("msentraauth_template.settings.Redis.from_url", fake_from_url)
    env = valid_env()
    env["REDIS_URL"] = "redis://localhost:6379/0?client_name=template"
    settings = AppSettings.from_env(env)
    assert settings.create_redis_client() is not None
    assert captured["decode_responses"] is False
    assert captured["socket_timeout"] == 2.5

    for query in (
        "decode_responses=true",
        "socket_timeout=0",
        "%64ecode_responses=true",
        "ssl_cert_reqs=none",
        "ssl_check_hostname=false",
    ):
        invalid = valid_env()
        invalid["REDIS_URL"] = f"redis://localhost:6379/0?{query}"
        with pytest.raises(SettingsError, match="application-controlled"):
            AppSettings.from_env(invalid)


def test_production_rejects_debug_testing_http_redis_and_disabled_csrf() -> None:
    changes = (
        ({"DEBUG": "true"}, "DEBUG"),
        ({"TESTING": "true"}, "TESTING"),
        ({"WTF_CSRF_ENABLED": "false"}, "WTF_CSRF_ENABLED"),
        ({"SESSION_COOKIE_SECURE": "false"}, "SESSION_COOKIE_SECURE"),
        (
            {"REDIS_TLS_REQUIRED": "false", "REDIS_URL": "redis://redis.example.test:6379/0"},
            "REDIS_TLS_REQUIRED",
        ),
    )
    for overrides, message in changes:
        env = production_env()
        env.update(overrides)
        with pytest.raises(SettingsError, match=message):
            AppSettings.from_env(env)


def test_directly_constructed_settings_receive_the_same_validation(settings: AppSettings) -> None:
    settings.validate()
    cases: tuple[tuple[dict[str, object], str], ...] = (
        ({"environment": "staging"}, "APP_ENV"),
        ({"debug": "false"}, "DEBUG"),
        ({"secret_key": "short"}, "APP_SECRET_KEY"),
        ({"session_signing_keys": "key"}, "ordered key ring"),
        ({"session_signing_keys": tuple(cryptographic_key(i) for i in range(6))}, "5"),
        ({"csrf_secret_key": 1}, "WTF_CSRF_SECRET_KEY"),
        ({"trusted_hosts": ".example.test"}, "APP_TRUSTED_HOSTS"),
        ({"client_id": 1}, "MS_ENTRA_CLIENT_ID"),
        ({"client_secret": "short"}, "MS_ENTRA_CLIENT_SECRET"),
        ({"tenant_id": "common"}, "one tenant"),
        ({"scopes": ("Mail.Read",)}, r"User\.Read"),
        ({"graph_base_url": "https://evil.example/v1.0"}, "approved"),
        ({"graph_max_response_bytes": True}, "GRAPH_MAX_RESPONSE_BYTES"),
        ({"graph_max_retries": -1}, "GRAPH_MAX_RETRIES"),
        ({"proxy_hops": object()}, "proxy_hops"),
    )
    for changes, message in cases:
        invalid = replace(settings, **cast(Any, changes))
        with pytest.raises(SettingsError, match=message):
            invalid.validate()


def test_testing_defaults_and_production_config(settings: AppSettings) -> None:
    testing_env = valid_env()
    testing_env["APP_ENV"] = "testing"
    for name in ("TESTING", "DEBUG", "WTF_CSRF_ENABLED"):
        testing_env.pop(name)
    testing = AppSettings.from_env(testing_env)
    assert testing.testing is True
    assert testing.debug is False
    assert testing.csrf_enabled is False

    production = AppSettings.from_env(production_env())
    config = production.flask_config()
    assert config["MS_ENTRA_STRICT_SECURITY"] is True
    assert config["PREFERRED_URL_SCHEME"] == "https"
    assert config["TEMPLATES_AUTO_RELOAD"] is False


def test_documented_placeholders_are_rejected_without_false_positives() -> None:
    for name, value in (
        ("APP_SECRET_KEY", "substitua-por-uma-chave-aleatoria-de-pelo-menos-32-caracteres"),
        ("MS_ENTRA_CLIENT_ID", "substitua-pelo-client-id"),
        ("MS_ENTRA_CLIENT_SECRET", "replace-me-please-but-long-enough"),
        ("MS_ENTRA_TENANT_ID", "substitua-pelo-tenant-id"),
    ):
        env = valid_env()
        env[name] = value
        with pytest.raises(SettingsError, match="placeholder"):
            AppSettings.from_env(env)

    env = valid_env()
    env["APP_SECRET_KEY"] = "safe-replace-token-" + ("x" * 32)
    env["MS_ENTRA_CLIENT_SECRET"] = "secret-with-replace-inside-" + ("x" * 24)
    env["MS_ENTRA_TENANT_ID"] = "replace-industries.example.test"
    assert AppSettings.from_env(env).tenant_id == "replace-industries.example.test"


def test_missing_values_empty_lists_and_control_characters_are_rejected() -> None:
    env = valid_env()
    env.pop("MS_ENTRA_CLIENT_ID")
    with pytest.raises(SettingsError, match="required"):
        AppSettings.from_env(env)

    env = valid_env()
    env["MS_ENTRA_SCOPES"] = ", ,"
    with pytest.raises(SettingsError, match="at least one"):
        AppSettings.from_env(env)

    env = valid_env()
    env["APP_BASE_URL"] = "http://localhost:5000/%0A"
    with pytest.raises(SettingsError, match="control"):
        AppSettings.from_env(env)


def test_additional_parser_and_direct_validation_edges(
    settings: AppSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    no_scope = valid_env()
    no_scope["MS_ENTRA_SCOPES"] = "Mail.Read"
    with pytest.raises(SettingsError, match=r"User\.Read"):
        AppSettings.from_env(no_scope)

    defaults = valid_env()
    for name in (
        "REDIS_CONNECT_TIMEOUT_SECONDS",
        "REDIS_READ_TIMEOUT_SECONDS",
        "GRAPH_CONNECT_TIMEOUT_SECONDS",
        "GRAPH_READ_TIMEOUT_SECONDS",
    ):
        defaults.pop(name)
    assert AppSettings.from_env(defaults).graph_read_timeout == 10.0

    for name, value, message in (
        ("GRAPH_MAX_RETRIES", "invalid", "integer"),
        ("GRAPH_READ_TIMEOUT_SECONDS", "invalid", "numeric"),
        ("MS_ENTRA_CLIENT_ID", "not-a-uuid", "UUID"),
        ("MS_ENTRA_TENANT_ID", "https://tenant.example", "tenant UUID"),
        ("REDIS_URL", "redis://localhost:6379/0", "rediss"),
    ):
        env = production_env()
        env[name] = value
        if name == "REDIS_URL":
            env["REDIS_TLS_REQUIRED"] = "true"
        with pytest.raises(SettingsError, match=message):
            AppSettings.from_env(env)

    tls = AppSettings.from_env(production_env())
    captured: dict[str, object] = {}

    def fake_from_url(url: str, **kwargs: object) -> object:
        captured.update(url=url, **kwargs)
        return object()

    monkeypatch.setattr("msentraauth_template.settings.Redis.from_url", fake_from_url)
    assert tls.create_redis_client() is not None
    assert captured["ssl_cert_reqs"] == "required"
    assert captured["ssl_check_hostname"] is True

    direct_cases: tuple[tuple[dict[str, object], str], ...] = (
        ({"log_level": "info"}, "normalized"),
        ({"scopes": ()}, "at least one"),
        ({"graph_max_retries": "2"}, "integer"),
        ({"graph_max_response_bytes": 0}, "positive"),
        ({"graph_read_timeout": True}, "numeric"),
        ({"graph_read_timeout": 0.0}, "positive"),
        ({"graph_read_timeout": float("inf")}, "finite"),
        ({"graph_read_timeout": 31.0}, "exceed"),
        ({"client_secret": "x" * 4097}, "too long"),
    )
    for changes, message in direct_cases:
        with pytest.raises(SettingsError, match=message):
            replace(settings, **cast(Any, changes)).validate()


def test_additional_url_host_and_production_edges(settings: AppSettings) -> None:
    for value, message in (
        ("http://localhost:5000/" + ("a" * 240), "256"),
        ("http://localhost:5000/auth/call;back", "unsupported"),
        (r"http://localhost:5000/auth\callback", "unsupported"),
        ("http://localhost:5000/auth/callback#fragment", "fragment"),
        ("http://localhost:invalid/auth/callback", "invalid port"),
        ("http://localhost:0/auth/callback", "invalid port"),
        ("http://localhost:5000/%252525252fcallback", "excessive"),
    ):
        env = valid_env()
        env["MS_ENTRA_REDIRECT_URI"] = value
        with pytest.raises(SettingsError, match=message):
            AppSettings.from_env(env)

    for value, message in (
        ("[::1", "IPv6"),
        ("[::1]:invalid", "port"),
        ("[::1]:0", "port"),
        ("bad_host.example", "invalid host"),
    ):
        env = valid_env()
        env["APP_TRUSTED_HOSTS"] = value
        with pytest.raises(SettingsError, match=message):
            AppSettings.from_env(env)

    ipv6 = valid_env()
    ipv6.update(
        APP_BASE_URL="http://[::1]:5000",
        APP_TRUSTED_HOSTS="[::1]",
        MS_ENTRA_REDIRECT_URI="http://[::1]:5000/auth/callback",
    )
    assert AppSettings.from_env(ipv6).trusted_hosts == ("[::1]",)

    same_site = valid_env()
    same_site["SESSION_COOKIE_SAMESITE"] = "None"
    with pytest.raises(SettingsError, match="SECURE"):
        AppSettings.from_env(same_site)

    unsafe_loopback_production = replace(
        AppSettings.from_env(production_env()),
        base_url="http://localhost",
        redirect_uri="http://localhost/auth/callback",
        trusted_hosts=("localhost",),
    )
    with pytest.raises(SettingsError, match="HTTPS in production"):
        unsafe_loopback_production.validate()


def test_remaining_security_parser_edges(settings: AppSettings) -> None:
    import msentraauth_template.settings as settings_module

    production = AppSettings.from_env(production_env())
    with pytest.raises(SettingsError, match="SESSION_SIGNING_KEYS"):
        replace(production, session_signing_keys=()).validate()
    with pytest.raises(SettingsError, match="WTF_CSRF_SECRET_KEY"):
        replace(production, csrf_secret_key="").validate()

    invalid_base64_length = production_env()
    invalid_base64_length["APP_SECRET_KEY"] = "A" * 33
    with pytest.raises(SettingsError, match="base64"):
        AppSettings.from_env(invalid_base64_length)

    backslash = valid_env()
    backslash["APP_BASE_URL"] = r"http://localhost:5000\path"
    with pytest.raises(SettingsError, match="backslash"):
        AppSettings.from_env(backslash)

    excessive = valid_env()
    excessive["APP_BASE_URL"] = "http://localhost:5000/%252525252f"
    with pytest.raises(SettingsError, match="excessive"):
        AppSettings.from_env(excessive)

    invalid_colon_host = valid_env()
    invalid_colon_host["APP_TRUSTED_HOSTS"] = "localhost:not-a-port"
    with pytest.raises(SettingsError, match="invalid host"):
        AppSettings.from_env(invalid_colon_host)

    with pytest.raises(SettingsError, match="at least one"):
        replace(settings, trusted_hosts=()).validate()
    with pytest.raises(SettingsError, match="invalid host"):
        settings_module._canonical_hostname("", "TEST_HOST")
    with pytest.raises(SettingsError, match="invalid host"):
        settings_module._canonical_hostname("\ud800.example", "TEST_HOST")


def test_internal_normalization_completion_and_host_deduplication() -> None:
    import msentraauth_template.settings as settings_module

    assert settings_module._decode_url_layers("%25252f", "TEST_URL") == "/"
    assert settings_module._trusted_hosts(("localhost", "localhost")) == ("localhost",)
    with pytest.raises(SettingsError, match="at least one"):
        settings_module._trusted_hosts(())
