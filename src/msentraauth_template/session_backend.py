from __future__ import annotations

import re
from collections.abc import Mapping
from hashlib import sha256
from secrets import token_urlsafe

from flask import Flask, Request, Response
from flask.json.tag import TaggedJSONSerializer
from flask.sessions import SessionInterface, SessionMixin
from itsdangerous import BadSignature, Signer
from werkzeug.datastructures import CallbackDict

from .storage import RedisClient

_SID_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
_MAX_SESSION_BYTES = 64 * 1024


class SessionBackendError(RuntimeError):
    """Gerado quando uma sessão do servidor não pode ser persistida com segurança"""


class RedisSession(CallbackDict[str, object], SessionMixin):
    """Sessão Flask mutável cujo payload permanece no Redis"""

    def __init__(
        self,
        initial: Mapping[str, object] | None = None,
        *,
        sid: str,
        new: bool,
        discard_cookie: bool = False,
    ) -> None:
        def on_update(_: object) -> None:
            self.modified = True

        super().__init__(initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False
        self.discard_cookie = discard_cookie


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
        signed_sid = request.cookies.get(self.get_cookie_name(app))
        sid = self._unsign_sid(app, signed_sid) if signed_sid else None
        if sid is None:
            return self._fresh_session(app, discard_cookie=signed_sid is not None)
        try:
            payload = self._client.get(self._key(sid))
        except Exception:
            app.logger.error("server-side session load failed")
            return self._fresh_session(app, discard_cookie=True)
        if payload is None:
            return self._fresh_session(app, discard_cookie=True)
        if len(payload) > _MAX_SESSION_BYTES:
            app.logger.warning("server-side session payload exceeded the accepted size")
            return self._fresh_session(app, discard_cookie=True)
        try:
            decoded = self.serializer.loads(payload.decode("utf-8"))
        except Exception:
            app.logger.warning("server-side session payload was invalid")
            return self._fresh_session(app, discard_cookie=True)
        if not isinstance(decoded, dict):
            app.logger.warning("server-side session payload had an invalid structure")
            return self._fresh_session(app, discard_cookie=True)
        return self.session_class(decoded, sid=sid, new=False)

    def save_session(self, app: Flask, session: SessionMixin, response: Response) -> None:
        if not isinstance(session, RedisSession):
            raise TypeError("session must be RedisSession")
        if session.accessed:
            response.vary.add("Cookie")

        cookie_name = self.get_cookie_name(app)
        key = self._key(session.sid)
        if not session:
            if session.modified or session.discard_cookie:
                try:
                    self._client.delete(key)
                except Exception:
                    app.logger.error("server-side session deletion failed")
                self._delete_cookie(app, response, cookie_name)
            return

        if not self.should_set_cookie(app, session):
            if session.discard_cookie:
                self._delete_cookie(app, response, cookie_name)
            return

        payload = self.serializer.dumps(dict(session)).encode("utf-8")
        if len(payload) > _MAX_SESSION_BYTES:
            raise SessionBackendError("server-side session payload is too large")
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
            app.logger.error("server-side session save failed")
            raise SessionBackendError("server-side session save failed") from exc
        if not result:
            raise SessionBackendError("server-side session save failed")

        session.new = False
        session.discard_cookie = False
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

    def _delete_cookie(self, app: Flask, response: Response, cookie_name: str) -> None:
        response.delete_cookie(
            cookie_name,
            domain=self.get_cookie_domain(app),
            path=self.get_cookie_path(app),
            secure=self.get_cookie_secure(app),
            httponly=self.get_cookie_httponly(app),
            samesite=self.get_cookie_samesite(app),
        )

    def _fresh_session(self, app: Flask, *, discard_cookie: bool = False) -> RedisSession:
        initial: dict[str, object] = {}
        if app.config.get("SESSION_PERMANENT", False):
            initial["_permanent"] = True
        return self.session_class(
            initial, sid=self._new_sid(), new=True, discard_cookie=discard_cookie
        )

    def _key(self, sid: str) -> str:
        return f"{self._key_prefix}{sid}"

    def _new_sid(self) -> str:
        return token_urlsafe(32)

    def _signer(self, app: Flask) -> Signer:
        if not app.secret_key:
            raise RuntimeError("SECRET_KEY is required for server-side sessions")
        return Signer(
            app.secret_key,
            salt="msentra-template-session",
            digest_method=sha256,
        )

    def _sign_sid(self, app: Flask, sid: str) -> str:
        return self._signer(app).sign(sid.encode()).decode()

    def _unsign_sid(self, app: Flask, signed_sid: str) -> str | None:
        try:
            sid = self._signer(app).unsign(signed_sid.encode()).decode()
        except (BadSignature, UnicodeError):
            return None
        return sid if _SID_RE.fullmatch(sid) else None


__all__ = ["RedisSession", "RedisSessionInterface", "SessionBackendError"]
