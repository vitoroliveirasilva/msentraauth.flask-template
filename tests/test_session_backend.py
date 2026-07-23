from __future__ import annotations

from datetime import timedelta

import pytest
from flask import Flask, Response, request

from conftest import RedisDouble
from msentraauth_template.session_backend import (
    RedisSession,
    RedisSessionInterface,
    SessionBackendError,
)
from msentraauth_template.session_envelope import SessionEnvelopeCodec


class Clock:
    def __init__(self, value: float = 1_000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def codec(*keys: str, idle: int = 60, absolute: int = 300, renewal: int = 30) -> SessionEnvelopeCodec:
    return SessionEnvelopeCodec(
        keys or ("p" * 32,),
        namespace="template-test",
        idle_timeout_seconds=idle,
        absolute_timeout_seconds=absolute,
        sid_renewal_seconds=renewal,
        clock_skew_seconds=5,
        allowed_keys=("value",),
        strict_schema=True,
    )


def make_app(
    redis: RedisDouble,
    *,
    clock: Clock | None = None,
    payload_codec: SessionEnvelopeCodec | None = None,
    signing_keys: tuple[str, ...] = ("s" * 32,),
) -> tuple[Flask, RedisSessionInterface, Clock]:
    app = Flask("session-test")
    app.secret_key = "a" * 32
    app.config.from_mapping(
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_PERMANENT=True,
        SESSION_REFRESH_EACH_REQUEST=False,
        SESSION_SIGNING_KEYS=signing_keys,
    )
    app.permanent_session_lifetime = timedelta(seconds=60)
    resolved_clock = clock or Clock()
    interface = RedisSessionInterface(
        redis,
        codec=payload_codec or codec(),
        key_prefix="template-test:session:",
        revocation_prefix="template-test:revocation:",
        clock=resolved_clock,
    )
    app.session_interface = interface
    return app, interface, resolved_clock


def cookie_value(response: Response) -> str:
    return response.headers["Set-Cookie"].split(";", 1)[0].split("=", 1)[1]


def persisted_session(
    app: Flask,
    interface: RedisSessionInterface,
    *,
    value: str = "stored",
) -> tuple[RedisSession, str, Response]:
    with app.test_request_context("/"):
        opened = interface.open_session(app, request)
    opened["value"] = value
    response = Response()
    interface.save_session(app, opened, response)
    return opened, cookie_value(response), response


def open_cookie(app: Flask, interface: RedisSessionInterface, signed: str) -> RedisSession:
    with app.test_request_context("/", headers={"Cookie": f"session={signed}"}):
        return interface.open_session(app, request)


def test_new_save_load_uses_aead_and_no_refresh(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    opened, signed, _ = persisted_session(app, interface)
    raw = redis_double.get(f"template-test:session:{opened.sid}")
    assert raw is not None
    assert b"stored" not in raw

    restored = open_cookie(app, interface, signed)
    assert restored.new is False
    assert restored["value"] == "stored"
    assert restored.sid == opened.sid
    untouched = Response()
    interface.save_session(app, restored, untouched)
    assert "Set-Cookie" not in untouched.headers


def test_empty_anonymous_and_stateless_requests_do_not_touch_redis(
    redis_double: RedisDouble,
) -> None:
    app, interface, _ = make_app(redis_double)
    with app.test_request_context("/"):
        empty = interface.open_session(app, request)
    interface.save_session(app, empty, Response())
    assert list(redis_double.scan_iter()) == []

    redis_double.fail = "get"
    for path in ("/health/live", "/health/ready", "/static/app.css"):
        with app.test_request_context(path):
            stateless = interface.open_session(app, request)
        assert stateless.stateless is True
        stateless["value"] = path
        interface.save_session(app, stateless, Response())


def test_tampered_or_unknown_envelope_is_deleted_safely(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    opened, signed, _ = persisted_session(app, interface)
    key = f"template-test:session:{opened.sid}"
    raw = bytearray(redis_double.get(key) or b"")
    raw[-2] ^= 1
    redis_double.set(key, bytes(raw), xx=True)

    rejected = open_cookie(app, interface, signed)
    assert rejected.new is True
    assert rejected.discard_cookie is True
    assert redis_double.get(key) is None
    response = Response()
    interface.save_session(app, rejected, response)
    assert "Max-Age=0" in response.headers["Set-Cookie"]


def test_invalid_cleanup_fails_closed_when_value_changes(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    opened, signed, _ = persisted_session(app, interface)
    key = f"template-test:session:{opened.sid}"
    redis_double.set(key, b"invalid", xx=True)

    original_eval = redis_double.eval

    def changed(script: str, numkeys: int, *values: object) -> object:
        if "current ~= ARGV[1]" in script:
            redis_double.set(key, b"replacement", xx=True)
        return original_eval(script, numkeys, *values)

    redis_double.eval = changed  # type: ignore[method-assign]
    rejected = open_cookie(app, interface, signed)
    assert rejected.backend_available is False
    assert redis_double.get(key) == b"replacement"


def test_old_payload_key_is_rewrapped_by_active_key(redis_double: RedisDouble) -> None:
    app, old_interface, _ = make_app(redis_double, payload_codec=codec("o" * 32))
    opened, signed, _ = persisted_session(app, old_interface)
    key = f"template-test:session:{opened.sid}"
    before = redis_double.get(key)

    new_interface = RedisSessionInterface(
        redis_double,
        codec=codec("n" * 32, "o" * 32),
        key_prefix="template-test:session:",
        revocation_prefix="template-test:revocation:",
        clock=Clock(),
    )
    app.session_interface = new_interface
    restored = open_cookie(app, new_interface, signed)
    assert restored.needs_rewrap is True
    response = Response()
    new_interface.save_session(app, restored, response)
    assert redis_double.get(key) != before
    assert restored.needs_rewrap is False


def test_idle_and_absolute_expiration_delete_server_state(redis_double: RedisDouble) -> None:
    for idle, absolute, advance in ((10, 100, 16), (100, 20, 26)):
        clock = Clock()
        app, interface, _ = make_app(
            redis_double,
            clock=clock,
            payload_codec=codec(idle=idle, absolute=absolute, renewal=min(5, absolute - 1)),
        )
        opened, signed, _ = persisted_session(app, interface, value=f"{idle}-{absolute}")
        key = f"template-test:session:{opened.sid}"
        clock.advance(advance)
        expired = open_cookie(app, interface, signed)
        assert expired.discard_cookie is True
        assert redis_double.get(key) is None


def test_clock_skew_is_bounded_and_invalid_clock_is_rejected(redis_double: RedisDouble) -> None:
    clock = Clock()
    app, interface, _ = make_app(
        redis_double,
        clock=clock,
        payload_codec=codec(idle=10, absolute=100, renewal=30),
    )
    _, signed, _ = persisted_session(app, interface)
    clock.advance(14)
    assert open_cookie(app, interface, signed).new is False
    clock.advance(2)
    assert open_cookie(app, interface, signed).new is True

    clock.value = float("nan")
    with app.test_request_context("/"), pytest.raises(SessionBackendError, match="clock"):
        interface.open_session(app, request)


def test_activity_refresh_is_throttled(redis_double: RedisDouble) -> None:
    clock = Clock()
    app, interface, _ = make_app(redis_double, clock=clock)
    opened, signed, _ = persisted_session(app, interface)
    key = f"template-test:session:{opened.sid}"
    before = redis_double.get(key)

    clock.advance(10)
    restored = open_cookie(app, interface, signed)
    assert restored.activity_due is False
    restored.get("value")
    interface.save_session(app, restored, Response())
    assert redis_double.get(key) == before

    clock.advance(50)
    due = open_cookie(app, interface, signed)
    assert due.activity_due is True
    due.get("value")
    interface.save_session(app, due, Response())
    assert redis_double.get(key) != before


def test_periodic_sid_rotation_is_atomic_and_emits_new_cookie(redis_double: RedisDouble) -> None:
    clock = Clock()
    app, interface, _ = make_app(redis_double, clock=clock)
    opened, signed, _ = persisted_session(app, interface)
    old_sid = opened.sid
    clock.advance(31)

    loaded = open_cookie(app, interface, signed)
    assert loaded.rotate_required is True
    response = Response()
    interface.save_session(app, loaded, response)
    assert loaded.sid != old_sid
    assert redis_double.get(f"template-test:session:{old_sid}") is None
    assert redis_double.get(f"template-test:session:{loaded.sid}") is not None
    assert "Set-Cookie" in response.headers


def test_stale_request_cannot_resurrect_rotated_sid(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    opened, signed, _ = persisted_session(app, interface)
    old_sid = opened.sid
    first = open_cookie(app, interface, signed)
    stale = open_cookie(app, interface, signed)

    interface.regenerate(app, first)
    stale["value"] = "stale"
    response = Response("must-not-leak")
    interface.save_session(app, stale, response)
    assert response.status_code == 503
    assert redis_double.get(f"template-test:session:{old_sid}") is None


def test_explicit_regeneration_preserves_data_and_resets_lifetime(redis_double: RedisDouble) -> None:
    clock = Clock()
    app, interface, _ = make_app(redis_double, clock=clock)
    opened, signed, _ = persisted_session(app, interface)
    loaded = open_cookie(app, interface, signed)
    previous_issued_at = loaded.metadata.issued_at if loaded.metadata else 0
    clock.advance(20)
    interface.regenerate(app, loaded)
    assert loaded["value"] == "stored"
    assert loaded.metadata is not None
    assert loaded.metadata.issued_at > previous_issued_at
    assert loaded.modified is True


def test_session_and_identity_revocation(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    opened, signed, _ = persisted_session(app, interface)
    assert interface.revoke_session(opened.sid) is True
    assert open_cookie(app, interface, signed).new is True

    loaded, signed, _ = persisted_session(app, interface, value="authenticated")
    interface.bind_identity(app, loaded, tenant_id="tenant", object_id="user")
    interface.save_session(app, loaded, Response())
    assert interface.revoke_identity("tenant", "user") == 1
    revoked = open_cookie(app, interface, signed)
    assert revoked.discard_cookie is True


def test_revocation_backend_failure_is_not_treated_as_anonymous(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    loaded, signed, _ = persisted_session(app, interface)
    interface.bind_identity(app, loaded, tenant_id="tenant", object_id="user")
    interface.save_session(app, loaded, Response())
    redis_double.fail = "get"
    failed = open_cookie(app, interface, signed)
    assert failed.backend_available is False
    assert failed.discard_cookie is False


def test_schema_size_and_serialization_fail_closed(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    with app.test_request_context("/"):
        invalid = interface.open_session(app, request)
    invalid["unexpected"] = "x"
    response = Response("must-not-leak", status=302, headers={"Location": "/private"})
    interface.save_session(app, invalid, response)
    assert response.status_code == 500
    assert response.text == "Internal Server Error\n"
    assert "Location" not in response.headers

    with app.test_request_context("/"):
        oversized = interface.open_session(app, request)
    oversized["value"] = "x" * (65 * 1024)
    response = Response()
    interface.save_session(app, oversized, response)
    assert response.status_code == 500


def test_backend_failures_replace_success_and_preserve_cookie_on_load(
    redis_double: RedisDouble,
) -> None:
    app, interface, _ = make_app(redis_double)
    _, signed, _ = persisted_session(app, interface)
    redis_double.fail = "get"
    unavailable = open_cookie(app, interface, signed)
    assert unavailable.backend_available is False
    response = Response()
    interface.save_session(app, unavailable, response)
    assert "Set-Cookie" not in response.headers

    redis_double.fail = None
    with app.test_request_context("/"):
        failing = interface.open_session(app, request)
    failing["value"] = "x"
    redis_double.fail = "set"
    response = Response("must-not-leak", status=302, headers={"Location": "/profile"})
    interface.save_session(app, failing, response)
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert "Location" not in response.headers


def test_invalid_types_prefixes_and_revoke_arguments(redis_double: RedisDouble) -> None:
    with pytest.raises(TypeError, match="RedisClient"):
        RedisSessionInterface(object())  # type: ignore[arg-type]
    for prefix in ("invalid", "bad space:", "x" * 129 + ":"):
        with pytest.raises(ValueError, match="key_prefix"):
            RedisSessionInterface(redis_double, key_prefix=prefix)
    with pytest.raises(ValueError, match="different"):
        RedisSessionInterface(
            redis_double,
            key_prefix="same:",
            revocation_prefix="same:",
        )
    app, interface, _ = make_app(redis_double)
    with pytest.raises(TypeError, match="RedisSession"):
        interface.save_session(app, object(), Response())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="RedisSession"):
        interface.regenerate(app, object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="sid"):
        interface.revoke_session("short")


def test_delete_and_atomic_rotation_failures(redis_double: RedisDouble) -> None:
    app, interface, _ = make_app(redis_double)
    opened, signed, _ = persisted_session(app, interface)
    loaded = open_cookie(app, interface, signed)
    redis_double.fail = "eval"
    with pytest.raises(SessionBackendError, match="rotation"):
        interface.regenerate(app, loaded)

    redis_double.fail = None
    loaded = open_cookie(app, interface, signed)
    loaded.clear()
    redis_double.fail = "delete"
    response = Response("logout", status=302, headers={"Location": "/logged-out"})
    interface.save_session(app, loaded, response)
    assert response.status_code == 503
    assert "Location" not in response.headers
