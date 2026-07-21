from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final
from urllib.parse import SplitResult, urlsplit

from redis import Redis

_PLACEHOLDERS: Final = ("substitua", "changeme", "replace", "gere-uma-chave")
_ENVIRONMENTS: Final = frozenset({"development", "testing", "production"})
_LOG_LEVELS: Final = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})
_LOG_FORMATS: Final = frozenset({"json", "text"})


class SettingsError(ValueError):
    """É gerado quando a configuração do modelo está ausente ou insegura"""


@dataclass(frozen=True, slots=True)
class ProxyHops:
    x_for: int = 0
    x_proto: int = 0
    x_host: int = 0
    x_port: int = 0
    x_prefix: int = 0

    @property
    def any_enabled(self) -> bool:
        return any((self.x_for, self.x_proto, self.x_host, self.x_port, self.x_prefix))


@dataclass(frozen=True, slots=True)
class AppSettings:
    environment: str
    secret_key: str
    base_url: str
    trusted_hosts: tuple[str, ...]
    log_level: str
    log_format: str
    client_id: str
    client_secret: str
    tenant_id: str
    redirect_uri: str
    scopes: tuple[str, ...]
    redis_url: str
    redis_socket_connect_timeout: float
    redis_socket_timeout: float
    redis_health_check_interval: int
    redis_tls_required: bool
    session_lifetime_seconds: int
    session_refresh_each_request: bool
    cookie_secure: bool
    cookie_samesite: str
    graph_base_url: str
    graph_connect_timeout: float
    graph_read_timeout: float
    proxy_hops: ProxyHops = ProxyHops()
    testing: bool = False
    csrf_enabled: bool = True

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> AppSettings:
        values = os.environ if environ is None else environ
        environment = _environment(_text(values, "APP_ENV", default="production"))
        testing = _boolean(values, "TESTING", default=environment == "testing")
        secret_key = _secret(values, "APP_SECRET_KEY", minimum=32)
        base_url = _web_url(_text(values, "APP_BASE_URL"), "APP_BASE_URL")
        trusted_hosts = _csv(values, "APP_TRUSTED_HOSTS", default="localhost,127.0.0.1")
        log_level = _log_level(_text(values, "APP_LOG_LEVEL", default="INFO"))
        log_format = _choice(
            _text(
                values, "APP_LOG_FORMAT", default="json" if environment == "production" else "text"
            ),
            "APP_LOG_FORMAT",
            _LOG_FORMATS,
        )
        cookie_secure = _boolean(
            values,
            "SESSION_COOKIE_SECURE",
            default=environment == "production",
        )
        cookie_samesite = _samesite(_text(values, "SESSION_COOKIE_SAMESITE", default="Lax"))
        redirect_uri = _web_url(
            _text(values, "MS_ENTRA_REDIRECT_URI"),
            "MS_ENTRA_REDIRECT_URI",
        )
        redis_tls_required = _boolean(
            values,
            "REDIS_TLS_REQUIRED",
            default=environment == "production",
        )
        redis_url = _redis_url(_text(values, "REDIS_URL"), tls_required=redis_tls_required)
        scopes = _csv(values, "MS_ENTRA_SCOPES", default="User.Read")
        if "User.Read" not in scopes:
            raise SettingsError("MS_ENTRA_SCOPES must include User.Read for the profile route")

        _validate_environment_security(
            environment=environment,
            base_url=base_url,
            redirect_uri=redirect_uri,
            trusted_hosts=trusted_hosts,
            cookie_secure=cookie_secure,
            cookie_samesite=cookie_samesite,
        )

        return cls(
            environment=environment,
            secret_key=secret_key,
            base_url=base_url.rstrip("/"),
            trusted_hosts=trusted_hosts,
            log_level=log_level,
            log_format=log_format,
            client_id=_text(values, "MS_ENTRA_CLIENT_ID"),
            client_secret=_secret(values, "MS_ENTRA_CLIENT_SECRET", minimum=24),
            tenant_id=_text(values, "MS_ENTRA_TENANT_ID"),
            redirect_uri=redirect_uri,
            scopes=scopes,
            redis_url=redis_url,
            redis_socket_connect_timeout=_positive_float(
                values, "REDIS_CONNECT_TIMEOUT_SECONDS", 3.0
            ),
            redis_socket_timeout=_positive_float(values, "REDIS_READ_TIMEOUT_SECONDS", 3.0),
            redis_health_check_interval=_non_negative_int(
                values, "REDIS_HEALTH_CHECK_INTERVAL_SECONDS", 30
            ),
            redis_tls_required=redis_tls_required,
            session_lifetime_seconds=_positive_int(values, "SESSION_LIFETIME_SECONDS", 3600),
            session_refresh_each_request=_boolean(
                values, "SESSION_REFRESH_EACH_REQUEST", default=True
            ),
            cookie_secure=cookie_secure,
            cookie_samesite=cookie_samesite,
            graph_base_url=_https_url(
                _text(values, "GRAPH_BASE_URL", default="https://graph.microsoft.com/v1.0"),
                "GRAPH_BASE_URL",
            ).rstrip("/"),
            graph_connect_timeout=_positive_float(values, "GRAPH_CONNECT_TIMEOUT_SECONDS", 3.05),
            graph_read_timeout=_positive_float(values, "GRAPH_READ_TIMEOUT_SECONDS", 10.0),
            proxy_hops=ProxyHops(
                x_for=_bounded_non_negative_int(values, "PROXY_X_FOR", 0, maximum=5),
                x_proto=_bounded_non_negative_int(values, "PROXY_X_PROTO", 0, maximum=5),
                x_host=_bounded_non_negative_int(values, "PROXY_X_HOST", 0, maximum=5),
                x_port=_bounded_non_negative_int(values, "PROXY_X_PORT", 0, maximum=5),
                x_prefix=_bounded_non_negative_int(values, "PROXY_X_PREFIX", 0, maximum=5),
            ),
            testing=testing,
            csrf_enabled=_boolean(values, "WTF_CSRF_ENABLED", default=not testing),
        )

    def create_redis_client(self) -> Redis:
        return Redis.from_url(
            self.redis_url,
            decode_responses=False,
            socket_connect_timeout=self.redis_socket_connect_timeout,
            socket_timeout=self.redis_socket_timeout,
            health_check_interval=self.redis_health_check_interval,
        )

    def flask_config(self) -> dict[str, object]:
        production = self.environment == "production"
        return {
            "ENV": self.environment,
            "TESTING": self.testing,
            "DEBUG": self.environment == "development",
            "SECRET_KEY": self.secret_key,
            "TRUSTED_HOSTS": list(self.trusted_hosts),
            "PREFERRED_URL_SCHEME": "https" if production else urlsplit(self.base_url).scheme,
            "MAX_CONTENT_LENGTH": 1 * 1024 * 1024,
            "MAX_FORM_MEMORY_SIZE": 256 * 1024,
            "MAX_FORM_PARTS": 100,
            "SESSION_PERMANENT": True,
            "PERMANENT_SESSION_LIFETIME": self.session_lifetime_seconds,
            "SESSION_REFRESH_EACH_REQUEST": self.session_refresh_each_request,
            "SESSION_COOKIE_NAME": "__Host-msentra_session" if production else "msentra_session",
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SECURE": self.cookie_secure,
            "SESSION_COOKIE_SAMESITE": self.cookie_samesite,
            "SESSION_COOKIE_PATH": "/",
            "SESSION_COOKIE_DOMAIN": None,
            "WTF_CSRF_ENABLED": self.csrf_enabled,
            "WTF_CSRF_TIME_LIMIT": self.session_lifetime_seconds,
            "MS_ENTRA_CLIENT_ID": self.client_id,
            "MS_ENTRA_CLIENT_SECRET": self.client_secret,
            "MS_ENTRA_TENANT_ID": self.tenant_id,
            "MS_ENTRA_REDIRECT_URI": self.redirect_uri,
            "MS_ENTRA_SCOPES": list(self.scopes),
            "MS_ENTRA_SESSION_NAMESPACE": "msentraauth-flask-template",
            "MS_ENTRA_TOKEN_CACHE_TTL": self.session_lifetime_seconds,
            "MS_ENTRA_IDENTITY_TTL": self.session_lifetime_seconds,
            "MS_ENTRA_FLOW_TTL": min(self.session_lifetime_seconds, 600),
            "MS_ENTRA_REQUIRE_ATOMIC_STORAGE": True,
            "MS_ENTRA_STRICT_SECURITY": production,
            "MS_ENTRA_EVENT_LOGGING": True,
            "MS_ENTRA_REQUEST_ID_HEADER": "X-Request-ID",
            "MS_ENTRA_POST_LOGIN_REDIRECT_URI": "/profile",
            "MS_ENTRA_POST_LOGOUT_REDIRECT_URI": "/logged-out",
            "SEND_FILE_MAX_AGE_DEFAULT": 31536000 if production else 0,
            "TEMPLATES_AUTO_RELOAD": not production,
        }


def _text(values: Mapping[str, str], name: str, default: str | None = None) -> str:
    raw = values.get(name, default)
    if raw is None or not raw.strip():
        raise SettingsError(f"{name} is required")
    value = raw.strip()
    if any(marker in value.lower() for marker in _PLACEHOLDERS):
        raise SettingsError(f"{name} contains a placeholder")
    return value


def _secret(values: Mapping[str, str], name: str, *, minimum: int) -> str:
    value = _text(values, name)
    if len(value) < minimum:
        raise SettingsError(f"{name} must contain at least {minimum} characters")
    return value


def _csv(values: Mapping[str, str], name: str, default: str) -> tuple[str, ...]:
    parts = tuple(
        dict.fromkeys(
            part.strip() for part in _text(values, name, default).split(",") if part.strip()
        )
    )
    if not parts:
        raise SettingsError(f"{name} must contain at least one value")
    return parts


def _boolean(values: Mapping[str, str], name: str, default: bool) -> bool:
    raw = values.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"{name} must be a boolean")


def _positive_int(values: Mapping[str, str], name: str, default: int) -> int:
    value = _non_negative_int(values, name, default)
    if value == 0:
        raise SettingsError(f"{name} must be positive")
    return value


def _bounded_non_negative_int(
    values: Mapping[str, str], name: str, default: int, *, maximum: int
) -> int:
    value = _non_negative_int(values, name, default)
    if value > maximum:
        raise SettingsError(f"{name} cannot exceed {maximum}")
    return value


def _non_negative_int(values: Mapping[str, str], name: str, default: int) -> int:
    raw = values.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be an integer") from exc
    if value < 0:
        raise SettingsError(f"{name} cannot be negative")
    return value


def _positive_float(values: Mapping[str, str], name: str, default: float) -> float:
    raw = values.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be numeric") from exc
    if value <= 0:
        raise SettingsError(f"{name} must be positive")
    return value


def _environment(value: str) -> str:
    return _choice(value.lower(), "APP_ENV", _ENVIRONMENTS)


def _log_level(value: str) -> str:
    return _choice(value.upper(), "APP_LOG_LEVEL", _LOG_LEVELS)


def _choice(value: str, name: str, allowed: frozenset[str]) -> str:
    if value not in allowed:
        options = ", ".join(sorted(allowed))
        raise SettingsError(f"{name} must be one of: {options}")
    return value


def _samesite(value: str) -> str:
    normalized = value.capitalize()
    if normalized not in {"Lax", "Strict", "None"}:
        raise SettingsError("SESSION_COOKIE_SAMESITE must be Lax, Strict, or None")
    return normalized


def _web_url(value: str, name: str) -> str:
    parsed = _parsed_url(value, name, schemes=("https", "http"), allow_credentials=False)
    if parsed.scheme == "http" and not _is_loopback(parsed.hostname):
        raise SettingsError(f"{name} must use HTTPS outside loopback")
    return value


def _https_url(value: str, name: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https":
        raise SettingsError(f"{name} must use HTTPS")
    _parsed_url(value, name, schemes=("https",), allow_credentials=False)
    return value


def _redis_url(value: str, *, tls_required: bool) -> str:
    parsed = _parsed_url(value, "REDIS_URL", schemes=("redis", "rediss"), allow_credentials=True)
    if tls_required and parsed.scheme != "rediss":
        raise SettingsError("REDIS_URL must use rediss when REDIS_TLS_REQUIRED is true")
    return value


def _parsed_url(
    value: str,
    name: str,
    *,
    schemes: tuple[str, ...],
    allow_credentials: bool,
) -> SplitResult:
    parsed = urlsplit(value)
    credentials_present = parsed.username is not None or parsed.password is not None
    if (
        parsed.scheme not in schemes
        or not parsed.hostname
        or (credentials_present and not allow_credentials)
    ):
        raise SettingsError(f"{name} must be an absolute safe URL")
    if parsed.fragment:
        raise SettingsError(f"{name} cannot contain a fragment")
    try:
        parsed_port = parsed.port
    except ValueError as exc:
        raise SettingsError(f"{name} contains an invalid port") from exc
    if parsed_port == 0:
        raise SettingsError(f"{name} contains an invalid port")
    return parsed


def _validate_environment_security(
    *,
    environment: str,
    base_url: str,
    redirect_uri: str,
    trusted_hosts: tuple[str, ...],
    cookie_secure: bool,
    cookie_samesite: str,
) -> None:
    base = urlsplit(base_url)
    redirect = urlsplit(redirect_uri)
    if _origin(base) != _origin(redirect):
        raise SettingsError("MS_ENTRA_REDIRECT_URI must use the same origin as APP_BASE_URL")
    if not any(_trusted_host_matches(base.hostname or "", pattern) for pattern in trusted_hosts):
        raise SettingsError("APP_TRUSTED_HOSTS must include the APP_BASE_URL host")
    if cookie_samesite == "None" and not cookie_secure:
        raise SettingsError("SESSION_COOKIE_SECURE must be true when SameSite=None")
    if environment == "production":
        if base.scheme != "https":
            raise SettingsError("APP_BASE_URL must use HTTPS in production")
        if not cookie_secure:
            raise SettingsError("SESSION_COOKIE_SECURE must be true in production")


def _origin(parsed: SplitResult) -> tuple[str, str, int | None]:
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme.lower() == "https" else 80
    return (parsed.scheme.lower(), (parsed.hostname or "").lower(), port)


def _trusted_host_matches(hostname: str, pattern: str) -> bool:
    normalized_host = hostname.lower().rstrip(".")
    normalized_pattern = pattern.lower().rstrip(".")
    if normalized_pattern.startswith("."):
        suffix = normalized_pattern[1:]
        return normalized_host == suffix or normalized_host.endswith(f".{suffix}")
    return normalized_host == normalized_pattern


def _is_loopback(hostname: str | None) -> bool:
    return hostname in {"localhost", "127.0.0.1", "::1"}


__all__ = ["AppSettings", "ProxyHops", "SettingsError"]
