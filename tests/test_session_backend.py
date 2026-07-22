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


def make_app(
    redis: RedisDouble, *, secret: str | None = "s" * 32
) -> tuple[Flask, RedisSessionInterface]:
    app = Flask("session-test")
    app.secret_key = secret
    app.config.from_mapping(
        SESSION_COOKIE_NAME="session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_REFRESH_EACH_REQUEST=False,
    )
    app.permanent_session_lifetime = timedelta(seconds=60)
    interface = RedisSessionInterface(redis)
    app.session_interface = interface
    return app, interface


def cookie_value(response: Response) -> str:
    header = response.headers["Set-Cookie"]
    return header.split(";", 1)[0].split("=", 1)[1]


def test_rejects_invalid_client() -> None:
    with pytest.raises(TypeError, match="RedisClient"):
        RedisSessionInterface(object())  # type: ignore[arg-type]


def test_new_save_load_and_no_refresh(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double)
    with app.test_request_context("/"):
        opened = interface.open_session(app, request)
    assert opened.new is True
    opened["value"] = "stored"
    assert opened.permanent is False
    response = Response()
    interface.save_session(app, opened, response)
    assert opened.permanent is True
    assert opened.new is False
    assert opened.discard_cookie is False
    signed = cookie_value(response)

    with app.test_request_context("/", headers={"Cookie": f"session={signed}"}):
        restored = interface.open_session(app, request)
    assert restored.new is False
    assert restored["value"] == "stored"
    assert restored.sid == opened.sid

    untouched = Response()
    interface.save_session(app, restored, untouched)
    assert "Set-Cookie" not in untouched.headers


def test_session_reads_mark_cookie_as_accessed(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double)

    by_index = RedisSession({"value": "x"}, sid=interface._new_sid(), new=False)
    assert by_index.accessed is False
    assert by_index["value"] == "x"
    assert by_index.accessed is True

    by_get = RedisSession({"value": "x"}, sid=interface._new_sid(), new=False)
    assert by_get.get("value") == "x"
    assert by_get.accessed is True

    by_default = RedisSession(sid=interface._new_sid(), new=True)
    assert by_default.setdefault("value", "x") == "x"
    assert by_default.accessed is True
    response = Response()
    interface.save_session(app, by_default, response)
    assert response.headers["Vary"] == "Cookie"


def test_missing_expired_corrupt_and_non_mapping_payloads(
    redis_double: RedisDouble,
) -> None:
    app, interface = make_app(redis_double)
    sid = interface._new_sid()
    signed = interface._sign_sid(app, sid)

    with app.test_request_context("/", headers={"Cookie": f"session={signed}"}):
        missing = interface.open_session(app, request)
    assert missing.new is True
    assert missing.sid != sid
    assert missing.discard_cookie is True

    redis_double.set(f"msentra-template:session:{sid}", b"not-json")
    with app.test_request_context("/", headers={"Cookie": f"session={signed}"}):
        corrupt = interface.open_session(app, request)
    assert corrupt.new is True
    assert corrupt.sid != sid
    assert corrupt.discard_cookie is True

    sid2 = interface._new_sid()
    signed2 = interface._sign_sid(app, sid2)
    payload = interface.serializer.dumps(["not", "mapping"]).encode()
    redis_double.set(f"msentra-template:session:{sid2}", payload)
    with app.test_request_context("/", headers={"Cookie": f"session={signed2}"}):
        non_mapping = interface.open_session(app, request)
    assert non_mapping.new is True
    assert non_mapping.sid != sid2


def test_load_failure_and_invalid_signature_create_fresh_session(
    redis_double: RedisDouble,
) -> None:
    app, interface = make_app(redis_double)
    redis_double.fail = "get"
    signed = interface._sign_sid(app, interface._new_sid())
    with app.test_request_context("/", headers={"Cookie": f"session={signed}"}):
        failed = interface.open_session(app, request)
    assert failed.new is True
    assert failed.backend_available is False
    assert failed.discard_cookie is False
    unavailable_response = Response()
    interface.save_session(app, failed, unavailable_response)
    assert "Set-Cookie" not in unavailable_response.headers

    redis_double.fail = None
    with app.test_request_context("/", headers={"Cookie": "session=tampered"}):
        invalid = interface.open_session(app, request)
    assert invalid.new is True
    assert invalid.backend_available is True
    assert invalid.discard_cookie is True
    response = Response()
    interface.save_session(app, invalid, response)
    assert "Max-Age=0" in response.headers["Set-Cookie"]


def test_stale_cookie_is_deleted_without_session_refresh(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double)
    app.config["SESSION_PERMANENT"] = True
    sid = interface._new_sid()
    signed = interface._sign_sid(app, sid)

    with app.test_request_context("/", headers={"Cookie": f"session={signed}"}):
        fresh = interface.open_session(app, request)
    assert fresh.permanent is False
    assert fresh.discard_cookie is True

    response = Response()
    interface.save_session(app, fresh, response)
    assert "Max-Age=0" in response.headers["Set-Cookie"]
    assert redis_double.get(f"msentra-template:session:{fresh.sid}") is None


def test_empty_modified_session_deletes_backend_and_cookie(
    redis_double: RedisDouble,
) -> None:
    app, interface = make_app(redis_double)
    session = RedisSession({"value": "x"}, sid=interface._new_sid(), new=False)
    session.clear()
    response = Response()
    interface.save_session(app, session, response)
    assert "Max-Age=0" in response.headers["Set-Cookie"]


def test_empty_unmodified_session_does_nothing(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double)
    session = RedisSession(sid=interface._new_sid(), new=True)
    response = Response()
    interface.save_session(app, session, response)
    assert "Set-Cookie" not in response.headers
    assert redis_double.get(f"msentra-template:session:{session.sid}") is None


def test_loaded_permanent_only_session_is_removed(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double)
    session = RedisSession({"_permanent": True}, sid=interface._new_sid(), new=False)
    redis_double.set(f"msentra-template:session:{session.sid}", b"obsolete")
    response = Response()

    interface.save_session(app, session, response)

    assert "Max-Age=0" in response.headers["Set-Cookie"]
    assert redis_double.get(f"msentra-template:session:{session.sid}") is None


def test_rejects_wrong_session_type_and_missing_secret(
    redis_double: RedisDouble,
) -> None:
    app, interface = make_app(redis_double)
    with pytest.raises(TypeError, match="RedisSession"):
        interface.save_session(app, object(), Response())  # type: ignore[arg-type]

    no_secret, no_secret_interface = make_app(redis_double, secret=None)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        no_secret_interface._sign_sid(no_secret, "a" * 32)


def test_invalid_sid_shape_is_rejected_even_with_valid_signature(
    redis_double: RedisDouble,
) -> None:
    app, interface = make_app(redis_double)
    signed = interface._signer(app).sign(b"short").decode()
    assert interface._unsign_sid(app, signed) is None


def test_prefix_payload_limits_and_backend_save_failures(
    redis_double: RedisDouble,
) -> None:
    with pytest.raises(ValueError, match="key_prefix"):
        RedisSessionInterface(redis_double, key_prefix="invalid")

    app, interface = make_app(redis_double)
    sid = interface._new_sid()
    signed = interface._sign_sid(app, sid)
    redis_double.forced_get = b"x" * (64 * 1024 + 1)
    with app.test_request_context("/", headers={"Cookie": f"session={signed}"}):
        oversized = interface.open_session(app, request)
    assert oversized.sid != sid
    redis_double.forced_get = None

    huge = RedisSession({"value": "x" * (64 * 1024)}, sid=interface._new_sid(), new=True)
    huge.modified = True
    with pytest.raises(SessionBackendError, match="too large"):
        interface.save_session(app, huge, Response())

    failing = RedisSession({"value": "x"}, sid=interface._new_sid(), new=True)
    failing.modified = True
    redis_double.fail = "set"
    with pytest.raises(SessionBackendError, match="save failed"):
        interface.save_session(app, failing, Response())
    redis_double.fail = None
    redis_double.return_false = True
    with pytest.raises(SessionBackendError, match="save failed"):
        interface.save_session(app, failing, Response())


def test_rotation_prevents_stale_request_from_resurrecting_old_sid(
    redis_double: RedisDouble,
) -> None:
    app, interface = make_app(redis_double)
    active = RedisSession({"value": "current"}, sid=interface._new_sid(), new=True)
    active.modified = True
    interface.save_session(app, active, Response())
    old_sid = active.sid

    stale = RedisSession({"value": "stale"}, sid=old_sid, new=False)
    stale.modified = True
    interface.regenerate(app, active)

    with pytest.raises(SessionBackendError, match="save failed"):
        interface.save_session(app, stale, Response())
    assert redis_double.get(f"msentra-template:session:{old_sid}") is None

    interface.save_session(app, active, Response())
    assert active.new is False
    assert redis_double.get(f"msentra-template:session:{active.sid}") is not None


def test_delete_and_regeneration_failure_paths(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double)
    empty = RedisSession({"value": "x"}, sid=interface._new_sid(), new=False)
    empty.clear()
    redis_double.fail = "delete"
    response = Response()
    interface.save_session(app, empty, response)
    assert "Max-Age=0" in response.headers["Set-Cookie"]

    with pytest.raises(TypeError, match="RedisSession"):
        interface.regenerate(app, object())  # type: ignore[arg-type]
    session = RedisSession({"value": "x"}, sid=interface._new_sid(), new=False)
    with pytest.raises(SessionBackendError, match="rotation"):
        interface.regenerate(app, session)

    redis_double.fail = None
    previous = session.sid
    interface.regenerate(app, session)
    assert session.sid != previous
    assert session.new is True
    assert session.modified is True


def test_non_permanent_fresh_session(redis_double: RedisDouble) -> None:
    app, interface = make_app(redis_double)
    app.config["SESSION_PERMANENT"] = False
    fresh = interface._fresh_session(app)
    assert fresh.permanent is False
    assert fresh.backend_available is True

    fresh["value"] = "stored"
    response = Response()
    interface.save_session(app, fresh, response)
    assert fresh.permanent is False
    assert "Set-Cookie" in response.headers
