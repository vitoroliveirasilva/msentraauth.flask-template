from __future__ import annotations

from datetime import timedelta

import pytest
from flask import Flask, Response, request
from itsdangerous import Signer

from conftest import RedisDouble, cryptographic_key
from msentraauth_template.session_backend import RedisSessionInterface


def make_app(redis: RedisDouble, keys: tuple[str, ...]) -> tuple[Flask, RedisSessionInterface]:
    app = Flask("session-key-ring-test")
    app.secret_key = cryptographic_key(1)
    app.config.from_mapping(
        SESSION_SIGNING_KEYS=keys,
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_PERMANENT=True,
        SESSION_REFRESH_EACH_REQUEST=False,
    )
    app.permanent_session_lifetime = timedelta(seconds=60)
    interface = RedisSessionInterface(redis)
    app.session_interface = interface
    return app, interface


def cookie_value(response: Response) -> str:
    return response.headers["Set-Cookie"].split(";", 1)[0].split("=", 1)[1]


def test_active_key_signs_and_previous_key_is_accepted_then_replaced(
    redis_double: RedisDouble,
) -> None:
    active = cryptographic_key(10)
    previous = cryptographic_key(20)
    app, interface = make_app(redis_double, (active, previous))
    sid = interface._new_sid()
    payload = interface.serializer.dumps({"value": "stored", "_permanent": True}).encode()
    redis_double.set(f"msentra-template:session:{sid}", payload, ex=60)

    legacy = Signer(
        previous,
        salt="msentra-template-session",
        digest_method=interface._signer(app).digest_method,
    ).sign(sid.encode()).decode()
    with app.test_request_context("/", headers={"Cookie": f"session={legacy}"}):
        restored = interface.open_session(app, request)

    assert restored.sid == sid
    assert restored.resign_cookie is True
    assert restored["value"] == "stored"

    response = Response()
    interface.save_session(app, restored, response)
    replacement = cookie_value(response)
    assert replacement != legacy
    assert interface._unsign_sid(app, replacement) == (sid, False)
    assert restored.resign_cookie is False


def test_removed_or_unknown_key_is_rejected(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double, (cryptographic_key(30),))
    sid = interface._new_sid()
    removed = Signer(
        cryptographic_key(40),
        salt="msentra-template-session",
        digest_method=interface._signer(app).digest_method,
    ).sign(sid.encode()).decode()
    with app.test_request_context("/", headers={"Cookie": f"session={removed}"}):
        opened = interface.open_session(app, request)
    assert opened.new is True
    assert opened.discard_cookie is True


def test_signing_configuration_rejects_empty_invalid_and_excessive_rings(
    redis_double: RedisDouble,
) -> None:
    app, interface = make_app(redis_double, ())
    app.secret_key = None
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        interface._sign_sid(app, interface._new_sid())

    app.config["SESSION_SIGNING_KEYS"] = [cryptographic_key(index) for index in range(6)]
    with pytest.raises(RuntimeError, match="five"):
        interface._sign_sid(app, interface._new_sid())

    app.config["SESSION_SIGNING_KEYS"] = [""]
    with pytest.raises(RuntimeError, match="invalid"):
        interface._sign_sid(app, interface._new_sid())


def test_string_configuration_remains_compatible(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double, (cryptographic_key(50),))
    app.config["SESSION_SIGNING_KEYS"] = cryptographic_key(50)
    sid = interface._new_sid()
    signed = interface._sign_sid(app, sid)
    assert interface._unsign_sid(app, signed) == (sid, False)
