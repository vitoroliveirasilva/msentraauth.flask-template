from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Protocol, cast

import requests
from requests.adapters import HTTPAdapter
from requests.utils import parse_dict_header
from urllib3.util.retry import Retry

from ..settings import AppSettings

_MAX_CLAIMS_CHALLENGE_BYTES = 4096
_MAX_PROFILE_ID_CHARACTERS = 128
_MAX_DISPLAY_NAME_CHARACTERS = 256
_MAX_ADDRESS_CHARACTERS = 320
_JSON_CONTENT_TYPE_RE = re.compile(r"^application/(?:[a-z0-9.+-]*\+)?json(?:\s*;|$)", re.IGNORECASE)


class GraphError(RuntimeError):
    """Exceção base para falhas previsíveis do Graph"""


class GraphUnauthorized(GraphError):
    """Lançada quando o Graph rejeita a credencial delegada"""


class GraphForbidden(GraphError):
    """Lançada quando a identidade não possui autorização no Graph"""


class GraphClaimsChallenge(GraphUnauthorized):
    """Sinaliza um claims challenge que exige suporte de reautenticação na extensão"""

    def __init__(self, claims: str) -> None:
        super().__init__("Microsoft Graph requires additional authentication claims")
        self.claims = claims


class GraphUnavailable(GraphError):
    """Lançada quando o Graph não pode ser alcançado ou retorna falha transitória"""

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class GraphRateLimited(GraphUnavailable):
    """Lançada quando o Graph aplica limitação de taxa"""


class GraphRedirectRejected(GraphError):
    """Lançada quando o Graph tenta redirecionar uma chamada autenticada"""


class GraphResponseTooLarge(GraphError):
    """Lançada antes de processar respostas maiores que o limite configurado"""


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


@dataclass(frozen=True, slots=True)
class _BufferedResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes | None

    def json(self) -> object:
        if self.body is None:
            return None
        text = self.body.decode("utf-8")
        return json.loads(text, parse_constant=_reject_json_constant)


class _RequestsTransport:
    __slots__ = ("_max_response_bytes", "_session")

    def __init__(self, session: requests.Session, *, max_response_bytes: int) -> None:
        self._session = session
        self._max_response_bytes = max_response_bytes

    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        timeout: tuple[float, float],
    ) -> HttpResponse:
        try:
            response = self._session.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
            )
        except TypeError:
            # Mantém doubles antigos compatíveis sem enfraquecer requests.Session em runtime
            if isinstance(self._session, requests.sessions.Session):
                raise
            return cast(
                HttpResponse,
                self._session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout,
                ),
            )

        try:
            status_code = int(response.status_code)
            response_headers = dict(response.headers)
            if status_code != 200:
                return _BufferedResponse(status_code, response_headers, None)
            _validate_json_content_type(response_headers)
            body = _read_limited_body(
                response.iter_content(chunk_size=8192),
                response_headers,
                maximum=self._max_response_bytes,
            )
            return _BufferedResponse(status_code, response_headers, body)
        finally:
            response.close()


class GraphClient:
    """Solicita somente os campos de perfil renderizados pelo template"""

    __slots__ = ("_base_url", "_max_retry_after", "_timeout", "_transport")

    def __init__(
        self,
        *,
        base_url: str,
        connect_timeout: float,
        read_timeout: float,
        transport: HttpTransport,
        max_retry_after_seconds: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = (connect_timeout, read_timeout)
        self._transport = transport
        self._max_retry_after = max_retry_after_seconds

    @classmethod
    def from_settings(
        cls,
        settings: AppSettings,
        *,
        transport: HttpTransport | None = None,
    ) -> GraphClient:
        settings.validate()
        return cls(
            base_url=settings.graph_base_url,
            connect_timeout=settings.graph_connect_timeout,
            read_timeout=settings.graph_read_timeout,
            transport=transport
            or _build_transport(
                max_response_bytes=settings.graph_max_response_bytes,
                max_retries=settings.graph_max_retries,
            ),
            max_retry_after_seconds=settings.graph_max_retry_after_seconds,
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
                    "User-Agent": f"msentraauth-flask-template/{_package_version()}",
                },
                params={"$select": "id,displayName,userPrincipalName,mail"},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise GraphUnavailable("Microsoft Graph is unavailable") from exc

        status_code = response.status_code
        if isinstance(status_code, bool) or not isinstance(status_code, int):
            raise GraphError("Microsoft Graph returned an invalid status")
        headers = _response_headers(response)
        if 300 <= status_code < 400:
            raise GraphRedirectRejected("Microsoft Graph redirect was rejected")
        if status_code in {401, 403}:
            claims = _claims_challenge(headers)
            if claims is not None:
                raise GraphClaimsChallenge(claims)
            if status_code == 401:
                raise GraphUnauthorized("Microsoft Graph rejected the delegated credential")
            raise GraphForbidden("Microsoft Graph denied the requested operation")
        if status_code == 429:
            raise GraphRateLimited(
                "Microsoft Graph rate limit was reached",
                retry_after=_bounded_retry_after(headers, maximum=self._max_retry_after),
            )
        if status_code >= 500:
            raise GraphUnavailable(
                "Microsoft Graph is temporarily unavailable",
                retry_after=_bounded_retry_after(headers, maximum=self._max_retry_after),
            )
        if status_code != 200:
            raise GraphError("Microsoft Graph returned an unexpected response")

        try:
            payload = response.json()
        except (UnicodeError, ValueError, TypeError) as exc:
            raise GraphError("Microsoft Graph returned invalid JSON") from exc
        except Exception as exc:
            raise GraphError("Microsoft Graph returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise GraphError("Microsoft Graph returned an invalid profile")
        return _profile_from_payload(payload)


def _build_transport(*, max_response_bytes: int, max_retries: int) -> HttpTransport:
    retries = Retry(
        total=max_retries,
        connect=max_retries,
        read=max_retries,
        status=max_retries,
        allowed_methods=frozenset({"GET"}),
        status_forcelist=(429, 500, 502, 503, 504),
        backoff_factor=0.25,
        backoff_max=2.0,
        respect_retry_after_header=False,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session = requests.Session()
    session.trust_env = False
    session.auth = None
    session.verify = True
    session.mount("https://", adapter)
    return _RequestsTransport(session, max_response_bytes=max_response_bytes)


def _read_limited_body(
    chunks: Iterable[bytes],
    headers: Mapping[str, str],
    *,
    maximum: int,
) -> bytes:
    content_length = _header_value(headers, "Content-Length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise GraphError("Microsoft Graph returned an invalid Content-Length") from exc
        if declared < 0:
            raise GraphError("Microsoft Graph returned an invalid Content-Length")
        if declared > maximum:
            raise GraphResponseTooLarge("Microsoft Graph response exceeded the configured limit")
    body = bytearray()
    for chunk in chunks:
        if not isinstance(chunk, (bytes, bytearray)):
            raise GraphError("Microsoft Graph returned an invalid response body")
        body.extend(chunk)
        if len(body) > maximum:
            raise GraphResponseTooLarge("Microsoft Graph response exceeded the configured limit")
    return bytes(body)


def _validate_json_content_type(headers: Mapping[str, str]) -> None:
    value = _header_value(headers, "Content-Type")
    if value is None or not _JSON_CONTENT_TYPE_RE.match(value.strip()):
        raise GraphError("Microsoft Graph returned an unexpected content type")


def _response_headers(response: HttpResponse) -> Mapping[str, str]:
    value = getattr(response, "headers", {})
    return value if isinstance(value, Mapping) else {}


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    expected = name.casefold()
    for key, value in headers.items():
        if isinstance(key, str) and key.casefold() == expected and isinstance(value, str):
            return value.strip()
    return None


def _claims_challenge(headers: Mapping[str, str]) -> str | None:
    header = _header_value(headers, "WWW-Authenticate")
    if header is None or not header.lower().startswith("bearer "):
        return None
    parameters = parse_dict_header(header[7:].strip())
    raw_claims = parameters.get("claims")
    if raw_claims is None:
        return None
    if (
        not isinstance(raw_claims, str)
        or len(raw_claims.encode("utf-8")) > _MAX_CLAIMS_CHALLENGE_BYTES
    ):
        raise GraphError("Microsoft Graph returned an invalid claims challenge")
    try:
        payload = json.loads(raw_claims, parse_constant=_reject_json_constant)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise GraphError("Microsoft Graph returned an invalid claims challenge") from exc
    if not isinstance(payload, dict):
        raise GraphError("Microsoft Graph returned an invalid claims challenge")
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _bounded_retry_after(headers: Mapping[str, str], *, maximum: int) -> int | None:
    raw = _header_value(headers, "Retry-After")
    if raw is None:
        return None
    try:
        seconds = int(raw)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        seconds = int((retry_at - datetime.now(UTC)).total_seconds())
    if seconds <= 0:
        return 1
    return min(seconds, maximum)


def _profile_from_payload(payload: Mapping[object, object]) -> GraphProfile:
    identifier = _required_text(
        payload,
        "id",
        maximum=_MAX_PROFILE_ID_CHARACTERS,
    )
    display_name = _required_text(
        payload,
        "displayName",
        maximum=_MAX_DISPLAY_NAME_CHARACTERS,
    )
    return GraphProfile(
        id=identifier,
        display_name=display_name,
        user_principal_name=_optional_text(
            payload,
            "userPrincipalName",
            maximum=_MAX_ADDRESS_CHARACTERS,
        ),
        mail=_optional_text(payload, "mail", maximum=_MAX_ADDRESS_CHARACTERS),
    )


def _required_text(payload: Mapping[object, object], key: str, *, maximum: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GraphError("Microsoft Graph returned an incomplete profile")
    return _normalize_profile_text(value, maximum=maximum)


def _optional_text(
    payload: Mapping[object, object],
    key: str,
    *,
    maximum: int,
) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise GraphError("Microsoft Graph returned an invalid profile")
    normalized = value.strip()
    if not normalized:
        return None
    return _normalize_profile_text(normalized, maximum=maximum)


def _normalize_profile_text(value: str, *, maximum: int) -> str:
    normalized = value.strip()
    if len(normalized) > maximum or any(
        ord(character) < 32 or ord(character) == 127 for character in normalized
    ):
        raise GraphError("Microsoft Graph returned an invalid profile")
    return normalized


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"unsupported JSON constant: {value}")


def _package_version() -> str:
    try:
        return version("msentraauth-flask-template")
    except PackageNotFoundError:
        return "0+unknown"


__all__ = [
    "GraphClaimsChallenge",
    "GraphClient",
    "GraphError",
    "GraphForbidden",
    "GraphProfile",
    "GraphRateLimited",
    "GraphRedirectRejected",
    "GraphResponseTooLarge",
    "GraphUnauthorized",
    "GraphUnavailable",
    "HttpTransport",
]
