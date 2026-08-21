from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from hashlib import sha256
from secrets import token_urlsafe
from time import time
from typing import Any, cast

from flask import Flask, Request, Response, request, session
from flask.sessions import SessionInterface, SessionMixin
from itsdangerous import BadSignature, Signer
from werkzeug.datastructures import CallbackDict

from .session_envelope import (
    SessionEnvelopeCodec,
    SessionEnvelopeError,
    SessionEnvelopeExpired,
    SessionMetadata,
    subject_fingerprint,
)
from .storage import RedisClient

_SID_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
_PREFIX_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}:$")
_STATELESS_PATHS = frozenset({"/health/live", "/health/ready"})
_MAX_SIGNING_KEYS = 5
_COMPARE_DELETE_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then return 1 end
if current ~= ARGV[1] then return 0 end
redis.call('DEL', KEYS[1])
return 1
""".strip()
_ATOMIC_ROTATE_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then return 0 end
if current ~= ARGV[1] then return -2 end
if redis.call('EXISTS', KEYS[2]) == 1 then return -1 end
local written = redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3], 'NX')
if not written then return -1 end
redis.call('DEL', KEYS[1])
return 1
""".strip()
_INCREMENT_REVISION_SCRIPT = """
local raw = redis.call('GET', KEYS[1])
local current = 0
if raw then current = tonumber(raw); if not current or current < 0 then return -1 end end
if current >= 9223372036854775806 then return -1 end
local updated = current + 1
redis.call('SET', KEYS[1], tostring(updated))
return updated
""".strip()


class SessionBackendError(RuntimeError):
    pass


class SessionBackendUnavailable(SessionBackendError):
    pass


class RedisSession(CallbackDict[str, object], SessionMixin):
    def __init__(
        self,
        initial: Mapping[str, object] | None = None,
        *,
        sid: str,
        new: bool,
        discard_cookie: bool = False,
        backend_available: bool = True,
        stateless: bool = False,
        resign_cookie: bool = False,
        metadata: SessionMetadata | None = None,
        loaded_envelope: bytes | None = None,
        needs_rewrap: bool = False,
        rotate_required: bool = False,
        activity_due: bool = False,
    ) -> None:
        def on_update(_: object) -> None:
            self.modified = True

        super().__init__(initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        self.accessed = False
        self.discard_cookie = discard_cookie
        self.backend_available = backend_available
        self.stateless = stateless
        self.resign_cookie = resign_cookie
        self.metadata = metadata
        self.loaded_envelope = loaded_envelope
        self.needs_rewrap = needs_rewrap
        self.rotate_required = rotate_required
        self.activity_due = activity_due

    def __getitem__(self, key: str) -> Any:
        self.accessed = True
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        self.accessed = True
        return super().get(key, default)


class RedisSessionInterface(SessionInterface):
    session_class = RedisSession

    def __init__(
        self,
        client: RedisClient,
        *,
        codec: SessionEnvelopeCodec,
        key_prefix: str,
        revocation_prefix: str,
        clock: Callable[[], float] = time,
    ) -> None:
        if not isinstance(client, RedisClient):
            raise TypeError("client must implement RedisClient")
        for name, prefix in (("key_prefix", key_prefix), ("revocation_prefix", revocation_prefix)):
            if not isinstance(prefix, str) or not _PREFIX_RE.fullmatch(prefix):
                raise ValueError(f"{name} must be a safe prefix ending with ':'")
        if key_prefix == revocation_prefix:
            raise ValueError("session and revocation prefixes must be different")
        self._client = client
        self._codec = codec
        self._key_prefix = key_prefix
        self._revocation_prefix = revocation_prefix
        self._clock = clock

    def open_session(self, app: Flask, request: Request) -> RedisSession:
        if self._is_stateless_request(app, request):
            return self._fresh(stateless=True)
        cookie = request.cookies.get(self.get_cookie_name(app))
        resolved = self._unsign_sid(app, cookie) if cookie else None
        if resolved is None:
            return self._fresh(discard_cookie=cookie is not None)
        sid, resign_cookie = resolved
        key = self._key(sid)
        try:
            raw = self._client.get(key)
        except Exception:
            app.logger.error("server-side session load failed")
            return self._fresh(backend_available=False)
        if raw is None:
            return self._fresh(discard_cookie=True)
        if not isinstance(raw, (bytes, bytearray)):
            app.logger.error("server-side session backend returned invalid payload")
            return self._fresh(backend_available=False)
        payload = bytes(raw)
        now = self._now()
        try:
            decoded = self._codec.open(sid, payload, now=now)
        except (SessionEnvelopeExpired, SessionEnvelopeError):
            app.logger.warning("server-side session envelope rejected")
            return self._invalidated(app, key, payload)
        if decoded.metadata.subject_id is not None:
            try:
                revision = self._load_subject_revision(decoded.metadata.subject_id)
            except SessionBackendError:
                app.logger.error("server-side revocation check failed")
                return self._fresh(backend_available=False)
            if revision != decoded.metadata.subject_revision:
                return self._invalidated(app, key, payload)
        interval = max(1, int(app.config.get("SESSION_ACTIVITY_UPDATE_SECONDS", 60)))
        return self.session_class(
            decoded.data,
            sid=sid,
            new=False,
            resign_cookie=resign_cookie,
            metadata=decoded.metadata,
            loaded_envelope=payload,
            needs_rewrap=decoded.needs_rewrap,
            rotate_required=decoded.rotation_due,
            activity_due=now - decoded.metadata.last_seen_at >= interval,
        )

    def save_session(self, app: Flask, session: SessionMixin, response: Response) -> None:
        if not isinstance(session, RedisSession):
            raise TypeError("session must be RedisSession")
        if session.stateless:
            return
        if session.accessed:
            response.vary.add("Cookie")
        if not session.backend_available:
            return
        name = self.get_cookie_name(app)
        key = self._key(session.sid)
        if not self._has_data(session):
            if session.discard_cookie:
                self._delete_cookie(app, response, name)
            elif not session.new:
                try:
                    self._client.delete(key)
                except Exception as exc:
                    app.logger.error(
                        "server-side session deletion failed",
                        extra={"error_type": type(exc).__name__},
                    )
                    self._fail_response(response, 503, retry_after=5)
                    return
                self._delete_cookie(app, response, name)
            return
        if app.config.get("SESSION_PERMANENT", False) and not session.permanent:
            session.permanent = True
        now = self._now()
        if session.metadata is None:
            session.metadata = self._codec.new_metadata(now)
        try:
            self._codec.ensure_active(session.metadata, now)
        except SessionEnvelopeExpired:
            self._delete_cookie(app, response, name)
            return
        except SessionEnvelopeError:
            self._fail_response(response, 500)
            return
        write_required = (
            session.new
            or session.modified
            or session.needs_rewrap
            or session.rotate_required
            or (session.activity_due and session.accessed)
        )
        sid_rotated = False
        if session.rotate_required and not session.new:
            try:
                self._rotate_loaded(session, reset_lifetime=False)
            except SessionBackendError as exc:
                app.logger.warning(
                    "server-side periodic session rotation failed",
                    extra={"error_type": type(exc).__name__},
                )
                self._fail_response(response, 503, retry_after=5)
                return
            sid_rotated = True
            write_required = False
        elif write_required:
            if session.accessed or session.modified or session.needs_rewrap:
                session.metadata = self._codec.refresh_metadata(session.metadata, now)
            try:
                payload = self._codec.seal(session.sid, dict(session), session.metadata)
                ttl = self._ttl(session.metadata, now)
                result = self._client.set(key, payload, ex=ttl, nx=session.new, xx=not session.new)
            except SessionEnvelopeError:
                self._fail_response(response, 500)
                return
            except Exception as exc:
                app.logger.error(
                    "server-side session save failed", extra={"error_type": type(exc).__name__}
                )
                self._fail_response(response, 503, retry_after=5)
                return
            if not result:
                self._fail_response(response, 503, retry_after=5)
                return
            session.loaded_envelope = payload
            session.new = False
            session.needs_rewrap = False
            session.activity_due = False
        if not (
            self.should_set_cookie(app, session)
            or session.resign_cookie
            or sid_rotated
            or write_required
        ):
            if session.discard_cookie:
                self._delete_cookie(app, response, name)
            return
        session.discard_cookie = False
        session.resign_cookie = False
        session.rotate_required = False
        response.set_cookie(
            name,
            self._sign_sid(app, session.sid),
            expires=self._cookie_expiration(session.metadata),
            httponly=self.get_cookie_httponly(app),
            domain=self.get_cookie_domain(app),
            path=self.get_cookie_path(app),
            secure=self.get_cookie_secure(app),
            partitioned=self.get_cookie_partitioned(app),
            samesite=self.get_cookie_samesite(app),
        )

    def regenerate(self, app: Flask, session: SessionMixin, *, reset_lifetime: bool = True) -> None:
        if not isinstance(session, RedisSession):
            raise TypeError("session must be RedisSession")
        if session.stateless:
            raise SessionBackendError("stateless sessions cannot be rotated")
        if session.new:
            session.sid = self._new_sid()
            session.metadata = self._codec.new_metadata(self._now())
            session.modified = True
            return
        self._rotate_loaded(session, reset_lifetime=reset_lifetime)
        session.modified = True

    def bind_identity(
        self, app: Flask, session: SessionMixin, *, tenant_id: str, object_id: str
    ) -> str:
        del app
        if not isinstance(session, RedisSession):
            raise TypeError("session must be RedisSession")
        subject_id = subject_fingerprint(tenant_id, object_id)
        revision = self._load_subject_revision(subject_id)
        metadata = session.metadata or self._codec.new_metadata(self._now())
        session.metadata = self._codec.refresh_metadata(
            metadata, self._now(), subject_id=subject_id, subject_revision=revision
        )
        session.modified = True
        return subject_id

    def revoke_identity(self, tenant_id: str, object_id: str) -> int:
        subject_id = subject_fingerprint(tenant_id, object_id)
        try:
            result = self._client.eval(
                _INCREMENT_REVISION_SCRIPT, 1, self._subject_revision_key(subject_id)
            )
        except Exception as exc:
            raise SessionBackendError("subject session revocation failed") from exc
        if isinstance(result, bool) or not isinstance(result, int) or result <= 0:
            raise SessionBackendError("subject session revocation failed")
        return result

    def _rotate_loaded(self, session: RedisSession, *, reset_lifetime: bool) -> None:
        if session.loaded_envelope is None or session.metadata is None:
            raise SessionBackendError("rotation requires loaded session state")
        now = self._now()
        new_sid = self._new_sid()
        metadata = self._codec.refresh_metadata(
            session.metadata, now, rotate_sid=True, reset_lifetime=reset_lifetime
        )
        try:
            payload = self._codec.seal(new_sid, dict(session), metadata)
            ttl = self._ttl(metadata, now)
            result = self._client.eval(
                _ATOMIC_ROTATE_SCRIPT,
                2,
                self._key(session.sid),
                self._key(new_sid),
                session.loaded_envelope,
                payload,
                str(ttl),
            )
        except Exception as exc:
            raise SessionBackendError("server-side session rotation failed") from exc
        if result != 1:
            raise SessionBackendError("server-side session rotation was rejected")
        session.sid = new_sid
        session.metadata = metadata
        session.loaded_envelope = payload
        session.new = False
        session.needs_rewrap = False
        session.rotate_required = False
        session.activity_due = False

    def _invalidated(self, app: Flask, key: str, payload: bytes) -> RedisSession:
        try:
            result = self._client.eval(_COMPARE_DELETE_SCRIPT, 1, key, payload)
        except Exception:
            app.logger.error("invalid session cleanup failed")
            return self._fresh(backend_available=False)
        if result != 1:
            return self._fresh(backend_available=False)
        return self._fresh(discard_cookie=True)

    def _load_subject_revision(self, subject_id: str) -> int:
        try:
            raw = self._client.get(self._subject_revision_key(subject_id))
        except Exception as exc:
            raise SessionBackendError("subject revision load failed") from exc
        if raw is None:
            return 0
        if not isinstance(raw, (bytes, bytearray)):
            raise SessionBackendError("subject revision is invalid")
        try:
            value = int(bytes(raw).decode("ascii"))
        except (UnicodeError, ValueError) as exc:
            raise SessionBackendError("subject revision is invalid") from exc
        if not 0 <= value <= 2**63 - 1:
            raise SessionBackendError("subject revision is invalid")
        return value

    def _fresh(
        self,
        *,
        discard_cookie: bool = False,
        backend_available: bool = True,
        stateless: bool = False,
    ) -> RedisSession:
        now = self._now()
        return self.session_class(
            {},
            sid=self._new_sid(),
            new=True,
            discard_cookie=discard_cookie,
            backend_available=backend_available,
            stateless=stateless,
            metadata=self._codec.new_metadata(now),
        )

    @staticmethod
    def _is_stateless_request(app: Flask, req: Request) -> bool:
        if req.path in _STATELESS_PATHS:
            return True
        static_path = (app.static_url_path or "").rstrip("/")
        return bool(
            static_path
            and static_path != "/"
            and (req.path == static_path or req.path.startswith(f"{static_path}/"))
        )

    @staticmethod
    def _has_data(session: RedisSession) -> bool:
        return any(key != "_permanent" for key in session)

    def _ttl(self, metadata: SessionMetadata, now: int) -> int:
        self._codec.ensure_active(metadata, now)
        remaining = metadata.issued_at + self._codec.absolute_timeout_seconds - now
        if remaining <= 0:
            raise SessionEnvelopeExpired("session absolute timeout was exceeded")
        return min(self._codec.idle_timeout_seconds, remaining)

    def _cookie_expiration(self, metadata: SessionMetadata | None) -> datetime | None:
        if metadata is None:
            return None
        return datetime.fromtimestamp(
            metadata.issued_at + self._codec.absolute_timeout_seconds, tz=UTC
        )

    def _key(self, sid: str) -> str:
        return f"{self._key_prefix}{sid}"

    def _subject_revision_key(self, subject_id: str) -> str:
        return f"{self._revocation_prefix}subject:{subject_id}"

    @staticmethod
    def _new_sid() -> str:
        return token_urlsafe(32)

    def _now(self) -> int:
        value = self._clock()
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise SessionBackendError("session clock returned an invalid value")
        return int(value)

    def _signers(self, app: Flask) -> tuple[Signer, ...]:
        configured = app.config.get("SESSION_SIGNING_KEYS")
        if isinstance(configured, (str, bytes)):
            keys: tuple[str | bytes, ...] = (configured,)
        elif isinstance(configured, Sequence) and not isinstance(configured, (bytes, bytearray)):
            raw_keys = tuple(configured)
            if any(not isinstance(key, (str, bytes)) for key in raw_keys):
                raise RuntimeError("SESSION_SIGNING_KEYS is invalid")
            keys = cast(tuple[str | bytes, ...], raw_keys)
        else:
            keys = (app.secret_key,) if app.secret_key else ()
        if not keys or len(keys) > _MAX_SIGNING_KEYS or any(not key for key in keys):
            raise RuntimeError("SESSION_SIGNING_KEYS is invalid")
        return tuple(Signer(key, salt="server-side-session", digest_method=sha256) for key in keys)

    def _sign_sid(self, app: Flask, sid: str) -> str:
        return self._signers(app)[0].sign(sid.encode()).decode()

    def _unsign_sid(self, app: Flask, signed_sid: str) -> tuple[str, bool] | None:
        for index, signer in enumerate(self._signers(app)):
            try:
                sid = signer.unsign(signed_sid.encode()).decode()
            except (BadSignature, UnicodeError):
                continue
            return (sid, index > 0) if _SID_RE.fullmatch(sid) else None
        return None

    def _delete_cookie(self, app: Flask, response: Response, name: str) -> None:
        response.delete_cookie(
            name,
            domain=self.get_cookie_domain(app),
            path=self.get_cookie_path(app),
            secure=self.get_cookie_secure(app),
            httponly=self.get_cookie_httponly(app),
            samesite=self.get_cookie_samesite(app),
            partitioned=self.get_cookie_partitioned(app),
        )

    @staticmethod
    def _fail_response(
        response: Response, status_code: int, *, retry_after: int | None = None
    ) -> None:
        response.direct_passthrough = False
        response.status_code = status_code
        response.set_data(
            "Service Unavailable\n" if status_code == 503 else "Internal Server Error\n"
        )
        response.content_type = "text/plain; charset=utf-8"
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers.pop("Set-Cookie", None)
        if retry_after is not None:
            response.headers["Retry-After"] = str(retry_after)


def register_session_backend_guard(app: Flask) -> None:
    @app.before_request
    def ensure_session_backend_available() -> None:
        if (
            request.endpoint is None
            or request.path in _STATELESS_PATHS
            or request.endpoint == "static"
        ):
            return
        current = session
        if isinstance(current, RedisSession) and not current.backend_available:
            raise SessionBackendUnavailable("server-side session backend is unavailable")


__all__ = [
    "RedisSession",
    "RedisSessionInterface",
    "SessionBackendError",
    "SessionBackendUnavailable",
    "register_session_backend_guard",
]
