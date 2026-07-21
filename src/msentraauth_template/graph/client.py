from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..settings import AppSettings


class GraphError(RuntimeError):
    """Exceção base para falhas previsíveis do Graph"""


class GraphUnauthorized(GraphError):
    """Lançada quando o Graph rejeita a credencial delegada"""


class GraphUnavailable(GraphError):
    """Lançada quando o Graph não pode ser alcançado ou retorna uma falha transitória"""


@dataclass(frozen=True, slots=True)
class GraphProfile:
    id: str
    display_name: str
    user_principal_name: str | None
    mail: str | None


class HttpResponse(Protocol):
    status_code: int

    def json(self) -> object: ...


class HttpTransport(Protocol):
    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        timeout: tuple[float, float],
    ) -> HttpResponse: ...


class GraphClient:
    """Solicita apenas os campos de perfil renderizados pelo template"""

    __slots__ = ("_base_url", "_timeout", "_transport")

    def __init__(
        self,
        *,
        base_url: str,
        connect_timeout: float,
        read_timeout: float,
        transport: HttpTransport,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = (connect_timeout, read_timeout)
        self._transport = transport

    @classmethod
    def from_settings(
        cls,
        settings: AppSettings,
        *,
        transport: HttpTransport | None = None,
    ) -> GraphClient:
        return cls(
            base_url=settings.graph_base_url,
            connect_timeout=settings.graph_connect_timeout,
            read_timeout=settings.graph_read_timeout,
            transport=transport or _build_transport(),
        )

    def get_profile(self, access_token: str) -> GraphProfile:
        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("access_token must be a non-empty string")
        normalized_token = access_token.strip()
        try:
            response = self._transport.get(
                f"{self._base_url}/me",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {normalized_token}",
                    "User-Agent": "msentraauth-flask-template/1.0",
                },
                params={"$select": "id,displayName,userPrincipalName,mail"},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise GraphUnavailable("Microsoft Graph is unavailable") from exc
        except Exception as exc:
            raise GraphUnavailable("Microsoft Graph request failed") from exc

        if response.status_code in {401, 403}:
            raise GraphUnauthorized("Microsoft Graph rejected the delegated credential")
        if response.status_code == 429 or response.status_code >= 500:
            raise GraphUnavailable("Microsoft Graph is temporarily unavailable")
        if response.status_code != 200:
            raise GraphError("Microsoft Graph returned an unexpected response")

        try:
            payload = response.json()
        except Exception as exc:
            raise GraphError("Microsoft Graph returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise GraphError("Microsoft Graph returned an invalid profile")
        return _profile_from_payload(payload)


def _build_transport() -> requests.Session:
    retries = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=(429, 500, 502, 503, 504),
        backoff_factor=0.25,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    transport = requests.Session()
    transport.mount("https://", adapter)
    return transport


def _profile_from_payload(payload: Mapping[object, object]) -> GraphProfile:
    identifier = _required_text(payload, "id")
    display_name = _required_text(payload, "displayName")
    return GraphProfile(
        id=identifier,
        display_name=display_name,
        user_principal_name=_optional_text(payload, "userPrincipalName"),
        mail=_optional_text(payload, "mail"),
    )


def _required_text(payload: Mapping[object, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GraphError("Microsoft Graph returned an incomplete profile")
    return value.strip()


def _optional_text(payload: Mapping[object, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise GraphError("Microsoft Graph returned an invalid profile")
    normalized = value.strip()
    return normalized or None


__all__ = [
    "GraphClient",
    "GraphError",
    "GraphProfile",
    "GraphUnauthorized",
    "GraphUnavailable",
    "HttpTransport",
]
