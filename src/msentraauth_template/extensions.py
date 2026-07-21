from __future__ import annotations

from dataclasses import dataclass

from flask_ms_entra_auth import AuthStorage, MicrosoftEntraAuth
from flask_ms_entra_auth.auth.protocols import MsalClientFactory
from flask_wtf.csrf import CSRFProtect  # type: ignore[import-untyped]

csrf = CSRFProtect()


@dataclass(frozen=True, slots=True)
class _EntraAuthFactory:
    # Crie uma instância de extensão para uma application factory invocation

    def with_runtime(
        self,
        *,
        storage: AuthStorage,
        msal_client_factory: MsalClientFactory | None,
    ) -> MicrosoftEntraAuth:
        return MicrosoftEntraAuth(
            storage=storage,
            msal_client_factory=msal_client_factory,
        )


entra_auth = _EntraAuthFactory()

__all__ = ["csrf", "entra_auth"]
