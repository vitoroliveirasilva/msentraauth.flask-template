from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from math import isfinite
from typing import Protocol, cast

import requests
from requests.adapters import HTTPAdapter
from requests.utils import parse_dict_header
from urllib3.util.retry import Retry

from ...settings import AppSettings

_JSON_CONTENT_TYPE = re.compile(r"^application/(?:[a-z0-9.+-]*\+)?json(?:\s*;|$)", re.IGNORECASE)
_APPROVED_BASE_URLS = frozenset({"https://graph.microsoft.com/v1.0"})
_parse_dict_header = cast(Callable[[str], dict[str, str | None]], parse_dict_header)


class GraphError(RuntimeError):
    pass


class GraphUnauthorized(GraphError):
    pass


class GraphForbidden(GraphError):
    pass


class GraphClaimsChallenge(GraphUnauthorized):
    def __init__(self, claims: str) -> None:
        super().__init__("Microsoft Graph requires additional authentication claims")
        self.claims = claims


class GraphUnavailable(GraphError):
    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class GraphRateLimited(GraphUnavailable):
    pass


class GraphRedirectRejected(GraphError):
    pass


class GraphResponseTooLarge(GraphError):
    pass


@dataclass(frozen=True, slots=True)
class GraphProfile:
    id: str
    display_name: str
    user_principal_name: str | None
    mail: str | None


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes | None

    def json(self) -> object:
        return None if self.body is None else json.loads(self.body.decode("utf-8"))


class HttpTransport(Protocol):
    def get(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        timeout: tuple[float, float],
    ) -> HttpResponse: ...


class RequestsTransport:
    def __init__(self, session: requests.Session, *, max_response_bytes: int) -> None:
        if (
            not isinstance(max_response_bytes, int)
            or isinstance(max_response_bytes, bool)
            or not 1 <= max_response_bytes <= 256 * 1024
        ):
            raise ValueError("max_response_bytes must be between 1 and 262144")
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
        response = self._session.get(
            url, headers=headers, params=params, timeout=timeout, allow_redirects=False, stream=True
        )
        try:
            status = int(response.status_code)
            response_headers = dict(response.headers)
            if status != 200:
                return HttpResponse(status, response_headers, None)
            content_type = _header(response_headers, "Content-Type")
            if content_type is None or not _JSON_CONTENT_TYPE.match(content_type):
                raise GraphError("Microsoft Graph returned an unexpected content type")
            body = _read_limited(
                response.iter_content(chunk_size=8192), response_headers, self._max_response_bytes
            )
            return HttpResponse(status, response_headers, body)
        finally:
            response.close()


class GraphClient:
    def __init__(
        self,
        *,
        base_url: str,
        connect_timeout: float,
        read_timeout: float,
        transport: HttpTransport,
        max_retry_after_seconds: int = 30,
    ) -> None:
        canonical_base_url = base_url.rstrip("/")
        if canonical_base_url not in _APPROVED_BASE_URLS:
            raise ValueError("base_url must be an approved Microsoft Graph endpoint")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or not 0 < value <= 30
            for value in (connect_timeout, read_timeout)
        ):
            raise ValueError("Graph timeouts must be finite values between 0 and 30 seconds")
        if (
            isinstance(max_retry_after_seconds, bool)
            or not isinstance(max_retry_after_seconds, int)
            or not 1 <= max_retry_after_seconds <= 120
        ):
            raise ValueError("max_retry_after_seconds must be between 1 and 120")
        if not callable(getattr(transport, "get", None)):
            raise TypeError("transport must provide get()")
        self._base_url = canonical_base_url
        self._timeout = (connect_timeout, read_timeout)
        self._transport = transport
        self._max_retry_after = max_retry_after_seconds

    @classmethod
    def from_settings(
        cls, settings: AppSettings, *, transport: HttpTransport | None = None
    ) -> GraphClient:
        return cls(
            base_url=settings.graph_base_url,
            connect_timeout=settings.graph_connect_timeout,
            read_timeout=settings.graph_read_timeout,
            transport=transport
            or _build_transport(settings.graph_max_response_bytes, settings.graph_max_retries),
            max_retry_after_seconds=settings.graph_max_retry_after_seconds,
        )

    def get_profile(self, access_token: str) -> GraphProfile:
        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("access_token must be non-empty")
        try:
            response = self._transport.get(
                f"{self._base_url}/me",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {access_token.strip()}",
                },
                params={"$select": "id,displayName,userPrincipalName,mail"},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise GraphUnavailable("Microsoft Graph is unavailable") from exc
        status = response.status_code
        if 300 <= status < 400:
            raise GraphRedirectRejected("Microsoft Graph redirect was rejected")
        if status in {401, 403}:
            claims = _claims(response.headers)
            if claims is not None:
                raise GraphClaimsChallenge(claims)
            if status == 401:
                raise GraphUnauthorized("Microsoft Graph rejected delegated access")
            raise GraphForbidden("Microsoft Graph denied the requested operation")
        if status == 429:
            raise GraphRateLimited(
                "Microsoft Graph rate limit was reached",
                retry_after=_retry_after(response.headers, self._max_retry_after),
            )
        if status >= 500:
            raise GraphUnavailable(
                "Microsoft Graph is temporarily unavailable",
                retry_after=_retry_after(response.headers, self._max_retry_after),
            )
        if status != 200:
            raise GraphError("Microsoft Graph returned an unexpected response")
        try:
            payload = response.json()
        except (UnicodeError, ValueError, TypeError) as exc:
            raise GraphError("Microsoft Graph returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise GraphError("Microsoft Graph returned an invalid profile")
        return GraphProfile(
            id=_required(payload, "id", 128),
            display_name=_required(payload, "displayName", 256),
            user_principal_name=_optional(payload, "userPrincipalName", 320),
            mail=_optional(payload, "mail", 320),
        )


def _build_transport(max_response_bytes: int, max_retries: int) -> HttpTransport:
    retry = Retry(
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
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session = requests.Session()
    session.trust_env = False
    session.auth = None
    session.verify = True
    session.mount("https://", adapter)
    return RequestsTransport(session, max_response_bytes=max_response_bytes)


def _read_limited(chunks: Iterable[bytes], headers: Mapping[str, str], maximum: int) -> bytes:
    raw_length = _header(headers, "Content-Length")
    if raw_length is not None:
        try:
            content_length = int(raw_length)
            if content_length < 0:
                raise GraphError("Microsoft Graph returned invalid Content-Length")
            if content_length > maximum:
                raise GraphResponseTooLarge("Microsoft Graph response exceeded limit")
        except ValueError as exc:
            raise GraphError("Microsoft Graph returned invalid Content-Length") from exc
    body = bytearray()
    for chunk in chunks:
        if not isinstance(chunk, (bytes, bytearray)):
            raise GraphError("Microsoft Graph returned invalid response body")
        body.extend(chunk)
        if len(body) > maximum:
            raise GraphResponseTooLarge("Microsoft Graph response exceeded limit")
    return bytes(body)


def _header(headers: Mapping[str, str], name: str) -> str | None:
    for key, value in headers.items():
        if key.casefold() == name.casefold():
            return value.strip()
    return None


def _claims(headers: Mapping[str, str]) -> str | None:
    header = _header(headers, "WWW-Authenticate")
    if header is None or not header.lower().startswith("bearer "):
        return None
    raw = _parse_dict_header(header[7:].strip()).get("claims")
    if not isinstance(raw, str) or len(raw.encode()) > 4096:
        return None
    try:
        payload = json.loads(raw)
    except ValueError:
        return None
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if isinstance(payload, dict)
        else None
    )


def _retry_after(headers: Mapping[str, str], maximum: int) -> int | None:
    raw = _header(headers, "Retry-After")
    if raw is None:
        return None
    try:
        seconds = int(raw)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        seconds = int((parsed - datetime.now(UTC)).total_seconds())
    return min(max(1, seconds), maximum)


def _required(payload: Mapping[object, object], key: str, maximum: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise GraphError("Microsoft Graph returned incomplete profile")
    return _clean(value, maximum)


def _optional(payload: Mapping[object, object], key: str, maximum: int) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise GraphError("Microsoft Graph returned invalid profile")
    return _clean(value, maximum) if value.strip() else None


def _clean(value: str, maximum: int) -> str:
    normalized = value.strip()
    if len(normalized) > maximum or any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
        raise GraphError("Microsoft Graph returned invalid profile")
    return normalized


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
