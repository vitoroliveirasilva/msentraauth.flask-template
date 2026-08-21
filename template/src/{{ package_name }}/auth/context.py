from __future__ import annotations

from dataclasses import dataclass

from flask_ms_entra_auth import AuthenticationRequired, current_identity


@dataclass(frozen=True, slots=True)
class AuthContext:
    authenticated: bool
    display_name: str | None = None
    username: str | None = None


def get_auth_context() -> AuthContext:
    try:
        identity = current_identity._get_current_object()
    except AuthenticationRequired:
        return AuthContext(False)
    return AuthContext(True, identity.display_name, identity.username)


__all__ = ["AuthContext", "get_auth_context"]
