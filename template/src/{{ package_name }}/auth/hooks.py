from __future__ import annotations

from logging import Logger
from typing import Protocol

from flask import current_app, session
from flask_ms_entra_auth import Identity, MicrosoftEntraAuth

from ..infrastructure.session_backend import RedisSessionInterface


class AuthenticatedIdentityHandler(Protocol):
    def __call__(self, identity: Identity) -> None: ...


def register_auth_hooks(
    extension: MicrosoftEntraAuth,
    logger: Logger,
    identity_handler: AuthenticatedIdentityHandler | None = None,
) -> None:
    @extension.on_authenticated
    def bind_authenticated_identity(identity: Identity) -> None:
        interface = current_app.session_interface
        if not isinstance(interface, RedisSessionInterface):
            raise RuntimeError("configured session interface cannot rotate session IDs")
        interface.regenerate(current_app, session)
        interface.bind_identity(
            current_app,
            session,
            tenant_id=identity.tenant_id,
            object_id=identity.object_id,
        )
        if identity_handler is not None:
            identity_handler(identity)

    @extension.on_logout
    def log_local_logout(identity: Identity | None) -> None:
        logger.info(
            "local authentication state cleared", extra={"had_identity": identity is not None}
        )


__all__ = ["AuthenticatedIdentityHandler", "register_auth_hooks"]
