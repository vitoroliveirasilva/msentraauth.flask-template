from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from hashlib import sha256
from secrets import token_urlsafe
from time import time
from typing import Any

from flask import Flask, Request, Response, request, session
from flask.json.tag import TaggedJSONSerializer
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
_MAX_SIGNING_KEYS = 5
_STATELESS_PATHS = frozenset({"/health/live", "/health/ready"})
_COMPARE_DELETE_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then
  return 1
end
if current ~= ARGV[1] then
  return 0
end
redis.call('DEL', KEYS[1])
return 1
""".strip()
_ATOMIC_ROTATE_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then
  return 0
end
if current ~= ARGV[1] then
  return -2
end
if redis.call('EXISTS', KEYS[2]) == 1 then
  return -1
end
local written = redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3], 'NX')
if not written then
  return -1
end
redis.call('DEL', KEYS[1])
return 1
""".strip()
_INCREMENT_REVISION_SCRIPT = """
local raw = redis.call('GET', KEYS[1])
local current = 0
if raw then
  current = tonumber(raw)
  if not current or current < 0 then
    return -1
  end
end
if current >= 9223372036854775806 then
  return -1
end
local updated = current + 1
redis.call('SET', KEYS[1], tostring(updated))
return updated
""".strip()


class SessionBackendError(RuntimeError):
    """Gerado quando uma sessão do servidor não pode ser persistida com segurança"""


class SessionBackendUnavailable(SessionBackendError):
    """Gerado quando o backend de sessão está temporariamente indisponível"""


class RedisSession(CallbackDict[str, object], SessionMixin):
    """Sessão Flask cujo payload protegido permanece no Redis"""

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

    def setdefault(self, key: str, default: Any = None) -> Any:
        self.accessed = True
        return super().setdefault(key, default)


class RedisSessionInterface(SessionInterface):
    """Persiste envelopes AEAD e assina somente o SID opaco do navegador"""

    # Mantido apenas para compatibilidade de API interna 1.0.x. Novas gravações usam JSON estrito
    serializer = TaggedJSONSerializer()
    session_class = RedisSession

    def __init__(
        self,
        client: RedisClient,
        *,
        codec: SessionEnvelopeCodec | None = None,
        key_prefix: str = "msentra-template:session:",
        revocation_prefix: str = "msentra-template:revocation:",
        clock: Callable[[], float] = time,
    ) -> None:
        if not isinstance(client, RedisClient):
            raise TypeError("client must implement RedisClient")
        for name, prefix in (("key_prefix", key_prefix), ("revocation_prefix", revocation_prefix)):
            if not isinstance(prefix, str) or not _PREFIX_RE.fullmatch(prefix):
                raise ValueError(
                    f"{name} must be a safe non-empty prefix ending with ':'"
                )
        if key_prefix == revocation_prefix:
            raise ValueError("session and revocation prefixes must be different")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._client = client
        self._configured_codec = codec
        self._key_prefix = key_prefix
        self._revocation_prefix = revocation_prefix
        self._clock = clock

    def open_session(self, app: Flask, request: Request) -> RedisSession:
        if self._is_stateless_request(app, request):
            return self._fresh_session(app, stateless=True)

        signed_sid = request.cookies.get(self.get_cookie_name(app))
        resolved_sid = self._unsign_sid(app, signed_sid) if signed_sid else None
        if resolved_sid is None:
            return self._fresh_session(app, discard_cookie=signed_sid is not None)
        sid, resign_cookie = resolved_sid
        key = self._key(sid)
        try:
            raw_payload = self._client.get(key)
        except Exception:
            app.logger.error("server-side session load failed")
            return self._fresh_session(app, backend_available=False)
        if raw_payload is None:
            # Uma resposta concorrente com o SID antigo não pode apagar o cookie recém-rotacionado
            return self._fresh_session(app)
        if not isinstance(raw_payload, (bytes, bytearray)):
            app.logger.error("server-side session backend returned an invalid payload type")
            return self._fresh_session(app, backend_available=False)
        payload = bytes(raw_payload)
        codec = self._codec(app)
        now = self._now()
        try:
            decoded = codec.open(sid, payload, now=now)
        except SessionEnvelopeExpired:
            app.logger.info("server-side session expired")
            return self._invalidated_session(app, key, payload)
        except SessionEnvelopeError:
            app.logger.warning("server-side session envelope was rejected")
            return self._invalidated_session(app, key, payload)

        if decoded.metadata.subject_id is not None:
            try:
                current_revision = self._load_subject_revision(decoded.metadata.subject_id)
            except SessionBackendError:
                app.logger.error("server-side session revocation check failed")
                return self._fresh_session(app, backend_available=False)
            if current_revision != decoded.metadata.subject_revision:
                app.logger.info("server-side session was revoked by subject")
                return self._invalidated_session(app, key, payload)

        activity_interval = self._activity_update_seconds(app, codec)
        return self.session_class(
            decoded.data,
            sid=sid,
            new=False,
            resign_cookie=resign_cookie,
            metadata=decoded.metadata,
            loaded_envelope=payload,
            needs_rewrap=decoded.needs_rewrap,
            rotate_required=decoded.rotation_due,
            activity_due=(now - decoded.metadata.last_seen_at) >= activity_interval,
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

        cookie_name = self.get_cookie_name(app)
        key = self._key(session.sid)
        if not self._has_session_data(session):
            if session.discard_cookie:
                self._delete_cookie(app, response, cookie_name)
                return
            if not session.new:
                try:
                    self._client.delete(key)
                except Exception as exc:
                    app.logger.error(
                        "server-side session deletion failed",
                        extra={"error_type": type(exc).__name__, "status_code": 503},
                    )
                    self._replace_response_with_error(response, status_code=503, retry_after=5)
                    return
                self._delete_cookie(app, response, cookie_name)
            return

        if app.config.get("SESSION_PERMANENT", False) and not session.permanent:
            session.permanent = True

        codec = self._codec(app)
        now = self._now()
        if session.metadata is None:
            session.metadata = codec.new_metadata(now)
        try:
            codec.ensure_active(session.metadata, now)
        except SessionEnvelopeExpired:
            app.logger.info("server-side session expired before persistence")
            if not session.new and session.loaded_envelope is not None:
                invalidated = self._invalidated_session(app, key, session.loaded_envelope)
                if invalidated.backend_available:
                    self._delete_cookie(app, response, cookie_name)
                else:
                    self._replace_response_with_error(response, status_code=503, retry_after=5)
            else:
                self._delete_cookie(app, response, cookie_name)
            return
        except SessionEnvelopeError as exc:
            app.logger.error(
                "server-side session metadata was invalid",
                extra={"error_type": type(exc).__name__, "status_code": 500},
            )
            self._replace_response_with_error(response, status_code=500)
            return
        write_required = any(
            (
                session.new,
                session.modified,
                session.needs_rewrap,
                session.rotate_required,
                session.activity_due and session.accessed,
            )
        )

        if session.rotate_required and not session.new:
            try:
                self._rotate_loaded_session(app, session, reset_lifetime=False)
            except SessionBackendError as exc:
                app.logger.warning(
                    "server-side periodic session rotation failed",
                    extra={"error_type": type(exc).__name__, "status_code": 503},
                )
                self._replace_response_with_error(response, status_code=503, retry_after=5)
                return
            write_required = False
            now = self._now()
        elif write_required:
            if session.accessed or session.modified or session.needs_rewrap:
                session.metadata = codec.refresh_metadata(session.metadata, now)
            try:
                payload = codec.seal(session.sid, dict(session), session.metadata)
                ttl = self._ttl(codec, session.metadata, now)
                result = self._client.set(
                    key,
                    payload,
                    ex=ttl,
                    nx=session.new,
                    xx=not session.new,
                )
            except SessionEnvelopeError as exc:
                app.logger.error(
                    "server-side session serialization failed",
                    extra={"error_type": type(exc).__name__, "status_code": 500},
                )
                self._replace_response_with_error(response, status_code=500)
                return
            except Exception as exc:
                app.logger.error(
                    "server-side session save failed",
                    extra={"error_type": type(exc).__name__, "status_code": 503},
                )
                self._replace_response_with_error(response, status_code=503, retry_after=5)
                return
            if not result:
                app.logger.warning(
                    "server-side session conditional save was rejected",
                    extra={"status_code": 503},
                )
                self._replace_response_with_error(response, status_code=503, retry_after=5)
                return
            session.loaded_envelope = payload
            session.new = False
            session.needs_rewrap = False
            session.activity_due = False

        if not (
            self.should_set_cookie(app, session)
            or session.resign_cookie
            or session.rotate_required
            or write_required
        ):
            if session.discard_cookie:
                self._delete_cookie(app, response, cookie_name)
            return

        session.discard_cookie = False
        session.resign_cookie = False
        session.rotate_required = False
        response.set_cookie(
            cookie_name,
            self._sign_sid(app, session.sid),
            expires=self._cookie_expiration(codec, session.metadata),
            httponly=self.get_cookie_httponly(app),
            domain=self.get_cookie_domain(app),
            path=self.get_cookie_path(app),
            secure=self.get_cookie_secure(app),
            partitioned=self.get_cookie_partitioned(app),
            samesite=self.get_cookie_samesite(app),
        )

    def regenerate(
        self,
        app: Flask,
        session: SessionMixin,
        *,
        reset_lifetime: bool = True,
    ) -> None:
        """Rotaciona o SID por uma operação Redis atômica e revoga o identificador anterior"""
        if not isinstance(session, RedisSession):
            raise TypeError("session must be RedisSession")
        if session.stateless:
            raise SessionBackendError("stateless sessions cannot be rotated")
        if session.new:
            session.sid = self._new_sid()
            session.metadata = self._codec(app).new_metadata(self._now())
            session.modified = True
            session.resign_cookie = False
            return
        self._rotate_loaded_session(app, session, reset_lifetime=reset_lifetime)
        session.modified = True
        session.resign_cookie = False

    def bind_identity(
        self,
        app: Flask,
        session: SessionMixin,
        *,
        tenant_id: str,
        object_id: str,
    ) -> str:
        """Vincula revisão de revogação estável ao envelope sem persistir PII no Redis"""
        if not isinstance(session, RedisSession):
            raise TypeError("session must be RedisSession")
        subject_id = subject_fingerprint(tenant_id, object_id)
        try:
            revision = self._load_subject_revision(subject_id)
        except SessionBackendError:
            app.logger.error("server-side identity revocation state could not be loaded")
            raise
        codec = self._codec(app)
        metadata = session.metadata or codec.new_metadata(self._now())
        session.metadata = codec.refresh_metadata(
            metadata,
            self._now(),
            subject_id=subject_id,
            subject_revision=revision,
        )
        session.modified = True
        return subject_id

    def revoke_identity(self, tenant_id: str, object_id: str) -> int:
        """Invalida todas as sessões atuais da identidade na próxima leitura segura"""
        subject_id = subject_fingerprint(tenant_id, object_id)
        try:
            result = self._client.eval(
                _INCREMENT_REVISION_SCRIPT,
                1,
                self._subject_revision_key(subject_id),
            )
        except Exception as exc:
            raise SessionBackendError("subject session revocation failed") from exc
        if isinstance(result, bool) or not isinstance(result, int) or result <= 0:
            raise SessionBackendError("subject session revocation failed")
        return result

    def revoke_session(self, sid: str) -> bool:
        """Revoga imediatamente um SID conhecido sem criar uma nova sessão"""
        if not isinstance(sid, str) or not _SID_RE.fullmatch(sid):
            raise ValueError("sid is invalid")
        try:
            return bool(self._client.delete(self._key(sid)))
        except Exception as exc:
            raise SessionBackendError("session revocation failed") from exc

    def _rotate_loaded_session(
        self,
        app: Flask,
        session: RedisSession,
        *,
        reset_lifetime: bool,
    ) -> None:
        if session.loaded_envelope is None or session.metadata is None:
            raise SessionBackendError("server-side session rotation requires loaded state")
        codec = self._codec(app)
        now = self._now()
        new_sid = self._new_sid()
        metadata = codec.refresh_metadata(
            session.metadata,
            now,
            rotate_sid=True,
            reset_lifetime=reset_lifetime,
        )
        try:
            new_payload = codec.seal(new_sid, dict(session), metadata)
            ttl = self._ttl(codec, metadata, now)
            result = self._client.eval(
                _ATOMIC_ROTATE_SCRIPT,
                2,
                self._key(session.sid),
                self._key(new_sid),
                session.loaded_envelope,
                new_payload,
                str(ttl),
            )
        except SessionEnvelopeError as exc:
            raise SessionBackendError(
                "server-side session rotation could not serialize state"
            ) from exc
        except Exception as exc:
            raise SessionBackendError("server-side session rotation failed") from exc
        if result != 1:
            raise SessionBackendError("server-side session rotation was rejected")
        session.sid = new_sid
        session.metadata = metadata
        session.loaded_envelope = new_payload
        session.new = False
        session.needs_rewrap = False
        session.rotate_required = False
        session.activity_due = False
        session.modified = True

    def _invalidated_session(self, app: Flask, key: str, payload: bytes) -> RedisSession:
        try:
            result = self._client.eval(_COMPARE_DELETE_SCRIPT, 1, key, payload)
        except Exception:
            app.logger.error("invalid server-side session cleanup failed")
            return self._fresh_session(app, backend_available=False)
        if result != 1:
            app.logger.warning("invalid server-side session changed during cleanup")
            return self._fresh_session(app, backend_available=False)
        return self._fresh_session(app, discard_cookie=True)

    def _load_subject_revision(self, subject_id: str) -> int:
        try:
            raw = self._client.get(self._subject_revision_key(subject_id))
        except Exception as exc:
            raise SessionBackendError("subject session revision load failed") from exc
        if raw is None:
            return 0
        if not isinstance(raw, (bytes, bytearray)):
            raise SessionBackendError("subject session revision is invalid")
        try:
            value = int(bytes(raw).decode("ascii"))
        except (UnicodeError, ValueError) as exc:
            raise SessionBackendError("subject session revision is invalid") from exc
        if not 0 <= value <= 2**63 - 1:
            raise SessionBackendError("subject session revision is invalid")
        return value

    def _codec(self, app: Flask) -> SessionEnvelopeCodec:
        if self._configured_codec is not None:
            return self._configured_codec
        cached = app.extensions.get("template_session_codec")
        if isinstance(cached, SessionEnvelopeCodec):
            return cached
        keys = app.config.get("SESSION_PAYLOAD_KEYS")
        if not isinstance(keys, Sequence) or isinstance(keys, (str, bytes)) or not keys:
            keys = app.config.get("SESSION_SIGNING_KEYS")
        if not isinstance(keys, Sequence) or isinstance(keys, (str, bytes)) or not keys:
            keys = (app.secret_key,) if app.secret_key else ()
        if not keys:
            raise RuntimeError("SESSION_PAYLOAD_KEYS or SECRET_KEY is required for sessions")
        idle_timeout = int(
            app.config.get(
                "SESSION_IDLE_TIMEOUT_SECONDS",
                app.permanent_session_lifetime.total_seconds(),
            )
        )
        absolute_timeout = int(
            app.config.get(
                "SESSION_ABSOLUTE_TIMEOUT_SECONDS",
                max(idle_timeout, min(idle_timeout * 8, 86_400)),
            )
        )
        renewal_default = min(900, max(1, absolute_timeout - 1))
        codec = SessionEnvelopeCodec(
            tuple(keys),
            namespace=str(app.config.get("SESSION_NAMESPACE", "msentra-template")),
            idle_timeout_seconds=idle_timeout,
            absolute_timeout_seconds=absolute_timeout,
            sid_renewal_seconds=int(
                app.config.get("SESSION_SID_RENEWAL_SECONDS", renewal_default)
            ),
            clock_skew_seconds=int(app.config.get("SESSION_CLOCK_SKEW_SECONDS", 30)),
            allowed_keys=tuple(app.config.get("SESSION_ALLOWED_KEYS", ())),
            strict_schema=bool(app.config.get("SESSION_SCHEMA_STRICT", False)),
        )
        app.extensions["template_session_codec"] = codec
        return codec

    def _delete_cookie(self, app: Flask, response: Response, cookie_name: str) -> None:
        response.delete_cookie(
            cookie_name,
            domain=self.get_cookie_domain(app),
            path=self.get_cookie_path(app),
            secure=self.get_cookie_secure(app),
            httponly=self.get_cookie_httponly(app),
            samesite=self.get_cookie_samesite(app),
        )

    def _fresh_session(
        self,
        app: Flask,
        *,
        discard_cookie: bool = False,
        backend_available: bool = True,
        stateless: bool = False,
    ) -> RedisSession:
        codec = self._codec(app)
        return self.session_class(
            {},
            sid=self._new_sid(),
            new=True,
            discard_cookie=discard_cookie,
            backend_available=backend_available,
            stateless=stateless,
            metadata=codec.new_metadata(self._now()),
        )

    @staticmethod
    def _is_stateless_request(app: Flask, request: Request) -> bool:
        if request.path in _STATELESS_PATHS:
            return True
        static_path = (app.static_url_path or "").rstrip("/")
        return bool(
            static_path
            and static_path != "/"
            and (request.path == static_path or request.path.startswith(f"{static_path}/"))
        )

    @staticmethod
    def _replace_response_with_error(
        response: Response,
        *,
        status_code: int,
        retry_after: int | None = None,
    ) -> None:
        body = "Service Unavailable\n" if status_code == 503 else "Internal Server Error\n"
        response.direct_passthrough = False
        response.status_code = status_code
        response.set_data(body)
        response.content_type = "text/plain; charset=utf-8"
        for header in (
            "Accept-Ranges",
            "Allow",
            "Content-Disposition",
            "Content-Encoding",
            "Content-Location",
            "Content-Range",
            "Digest",
            "ETag",
            "Last-Modified",
            "Location",
            "Set-Cookie",
            "WWW-Authenticate",
        ):
            response.headers.pop(header, None)
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        if retry_after is None:
            response.headers.pop("Retry-After", None)
        else:
            response.headers["Retry-After"] = str(retry_after)

    @staticmethod
    def _has_session_data(session: RedisSession) -> bool:
        return any(key != "_permanent" for key in session)

    @staticmethod
    def _activity_update_seconds(app: Flask, codec: SessionEnvelopeCodec) -> int:
        configured = app.config.get("SESSION_ACTIVITY_UPDATE_SECONDS")
        if configured is not None:
            return max(1, int(configured))
        return max(1, min(60, codec.idle_timeout_seconds // 4))

    @staticmethod
    def _ttl(codec: SessionEnvelopeCodec, metadata: SessionMetadata, now: int) -> int:
        codec.ensure_active(metadata, now)
        absolute_remaining = metadata.issued_at + codec.absolute_timeout_seconds - now
        if absolute_remaining <= 0:
            raise SessionEnvelopeExpired("session absolute timeout was exceeded")
        return min(codec.idle_timeout_seconds, absolute_remaining)

    @staticmethod
    def _cookie_expiration(
        codec: SessionEnvelopeCodec,
        metadata: SessionMetadata | None,
    ) -> datetime | None:
        if metadata is None:
            return None
        return datetime.fromtimestamp(
            metadata.issued_at + codec.absolute_timeout_seconds,
            tz=UTC,
        )

    def _key(self, sid: str) -> str:
        return f"{self._key_prefix}{sid}"

    def _subject_revision_key(self, subject_id: str) -> str:
        return f"{self._revocation_prefix}subject:{subject_id}"

    def _new_sid(self) -> str:
        return token_urlsafe(32)

    def _now(self) -> int:
        value = self._clock()
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise SessionBackendError("session clock returned an invalid value")
        timestamp = int(value)
        if timestamp < 0:
            raise SessionBackendError("session clock returned an invalid value")
        return timestamp

    def _signers(self, app: Flask) -> tuple[Signer, ...]:
        configured = app.config.get("SESSION_SIGNING_KEYS")
        if configured is None:
            configured = (app.secret_key,) if app.secret_key else ()
        if isinstance(configured, str):
            keys: tuple[object, ...] = (configured,)
        elif isinstance(configured, (tuple, list)):
            keys = tuple(configured)
        else:
            keys = ()
        if not keys:
            raise RuntimeError("SECRET_KEY or SESSION_SIGNING_KEYS is required for sessions")
        if len(keys) > _MAX_SIGNING_KEYS:
            raise RuntimeError("SESSION_SIGNING_KEYS must contain at most five keys")
        if any(not isinstance(key, (str, bytes)) or not key for key in keys):
            raise RuntimeError("SESSION_SIGNING_KEYS contains an invalid key")
        return tuple(
            Signer(
                key,
                salt="msentra-template-session",
                digest_method=sha256,
            )
            for key in keys
        )

    def _signer(self, app: Flask) -> Signer:
        """Retorna o signer ativo, preservando o helper interno da versão 1.0.x"""
        return self._signers(app)[0]

    def _sign_sid(self, app: Flask, sid: str) -> str:
        return self._signer(app).sign(sid.encode()).decode()

    def _unsign_sid(self, app: Flask, signed_sid: str) -> tuple[str, bool] | None:
        for index, signer in enumerate(self._signers(app)):
            try:
                sid = signer.unsign(signed_sid.encode()).decode()
            except (BadSignature, UnicodeError):
                continue
            if _SID_RE.fullmatch(sid):
                return sid, index > 0
            return None
        return None


def register_session_backend_guard(app: Flask) -> None:
    """Bloqueia rotas dependentes de sessão durante falhas transitórias do Redis"""

    @app.before_request
    def ensure_session_backend_available() -> None:
        if request.endpoint is None or request.endpoint in {"static", "web.live", "web.ready"}:
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
