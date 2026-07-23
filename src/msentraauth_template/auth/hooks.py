from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from logging import Logger
from threading import RLock
from time import time

from flask import current_app, session
from flask_ms_entra_auth import Identity, MicrosoftEntraAuth

from ..session_backend import RedisSessionInterface

_DEFAULT_MAX_USERS = 10_000


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
    # Registro demonstrativo thread-safe e limitado (não substitui persistência)

    __slots__ = ("_lock", "_max_users", "_users")

    def __init__(self, *, max_users: int = _DEFAULT_MAX_USERS) -> None:
        if isinstance(max_users, bool) or not isinstance(max_users, int) or max_users <= 0:
            raise ValueError("max_users must be a positive integer")
        self._lock = RLock()
        self._max_users = max_users
        self._users: OrderedDict[tuple[str, str], LocalUser] = OrderedDict()

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
            self._users.move_to_end(user.stable_id)
            while len(self._users) > self._max_users:
                self._users.popitem(last=False)
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
    # Registra comportamento da aplicação sem duplicar o protocolo OAuth/OIDC

    @extension.on_authenticated
    def bind_authenticated_identity(identity: Identity) -> None:
        interface = current_app.session_interface
        if not isinstance(interface, RedisSessionInterface):
            raise RuntimeError("the configured session interface cannot rotate session IDs")
        interface.regenerate(current_app, session)
        interface.bind_identity(
            current_app,
            session,
            tenant_id=identity.tenant_id,
            object_id=identity.object_id,
        )
        users.bind(identity)

    @extension.on_logout
    def log_local_logout(identity: Identity | None) -> None:
        logger.info(
            "local authentication state cleared",
            extra={"had_identity": identity is not None},
        )


__all__ = ["LocalUser", "LocalUserRegistry", "register_auth_hooks"]
