from __future__ import annotations

from dataclasses import dataclass
from logging import Logger
from threading import RLock
from time import time

from flask import current_app, session
from flask_ms_entra_auth import Identity, MicrosoftEntraAuth

from ..session_backend import RedisSessionInterface


@dataclass(frozen=True, slots=True)
class LocalUser:
    # Pequena projeção local indexada por identificadores externos estáveis

    tenant_id: str
    object_id: str
    display_name: str | None
    username: str | None
    last_authenticated_at: float

    @property
    def stable_id(self) -> tuple[str, str]:
        return (self.tenant_id, self.object_id)


class LocalUserRegistry:
    # Registro de demonstração seguro para threads; não é um banco de dados de produção

    __slots__ = ("_lock", "_users")

    def __init__(self) -> None:
        self._lock = RLock()
        self._users: dict[tuple[str, str], LocalUser] = {}

    def bind(self, identity: Identity) -> LocalUser:
        user = LocalUser(
            tenant_id=identity.tenant_id,
            object_id=identity.object_id,
            display_name=identity.display_name,
            username=identity.username,
            last_authenticated_at=time(),
        )
        with self._lock:
            self._users[user.stable_id] = user
        return user

    def get(self, tenant_id: str, object_id: str) -> LocalUser | None:
        with self._lock:
            return self._users.get((tenant_id, object_id))

    def count(self) -> int:
        with self._lock:
            return len(self._users)


def register_auth_hooks(
    extension: MicrosoftEntraAuth,
    users: LocalUserRegistry,
    logger: Logger,
) -> None:
    # Registra o comportamento da aplicação sem duplicar o código do protocolo

    @extension.on_authenticated
    def bind_authenticated_identity(identity: Identity) -> None:
        users.bind(identity)
        interface = current_app.session_interface
        if not isinstance(interface, RedisSessionInterface):
            raise RuntimeError(
                "the configured session interface cannot rotate session IDs"
            )
        interface.regenerate(current_app, session)

    @extension.on_logout
    def log_local_logout(identity: Identity | None) -> None:
        logger.info(
            "local authentication state cleared",
            extra={"had_identity": identity is not None},
        )


__all__ = ["LocalUser", "LocalUserRegistry", "register_auth_hooks"]
