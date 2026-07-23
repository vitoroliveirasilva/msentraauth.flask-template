from __future__ import annotations

import re
from collections.abc import Mapping
from hashlib import sha256
from secrets import token_urlsafe
from typing import Any

from flask import Flask, Request, Response, request, session
from flask.json.tag import TaggedJSONSerializer
from flask.sessions import SessionInterface, SessionMixin
from itsdangerous import BadSignature, Signer
from werkzeug.datastructures import CallbackDict

from .storage import RedisClient

_SID_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
_MAX_SESSION_BYTES = 64 * 1024
_MAX_SIGNING_KEYS = 5
_STATELESS_PATHS = frozenset({"/health/live", "/health/ready"})


class SessionBackendError(RuntimeError):
    """Gerado quando uma sessão do servidor não pode ser persistida com segurança"""


class SessionBackendUnavailable(SessionBackendError):
    """Gerado quando o backend de sessão está temporariamente indisponível"""


class RedisSession(CallbackDict[str, object], SessionMixin):
    # Sessão Flask mutável cujo payload permanece no Redis

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
    """Persiste payloads de sessão no Redis e assina apenas o SID opaco"""

    serializer = TaggedJSONSerializer()
    session_class = RedisSession

    def __init__(
        self,
        client: RedisClient,
        *,
        key_prefix: str = "msentra-template:session:",
    ) -> None:
        if not isinstance(client, RedisClient):
            raise TypeError("client must implement RedisClient")
        if not key_prefix or not key_prefix.endswith(":"):
            raise ValueError("key_prefix must be non-empty and end with ':'")
        self._client = client
        self._key_prefix = key_prefix

    def open_session(self, app: Flask, request: Request) -> RedisSession:
        if self._is_stateless_request(app, request):
            return self._fresh_session(app, stateless=True)

        signed_sid = request.cookies.get(self.get_cookie_name(app))
        resolved_sid = self._unsign_sid(app, signed_sid) if signed_sid else None
        if resolved_sid is None:
            return self._fresh_session(app, discard_cookie=signed_sid is not None)
        sid, resign_cookie = resolved_sid
        try:
            payload = self._client.get(self._key(sid))
        except Exception:
            app.logger.error("server-side session load failed")
            return self._fresh_session(app, backend_available=False)
        if payload is None:
            # Não expire o cookie aqui: uma resposta concorrente com o SID antigo
            # poderia apagar o cookie recém-rotacionado emitido por outra resposta.
            return self._fresh_session(app)
        if not isinstance(payload, (bytes, bytearray)):
            app.logger.error("server-side session backend returned an invalid payload type")
            return self._fresh_session(app, backend_available=False)
        payload_bytes = bytes(payload)
        if len(payload_bytes) > _MAX_SESSION_BYTES:
            app.logger.warning("server-side session payload exceeded the accepted size")
            return self._fresh_session(app, discard_cookie=True)
        try:
            decoded = self.serializer.loads(payload_bytes.decode("utf-8"))
        except Exception:
            app.logger.warning("server-side session payload was invalid")
            return self._fresh_session(app, discard_cookie=True)
        if not isinstance(decoded, dict):
            app.logger.warning("server-side session payload had an invalid structure")
            return self._fresh_session(app, discard_cookie=True)
        return self.session_class(
            decoded,
            sid=sid,
            new=False,
            resign_cookie=resign_cookie,
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

        if not (self.should_set_cookie(app, session) or session.resign_cookie):
            if session.discard_cookie:
                self._delete_cookie(app, response, cookie_name)
            return

        try:
            payload = self.serializer.dumps(dict(session)).encode("utf-8")
        except Exception as exc:
            app.logger.error(
                "server-side session serialization failed",
                extra={"error_type": type(exc).__name__, "status_code": 500},
            )
            self._replace_response_with_error(response, status_code=500)
            return
        if len(payload) > _MAX_SESSION_BYTES:
            app.logger.error(
                "server-side session payload is too large",
                extra={"status_code": 500},
            )
            self._replace_response_with_error(response, status_code=500)
            return
        ttl = int(app.permanent_session_lifetime.total_seconds())
        try:
            result = self._client.set(
                key,
                payload,
                ex=ttl,
                nx=session.new,
                xx=not session.new,
            )
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

        session.new = False
        session.discard_cookie = False
        session.resign_cookie = False
        response.set_cookie(
            cookie_name,
            self._sign_sid(app, session.sid),
            expires=self.get_expiration_time(app, session),
            httponly=self.get_cookie_httponly(app),
            domain=self.get_cookie_domain(app),
            path=self.get_cookie_path(app),
            secure=self.get_cookie_secure(app),
            partitioned=self.get_cookie_partitioned(app),
            samesite=self.get_cookie_samesite(app),
        )

    def regenerate(self, app: Flask, session: SessionMixin) -> None:
        """Roda o identificador de sessão do navegador preservando seu payload"""
        if not isinstance(session, RedisSession):
            raise TypeError("session must be RedisSession")
        old_key = self._key(session.sid)
        try:
            self._client.delete(old_key)
        except Exception as exc:
            app.logger.error("server-side session rotation failed")
            raise SessionBackendError("server-side session rotation failed") from exc
        session.sid = self._new_sid()
        session.new = True
        session.modified = True
        session.resign_cookie = False

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
        return self.session_class(
            {},
            sid=self._new_sid(),
            new=True,
            discard_cookie=discard_cookie,
            backend_available=backend_available,
            stateless=stateless,
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
            if header in response.headers:
                del response.headers[header]
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
        if retry_after is None:
            response.headers.pop("Retry-After", None)
        else:
            response.headers["Retry-After"] = str(retry_after)

    @staticmethod
    def _has_session_data(session: RedisSession) -> bool:
        return any(key != "_permanent" for key in session)

    def _key(self, sid: str) -> str:
        return f"{self._key_prefix}{sid}"

    def _new_sid(self) -> str:
        return token_urlsafe(32)

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
