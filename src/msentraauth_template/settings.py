from __future__ import annotations

import base64
import binascii
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from ipaddress import ip_address
from math import isfinite
from pathlib import Path
from typing import Final
from urllib.parse import SplitResult, parse_qsl, unquote, urlsplit
from uuid import UUID

from redis import Redis

from .session_envelope import SessionEnvelopeCodec

_PLACEHOLDER_VALUES: Final = frozenset(
    {"change-me", "changeme", "replace", "replace-me", "substitua"}
)
_PLACEHOLDER_PREFIXES: Final = (
    "change-me ",
    "change-me-",
    "change-me_",
    "changeme ",
    "changeme-",
    "changeme_",
    "gere uma chave",
    "gere-uma-chave",
    "gere_uma_chave",
    "replace me ",
    "replace me-",
    "replace me_",
    "replace-me ",
    "replace-me-",
    "replace-me_",
    "replace_me ",
    "replace_me-",
    "replace_me_",
    "substitua ",
    "substitua-",
    "substitua_",
)
_ENVIRONMENTS: Final = frozenset({"development", "testing", "production"})
_LOG_LEVELS: Final = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})
_LOG_FORMATS: Final = frozenset({"json", "text"})
_GRAPH_BASE_URLS: Final = frozenset({"https://graph.microsoft.com/v1.0"})
_SINGLE_TENANT_ALIASES: Final = frozenset({"common", "consumers", "organizations"})
_MAX_REDIRECT_URI_LENGTH: Final = 256
_MAX_SECRET_FILE_BYTES: Final = 16 * 1024
_MAX_SECRET_CHARACTERS: Final = 4096
_MAX_SESSION_KEYS: Final = 5
_MAX_REDIS_TIMEOUT_SECONDS: Final = 30.0
_MAX_GRAPH_CONNECT_TIMEOUT_SECONDS: Final = 10.0
_MAX_GRAPH_READ_TIMEOUT_SECONDS: Final = 30.0
_MAX_SESSION_LIFETIME_SECONDS: Final = 86_400
_MAX_SESSION_ABSOLUTE_TIMEOUT_SECONDS: Final = 7 * 86_400
_MAX_SESSION_CLOCK_SKEW_SECONDS: Final = 300
_MAX_SESSION_NAMESPACE_CHARACTERS: Final = 64
_SESSION_NAMESPACE_RE: Final = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
_MAX_REDIS_HEALTH_INTERVAL_SECONDS: Final = 300
_MAX_GRAPH_RESPONSE_BYTES: Final = 256 * 1024
_MAX_GRAPH_RETRIES: Final = 3
_MAX_RETRY_AFTER_SECONDS: Final = 120
_UNSUPPORTED_REDIRECT_URI_CHARACTERS: Final = frozenset("!$'(),;<>\\")
_UNSUPPORTED_ENCODED_SEPARATORS: Final = re.compile(r"%(?:2f|5c|252f|255c)", re.IGNORECASE)
_BASE64URL_RE: Final = re.compile(r"^[A-Za-z0-9_-]+={0,2}$")
_HOST_LABEL_RE: Final = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_REDIS_CONTROLLED_QUERY_OPTIONS: Final = frozenset(
    {
        "decode_responses",
        "encoding",
        "encoding_errors",
        "health_check_interval",
        "socket_connect_timeout",
        "socket_timeout",
        "ssl_cert_reqs",
        "ssl_check_hostname",
    }
)


class SettingsError(ValueError):
    """É gerado quando a configuração do template está ausente ou insegura."""


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
    debug: bool = False
    session_signing_keys: tuple[str, ...] = ()
    csrf_secret_key: str = ""
    graph_max_response_bytes: int = 64 * 1024
    graph_max_retries: int = 2
    graph_max_retry_after_seconds: int = 30
    session_payload_keys: tuple[str, ...] = ()
    session_namespace: str = "msentra-template"
    session_absolute_timeout_seconds: int = 28_800
    session_sid_renewal_seconds: int = 900
    session_clock_skew_seconds: int = 30
    session_activity_update_seconds: int = 60
    session_allowed_keys: tuple[str, ...] = ()
    session_schema_strict: bool = True
    redis_ca_certs_file: str = ""

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> AppSettings:
        values = os.environ if environ is None else environ
        environment = _environment(_text(values, "APP_ENV", default="production"))
        testing = _boolean(values, "TESTING", default=environment == "testing")
        debug = _boolean(values, "DEBUG", default=environment == "development")
        csrf_enabled = _boolean(values, "WTF_CSRF_ENABLED", default=not testing)

        secret_key = _secret_source(
            values,
            "APP_SECRET_KEY",
            minimum=32,
            environment=environment,
            cryptographic=True,
        )
        session_signing_keys = _secret_ring_source(
            values,
            "SESSION_SIGNING_KEYS",
            minimum=32,
            environment=environment,
        )
        csrf_secret_key = _optional_secret_source(
            values,
            "WTF_CSRF_SECRET_KEY",
            minimum=32,
            environment=environment,
            cryptographic=True,
        )
        session_payload_keys = _secret_ring_source(
            values,
            "SESSION_PAYLOAD_KEYS",
            minimum=32,
            environment=environment,
        )

        base_url = _base_url(_text(values, "APP_BASE_URL"))
        trusted_hosts = _trusted_hosts(
            _csv(values, "APP_TRUSTED_HOSTS", default="localhost,127.0.0.1")
        )
        log_level = _log_level(_text(values, "APP_LOG_LEVEL", default="INFO"))
        log_format = _choice(
            _text(
                values,
                "APP_LOG_FORMAT",
                default="json" if environment == "production" else "text",
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
        redirect_uri = _redirect_uri(_text(values, "MS_ENTRA_REDIRECT_URI"))
        redis_tls_required = _boolean(
            values,
            "REDIS_TLS_REQUIRED",
            default=environment == "production",
        )
        redis_url = _redis_url(
            _sensitive_text(values, "REDIS_URL"),
            tls_required=redis_tls_required,
        )
        scopes = _csv(values, "MS_ENTRA_SCOPES", default="User.Read")
        if "User.Read" not in scopes:
            raise SettingsError("MS_ENTRA_SCOPES must include User.Read for the profile route")

        settings = cls(
            environment=environment,
            secret_key=secret_key,
            base_url=base_url,
            trusted_hosts=trusted_hosts,
            log_level=log_level,
            log_format=log_format,
            client_id=_client_id(_text(values, "MS_ENTRA_CLIENT_ID"), environment=environment),
            client_secret=_secret_source(
                values,
                "MS_ENTRA_CLIENT_SECRET",
                minimum=24,
                environment=environment,
                cryptographic=False,
            ),
            tenant_id=_tenant_id(_text(values, "MS_ENTRA_TENANT_ID")),
            redirect_uri=redirect_uri,
            scopes=scopes,
            redis_url=redis_url,
            redis_socket_connect_timeout=_bounded_positive_float(
                values,
                "REDIS_CONNECT_TIMEOUT_SECONDS",
                3.0,
                maximum=_MAX_REDIS_TIMEOUT_SECONDS,
            ),
            redis_socket_timeout=_bounded_positive_float(
                values,
                "REDIS_READ_TIMEOUT_SECONDS",
                3.0,
                maximum=_MAX_REDIS_TIMEOUT_SECONDS,
            ),
            redis_health_check_interval=_bounded_non_negative_int(
                values,
                "REDIS_HEALTH_CHECK_INTERVAL_SECONDS",
                30,
                maximum=_MAX_REDIS_HEALTH_INTERVAL_SECONDS,
            ),
            redis_tls_required=redis_tls_required,
            session_lifetime_seconds=_bounded_positive_int(
                values,
                "SESSION_LIFETIME_SECONDS",
                3600,
                maximum=_MAX_SESSION_LIFETIME_SECONDS,
            ),
            session_refresh_each_request=_boolean(
                values,
                "SESSION_REFRESH_EACH_REQUEST",
                default=True,
            ),
            cookie_secure=cookie_secure,
            cookie_samesite=cookie_samesite,
            graph_base_url=_graph_base_url(
                _text(values, "GRAPH_BASE_URL", default="https://graph.microsoft.com/v1.0")
            ),
            graph_connect_timeout=_bounded_positive_float(
                values,
                "GRAPH_CONNECT_TIMEOUT_SECONDS",
                3.05,
                maximum=_MAX_GRAPH_CONNECT_TIMEOUT_SECONDS,
            ),
            graph_read_timeout=_bounded_positive_float(
                values,
                "GRAPH_READ_TIMEOUT_SECONDS",
                10.0,
                maximum=_MAX_GRAPH_READ_TIMEOUT_SECONDS,
            ),
            proxy_hops=ProxyHops(
                x_for=_bounded_non_negative_int(values, "PROXY_X_FOR", 0, maximum=5),
                x_proto=_bounded_non_negative_int(values, "PROXY_X_PROTO", 0, maximum=5),
                x_host=_bounded_non_negative_int(values, "PROXY_X_HOST", 0, maximum=5),
                x_port=_bounded_non_negative_int(values, "PROXY_X_PORT", 0, maximum=5),
                x_prefix=_bounded_non_negative_int(values, "PROXY_X_PREFIX", 0, maximum=5),
            ),
            testing=testing,
            csrf_enabled=csrf_enabled,
            debug=debug,
            session_signing_keys=session_signing_keys,
            csrf_secret_key=csrf_secret_key,
            graph_max_response_bytes=_bounded_positive_int(
                values,
                "GRAPH_MAX_RESPONSE_BYTES",
                64 * 1024,
                maximum=_MAX_GRAPH_RESPONSE_BYTES,
            ),
            graph_max_retries=_bounded_non_negative_int(
                values,
                "GRAPH_MAX_RETRIES",
                2,
                maximum=_MAX_GRAPH_RETRIES,
            ),
            graph_max_retry_after_seconds=_bounded_positive_int(
                values,
                "GRAPH_MAX_RETRY_AFTER_SECONDS",
                30,
                maximum=_MAX_RETRY_AFTER_SECONDS,
            ),
            session_payload_keys=session_payload_keys,
            session_namespace=_session_namespace(
                _text(values, "SESSION_NAMESPACE", default="msentra-template")
            ),
            session_absolute_timeout_seconds=_bounded_positive_int(
                values,
                "SESSION_ABSOLUTE_TIMEOUT_SECONDS",
                28_800,
                maximum=_MAX_SESSION_ABSOLUTE_TIMEOUT_SECONDS,
            ),
            session_sid_renewal_seconds=_bounded_positive_int(
                values,
                "SESSION_SID_RENEWAL_SECONDS",
                900,
                maximum=_MAX_SESSION_LIFETIME_SECONDS,
            ),
            session_clock_skew_seconds=_bounded_non_negative_int(
                values,
                "SESSION_CLOCK_SKEW_SECONDS",
                30,
                maximum=_MAX_SESSION_CLOCK_SKEW_SECONDS,
            ),
            session_activity_update_seconds=_bounded_positive_int(
                values,
                "SESSION_ACTIVITY_UPDATE_SECONDS",
                60,
                maximum=_MAX_SESSION_LIFETIME_SECONDS,
            ),
            session_allowed_keys=_optional_csv(values, "SESSION_ALLOWED_KEYS"),
            session_schema_strict=_boolean(values, "SESSION_SCHEMA_STRICT", default=True),
            redis_ca_certs_file=_optional_regular_file_path(
                values.get("REDIS_CA_CERTS_FILE", ""),
                "REDIS_CA_CERTS_FILE",
            ),
        )
        settings.validate()
        return settings

    @property
    def effective_session_signing_keys(self) -> tuple[str, ...]:
        return self.session_signing_keys or (self.secret_key,)

    @property
    def effective_csrf_secret_key(self) -> str:
        return self.csrf_secret_key or self.secret_key

    @property
    def effective_session_payload_keys(self) -> tuple[str, ...]:
        return self.session_payload_keys or (self.secret_key,)

    @property
    def session_key_prefix(self) -> str:
        return f"{self.session_namespace}:session:"

    @property
    def auth_storage_key_prefix(self) -> str:
        return f"{self.session_namespace}:auth:"

    @property
    def revocation_key_prefix(self) -> str:
        return f"{self.session_namespace}:revocation:"

    def create_session_codec(self) -> SessionEnvelopeCodec:
        self.validate()
        return SessionEnvelopeCodec(
            self.effective_session_payload_keys,
            namespace=self.session_namespace,
            idle_timeout_seconds=self.session_lifetime_seconds,
            absolute_timeout_seconds=self.session_absolute_timeout_seconds,
            sid_renewal_seconds=self.session_sid_renewal_seconds,
            clock_skew_seconds=self.session_clock_skew_seconds,
            allowed_keys=self.session_allowed_keys,
            strict_schema=self.session_schema_strict,
        )

    def validate(self) -> None:
        """Revalida invariantes ao receber uma instância construída diretamente."""

        environment = _environment(_required_text_value(self.environment, "APP_ENV"))
        _require_canonical(self.environment, environment, "APP_ENV")
        _validate_boolean(self.testing, "TESTING")
        _validate_boolean(self.debug, "DEBUG")
        _validate_boolean(self.csrf_enabled, "WTF_CSRF_ENABLED")

        secret_key = _validate_secret_value(
            self.secret_key,
            "APP_SECRET_KEY",
            minimum=32,
            environment=environment,
            cryptographic=True,
        )
        _require_canonical(self.secret_key, secret_key, "APP_SECRET_KEY")

        session_signing_keys = _validate_secret_ring(
            self.session_signing_keys,
            "SESSION_SIGNING_KEYS",
            minimum=32,
            environment=environment,
            required=environment == "production",
        )
        _require_canonical(self.session_signing_keys, session_signing_keys, "SESSION_SIGNING_KEYS")
        csrf_secret_key = _validate_optional_secret_value(
            self.csrf_secret_key,
            "WTF_CSRF_SECRET_KEY",
            minimum=32,
            environment=environment,
            cryptographic=True,
            required=environment == "production",
        )
        _require_canonical(self.csrf_secret_key, csrf_secret_key, "WTF_CSRF_SECRET_KEY")
        session_payload_keys = _validate_secret_ring(
            self.session_payload_keys,
            "SESSION_PAYLOAD_KEYS",
            minimum=32,
            environment=environment,
            required=environment == "production",
        )
        _require_canonical(self.session_payload_keys, session_payload_keys, "SESSION_PAYLOAD_KEYS")

        base_url = _base_url(_required_text_value(self.base_url, "APP_BASE_URL"))
        _require_canonical(self.base_url, base_url, "APP_BASE_URL")
        trusted_hosts = _trusted_hosts(
            _validate_string_values(self.trusted_hosts, "APP_TRUSTED_HOSTS")
        )
        _require_canonical(self.trusted_hosts, trusted_hosts, "APP_TRUSTED_HOSTS")
        log_level = _log_level(_required_text_value(self.log_level, "APP_LOG_LEVEL"))
        _require_canonical(self.log_level, log_level, "APP_LOG_LEVEL")
        log_format = _choice(
            _required_text_value(self.log_format, "APP_LOG_FORMAT"),
            "APP_LOG_FORMAT",
            _LOG_FORMATS,
        )
        _require_canonical(self.log_format, log_format, "APP_LOG_FORMAT")

        client_id = _client_id(
            _required_text_value(self.client_id, "MS_ENTRA_CLIENT_ID"),
            environment=environment,
        )
        _require_canonical(self.client_id, client_id, "MS_ENTRA_CLIENT_ID")
        client_secret = _validate_secret_value(
            self.client_secret,
            "MS_ENTRA_CLIENT_SECRET",
            minimum=24,
            environment=environment,
            cryptographic=False,
        )
        _require_canonical(self.client_secret, client_secret, "MS_ENTRA_CLIENT_SECRET")
        tenant_id = _tenant_id(_required_text_value(self.tenant_id, "MS_ENTRA_TENANT_ID"))
        _require_canonical(self.tenant_id, tenant_id, "MS_ENTRA_TENANT_ID")
        redirect_uri = _redirect_uri(
            _required_text_value(self.redirect_uri, "MS_ENTRA_REDIRECT_URI")
        )
        _require_canonical(self.redirect_uri, redirect_uri, "MS_ENTRA_REDIRECT_URI")
        scopes = _validate_string_values(self.scopes, "MS_ENTRA_SCOPES")
        _require_canonical(self.scopes, scopes, "MS_ENTRA_SCOPES")
        if "User.Read" not in scopes:
            raise SettingsError("MS_ENTRA_SCOPES must include User.Read for the profile route")

        _validate_boolean(self.redis_tls_required, "REDIS_TLS_REQUIRED")
        redis_url = _redis_url(
            _required_text_value(self.redis_url, "REDIS_URL"),
            tls_required=self.redis_tls_required,
        )
        _require_canonical(self.redis_url, redis_url, "REDIS_URL")
        _validate_bounded_positive_float(
            self.redis_socket_connect_timeout,
            "REDIS_CONNECT_TIMEOUT_SECONDS",
            maximum=_MAX_REDIS_TIMEOUT_SECONDS,
        )
        _validate_bounded_positive_float(
            self.redis_socket_timeout,
            "REDIS_READ_TIMEOUT_SECONDS",
            maximum=_MAX_REDIS_TIMEOUT_SECONDS,
        )
        _validate_bounded_non_negative_int(
            self.redis_health_check_interval,
            "REDIS_HEALTH_CHECK_INTERVAL_SECONDS",
            maximum=_MAX_REDIS_HEALTH_INTERVAL_SECONDS,
        )
        _validate_bounded_positive_int(
            self.session_lifetime_seconds,
            "SESSION_LIFETIME_SECONDS",
            maximum=_MAX_SESSION_LIFETIME_SECONDS,
        )
        _validate_boolean(self.session_refresh_each_request, "SESSION_REFRESH_EACH_REQUEST")
        _validate_bounded_positive_int(
            self.session_absolute_timeout_seconds,
            "SESSION_ABSOLUTE_TIMEOUT_SECONDS",
            maximum=_MAX_SESSION_ABSOLUTE_TIMEOUT_SECONDS,
        )
        _validate_bounded_positive_int(
            self.session_sid_renewal_seconds,
            "SESSION_SID_RENEWAL_SECONDS",
            maximum=_MAX_SESSION_LIFETIME_SECONDS,
        )
        _validate_bounded_non_negative_int(
            self.session_clock_skew_seconds,
            "SESSION_CLOCK_SKEW_SECONDS",
            maximum=_MAX_SESSION_CLOCK_SKEW_SECONDS,
        )
        _validate_bounded_positive_int(
            self.session_activity_update_seconds,
            "SESSION_ACTIVITY_UPDATE_SECONDS",
            maximum=_MAX_SESSION_LIFETIME_SECONDS,
        )
        if self.session_absolute_timeout_seconds < self.session_lifetime_seconds:
            raise SettingsError(
                "SESSION_ABSOLUTE_TIMEOUT_SECONDS cannot be shorter than "
                "SESSION_LIFETIME_SECONDS"
            )
        if self.session_sid_renewal_seconds >= self.session_absolute_timeout_seconds:
            raise SettingsError(
                "SESSION_SID_RENEWAL_SECONDS must be shorter than the absolute timeout"
            )
        if self.session_activity_update_seconds > self.session_lifetime_seconds:
            raise SettingsError("SESSION_ACTIVITY_UPDATE_SECONDS cannot exceed the idle timeout")
        namespace = _session_namespace(self.session_namespace)
        _require_canonical(self.session_namespace, namespace, "SESSION_NAMESPACE")
        allowed_keys = _validate_optional_string_values(
            self.session_allowed_keys,
            "SESSION_ALLOWED_KEYS",
        )
        _require_canonical(self.session_allowed_keys, allowed_keys, "SESSION_ALLOWED_KEYS")
        _validate_boolean(self.session_schema_strict, "SESSION_SCHEMA_STRICT")
        ca_file = _optional_regular_file_path(self.redis_ca_certs_file, "REDIS_CA_CERTS_FILE")
        _require_canonical(self.redis_ca_certs_file, ca_file, "REDIS_CA_CERTS_FILE")
        _validate_boolean(self.cookie_secure, "SESSION_COOKIE_SECURE")
        cookie_samesite = _samesite(
            _required_text_value(self.cookie_samesite, "SESSION_COOKIE_SAMESITE")
        )
        _require_canonical(self.cookie_samesite, cookie_samesite, "SESSION_COOKIE_SAMESITE")

        graph_base_url = _graph_base_url(
            _required_text_value(self.graph_base_url, "GRAPH_BASE_URL")
        )
        _require_canonical(self.graph_base_url, graph_base_url, "GRAPH_BASE_URL")
        _validate_bounded_positive_float(
            self.graph_connect_timeout,
            "GRAPH_CONNECT_TIMEOUT_SECONDS",
            maximum=_MAX_GRAPH_CONNECT_TIMEOUT_SECONDS,
        )
        _validate_bounded_positive_float(
            self.graph_read_timeout,
            "GRAPH_READ_TIMEOUT_SECONDS",
            maximum=_MAX_GRAPH_READ_TIMEOUT_SECONDS,
        )
        _validate_bounded_positive_int(
            self.graph_max_response_bytes,
            "GRAPH_MAX_RESPONSE_BYTES",
            maximum=_MAX_GRAPH_RESPONSE_BYTES,
        )
        _validate_bounded_non_negative_int(
            self.graph_max_retries,
            "GRAPH_MAX_RETRIES",
            maximum=_MAX_GRAPH_RETRIES,
        )
        _validate_bounded_positive_int(
            self.graph_max_retry_after_seconds,
            "GRAPH_MAX_RETRY_AFTER_SECONDS",
            maximum=_MAX_RETRY_AFTER_SECONDS,
        )
        _validate_proxy_hops(self.proxy_hops)

        _validate_environment_security(
            environment=environment,
            base_url=base_url,
            redirect_uri=redirect_uri,
            trusted_hosts=trusted_hosts,
            cookie_secure=self.cookie_secure,
            cookie_samesite=cookie_samesite,
            redis_tls_required=self.redis_tls_required,
            testing=self.testing,
            debug=self.debug,
            csrf_enabled=self.csrf_enabled,
            secret_key=secret_key,
            session_signing_keys=self.effective_session_signing_keys,
            csrf_secret_key=self.effective_csrf_secret_key,
            client_secret=client_secret,
            session_payload_keys=self.effective_session_payload_keys,
            session_namespace=self.session_namespace,
            session_schema_strict=self.session_schema_strict,
            redis_ca_certs_file=self.redis_ca_certs_file,
        )

    def create_redis_client(self) -> Redis:
        self.validate()
        connection_options: dict[str, object] = {
            "decode_responses": False,
            "socket_connect_timeout": self.redis_socket_connect_timeout,
            "socket_timeout": self.redis_socket_timeout,
            "health_check_interval": self.redis_health_check_interval,
        }
        if self.redis_tls_required:
            connection_options.update(
                ssl_cert_reqs="required",
                ssl_check_hostname=True,
            )
            if self.redis_ca_certs_file:
                connection_options["ssl_ca_certs"] = self.redis_ca_certs_file
        return Redis.from_url(self.redis_url, **connection_options)

    def flask_config(self) -> dict[str, object]:
        self.validate()
        production = self.environment == "production"
        return {
            "ENV": self.environment,
            "TESTING": self.testing,
            "DEBUG": self.debug,
            "SECRET_KEY": self.secret_key,
            "SESSION_SIGNING_KEYS": self.effective_session_signing_keys,
            "SESSION_PAYLOAD_KEYS": self.effective_session_payload_keys,
            "SESSION_NAMESPACE": self.session_namespace,
            "SESSION_IDLE_TIMEOUT_SECONDS": self.session_lifetime_seconds,
            "SESSION_ABSOLUTE_TIMEOUT_SECONDS": self.session_absolute_timeout_seconds,
            "SESSION_SID_RENEWAL_SECONDS": self.session_sid_renewal_seconds,
            "SESSION_CLOCK_SKEW_SECONDS": self.session_clock_skew_seconds,
            "SESSION_ACTIVITY_UPDATE_SECONDS": self.session_activity_update_seconds,
            "SESSION_ALLOWED_KEYS": self.session_allowed_keys,
            "SESSION_SCHEMA_STRICT": self.session_schema_strict,
            "WTF_CSRF_SECRET_KEY": self.effective_csrf_secret_key,
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
            "MS_ENTRA_SESSION_NAMESPACE": self.session_namespace,
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


def _require_canonical(actual: object, canonical: object, name: str) -> None:
    if actual != canonical:
        raise SettingsError(f"{name} must use its normalized form")


def _required_text_value(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SettingsError(f"{name} is required")
    normalized = value.strip()
    if _contains_placeholder(normalized):
        raise SettingsError(f"{name} contains a placeholder")
    _reject_control_characters(normalized, name)
    return normalized


def _contains_placeholder(value: str) -> bool:
    normalized = value.casefold()
    return normalized in _PLACEHOLDER_VALUES or normalized.startswith(_PLACEHOLDER_PREFIXES)


def _text(values: Mapping[str, str], name: str, default: str | None = None) -> str:
    raw = values.get(name, default)
    if raw is None or not raw.strip():
        raise SettingsError(f"{name} is required")
    return _required_text_value(raw, name)


def _sensitive_text(values: Mapping[str, str], name: str) -> str:
    return _secret_source_raw(values, name, required=True)


def _secret_source(
    values: Mapping[str, str],
    name: str,
    *,
    minimum: int,
    environment: str,
    cryptographic: bool,
) -> str:
    value = _secret_source_raw(values, name, required=True)
    return _validate_secret_value(
        value,
        name,
        minimum=minimum,
        environment=environment,
        cryptographic=cryptographic,
    )


def _optional_secret_source(
    values: Mapping[str, str],
    name: str,
    *,
    minimum: int,
    environment: str,
    cryptographic: bool,
) -> str:
    value = _secret_source_raw(values, name, required=False)
    if not value:
        return ""
    return _validate_secret_value(
        value,
        name,
        minimum=minimum,
        environment=environment,
        cryptographic=cryptographic,
    )


def _secret_source_raw(values: Mapping[str, str], name: str, *, required: bool) -> str:
    direct = values.get(name)
    file_name = f"{name}_FILE"
    file_value = values.get(file_name)
    if direct is not None and direct.strip() and file_value is not None and file_value.strip():
        raise SettingsError(f"{name} and {file_name} cannot be configured together")
    if file_value is not None and file_value.strip():
        return _read_secret_file(file_value.strip(), file_name)
    if direct is not None and direct.strip():
        return _required_text_value(direct, name)
    if required:
        raise SettingsError(f"{name} is required")
    return ""


def _read_secret_file(file_name: str, setting_name: str) -> str:
    path = Path(file_name)
    if not path.is_absolute():
        raise SettingsError(f"{setting_name} must be an absolute path")
    try:
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > _MAX_SECRET_FILE_BYTES:
            raise SettingsError(f"{setting_name} must reference a small regular file")
        raw = path.read_bytes()
    except SettingsError:
        raise
    except OSError as exc:
        raise SettingsError(f"{setting_name} could not be read") from exc
    try:
        value = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SettingsError(f"{setting_name} must contain UTF-8 text") from exc
    value = value.rstrip("\r\n")
    if not value:
        raise SettingsError(f"{setting_name} is empty")
    return value


def _secret_ring_source(
    values: Mapping[str, str],
    name: str,
    *,
    minimum: int,
    environment: str,
) -> tuple[str, ...]:
    raw = _secret_source_raw(values, name, required=environment == "production")
    if not raw:
        return ()
    parts = tuple(part.strip() for part in re.split(r"[,\r\n]+", raw) if part.strip())
    return _validate_secret_ring(
        parts,
        name,
        minimum=minimum,
        environment=environment,
        required=environment == "production",
    )


def _validate_secret_ring(
    values: object,
    name: str,
    *,
    minimum: int,
    environment: str,
    required: bool,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise SettingsError(f"{name} must contain an ordered key ring")
    normalized = tuple(
        _validate_secret_value(
            value,
            name,
            minimum=minimum,
            environment=environment,
            cryptographic=True,
        )
        for value in values
    )
    if required and not normalized:
        raise SettingsError(f"{name} is required in production")
    if len(normalized) > _MAX_SESSION_KEYS:
        raise SettingsError(f"{name} cannot contain more than {_MAX_SESSION_KEYS} keys")
    if len(set(normalized)) != len(normalized):
        raise SettingsError(f"{name} cannot contain duplicate keys")
    return normalized


def _validate_optional_secret_value(
    value: object,
    name: str,
    *,
    minimum: int,
    environment: str,
    cryptographic: bool,
    required: bool,
) -> str:
    if value == "" and not required:
        return ""
    if value == "" and required:
        raise SettingsError(f"{name} is required in production")
    return _validate_secret_value(
        value,
        name,
        minimum=minimum,
        environment=environment,
        cryptographic=cryptographic,
    )


def _validate_secret_value(
    value: object,
    name: str,
    *,
    minimum: int,
    environment: str,
    cryptographic: bool,
) -> str:
    normalized = _required_text_value(value, name)
    if len(normalized) < minimum:
        raise SettingsError(f"{name} must contain at least {minimum} characters")
    if len(normalized) > _MAX_SECRET_CHARACTERS:
        raise SettingsError(f"{name} is too long")
    if environment == "production" and cryptographic:
        _validate_base64url_secret(normalized, name)
    if environment == "production" and not cryptographic:
        if len(set(normalized)) < 8:
            raise SettingsError(f"{name} does not have enough character diversity")
    return normalized


def _validate_base64url_secret(value: str, name: str) -> None:
    if not _BASE64URL_RE.fullmatch(value):
        raise SettingsError(f"{name} must be URL-safe base64 in production")
    try:
        padded = value + ("=" * (-len(value) % 4))
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise SettingsError(f"{name} must be URL-safe base64 in production") from exc
    if len(decoded) < 32:
        raise SettingsError(f"{name} must encode at least 32 random bytes in production")


def _validate_string_values(values: object, name: str) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise SettingsError(f"{name} must contain at least one value")
    normalized = tuple(dict.fromkeys(_required_text_value(value, name) for value in values))
    if not normalized:
        raise SettingsError(f"{name} must contain at least one value")
    return normalized


def _csv(values: Mapping[str, str], name: str, default: str) -> tuple[str, ...]:
    parts = tuple(
        dict.fromkeys(
            part.strip() for part in _text(values, name, default).split(",") if part.strip()
        )
    )
    if not parts:
        raise SettingsError(f"{name} must contain at least one value")
    return parts


def _optional_csv(values: Mapping[str, str], name: str) -> tuple[str, ...]:
    raw = values.get(name, "").strip()
    if not raw:
        return ()
    return _validate_optional_string_values(
        tuple(part.strip() for part in raw.split(",") if part.strip()),
        name,
    )


def _validate_optional_string_values(values: object, name: str) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise SettingsError(f"{name} must be a list of values")
    normalized = tuple(dict.fromkeys(_required_text_value(value, name) for value in values))
    return normalized


def _session_namespace(value: str) -> str:
    normalized = _required_text_value(value, "SESSION_NAMESPACE")
    if (
        len(normalized) > _MAX_SESSION_NAMESPACE_CHARACTERS
        or not _SESSION_NAMESPACE_RE.fullmatch(normalized)
    ):
        raise SettingsError("SESSION_NAMESPACE contains unsupported characters")
    return normalized


def _optional_regular_file_path(value: object, name: str) -> str:
    if value == "":
        return ""
    if not isinstance(value, str) or not value.strip():
        raise SettingsError(f"{name} must be an absolute regular file path")
    normalized = value.strip()
    path = Path(normalized)
    if not path.is_absolute():
        raise SettingsError(f"{name} must be an absolute path")
    try:
        metadata = path.stat()
    except OSError as exc:
        raise SettingsError(f"{name} could not be read") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise SettingsError(f"{name} must reference a regular file")
    return normalized


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


def _validate_boolean(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise SettingsError(f"{name} must be a boolean")


def _bounded_positive_int(
    values: Mapping[str, str],
    name: str,
    default: int,
    *,
    maximum: int,
) -> int:
    value = _bounded_non_negative_int(values, name, default, maximum=maximum)
    if value == 0:
        raise SettingsError(f"{name} must be positive")
    return value


def _bounded_non_negative_int(
    values: Mapping[str, str],
    name: str,
    default: int,
    *,
    maximum: int,
) -> int:
    raw = values.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be an integer") from exc
    _validate_bounded_non_negative_int(value, name, maximum=maximum)
    return value


def _validate_bounded_non_negative_int(value: object, name: str, *, maximum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SettingsError(f"{name} must be an integer")
    if value < 0:
        raise SettingsError(f"{name} cannot be negative")
    if value > maximum:
        raise SettingsError(f"{name} cannot exceed {maximum}")


def _validate_bounded_positive_int(value: object, name: str, *, maximum: int) -> None:
    _validate_bounded_non_negative_int(value, name, maximum=maximum)
    if value == 0:
        raise SettingsError(f"{name} must be positive")


def _bounded_positive_float(
    values: Mapping[str, str],
    name: str,
    default: float,
    *,
    maximum: float,
) -> float:
    raw = values.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise SettingsError(f"{name} must be numeric") from exc
    _validate_bounded_positive_float(value, name, maximum=maximum)
    return value


def _validate_bounded_positive_float(value: object, name: str, *, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SettingsError(f"{name} must be numeric")
    normalized = float(value)
    if not isfinite(normalized):
        raise SettingsError(f"{name} must be finite")
    if normalized <= 0:
        raise SettingsError(f"{name} must be positive")
    if normalized > maximum:
        raise SettingsError(f"{name} cannot exceed {maximum:g}")


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


def _base_url(value: str) -> str:
    name = "APP_BASE_URL"
    parsed = _web_url(value, name)
    if parsed.query:
        raise SettingsError(f"{name} cannot contain a query")
    if parsed.path not in {"", "/"}:
        raise SettingsError(f"{name} must contain only the origin, without a path")
    return _canonical_origin(parsed)


def _redirect_uri(value: str) -> str:
    name = "MS_ENTRA_REDIRECT_URI"
    if len(value) > _MAX_REDIRECT_URI_LENGTH:
        raise SettingsError(f"{name} cannot exceed {_MAX_REDIRECT_URI_LENGTH} characters")
    if _UNSUPPORTED_ENCODED_SEPARATORS.search(value):
        raise SettingsError(f"{name} cannot contain encoded path separators")
    decoded = _decode_url_layers(value, name)
    if any(character in decoded for character in _UNSUPPORTED_REDIRECT_URI_CHARACTERS):
        raise SettingsError(f"{name} contains an unsupported character")
    parsed = _web_url(value, name)
    if parsed.query:
        raise SettingsError(f"{name} cannot contain a query")
    path = parsed.path
    if not path.startswith("/") or path == "/" or path.endswith("/"):
        raise SettingsError(f"{name} must use a non-root static callback path")
    if "//" in path or any(segment in {".", ".."} for segment in path.split("/")):
        raise SettingsError(f"{name} contains an ambiguous path")
    return value


def _graph_base_url(value: str) -> str:
    name = "GRAPH_BASE_URL"
    parsed = _https_url(value, name)
    if parsed.query:
        raise SettingsError(f"{name} cannot contain a query")
    canonical = value.rstrip("/")
    if canonical not in _GRAPH_BASE_URLS:
        raise SettingsError(f"{name} must use an approved Microsoft Graph endpoint")
    return canonical


def _web_url(value: str, name: str) -> SplitResult:
    decoded = _decode_url_layers(value, name)
    if "\\" in decoded:
        raise SettingsError(f"{name} cannot contain a backslash")
    parsed = _parsed_url(value, name, schemes=("https", "http"), allow_credentials=False)
    if parsed.scheme == "http" and not _is_loopback(parsed.hostname):
        raise SettingsError(f"{name} must use HTTPS outside loopback")
    _canonical_hostname(parsed.hostname or "", name)
    return parsed


def _https_url(value: str, name: str) -> SplitResult:
    if urlsplit(value).scheme != "https":
        raise SettingsError(f"{name} must use HTTPS")
    parsed = _parsed_url(value, name, schemes=("https",), allow_credentials=False)
    _canonical_hostname(parsed.hostname or "", name)
    return parsed


def _parsed_url(
    value: str,
    name: str,
    *,
    schemes: tuple[str, ...],
    allow_credentials: bool,
) -> SplitResult:
    _decode_url_layers(value, name)
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


def _decode_url_layers(value: str, name: str) -> str:
    decoded = value
    for _ in range(3):
        _reject_control_characters(decoded, name)
        next_value = unquote(decoded)
        if next_value == decoded:
            return decoded
        decoded = next_value
    _reject_control_characters(decoded, name)
    if unquote(decoded) != decoded:
        raise SettingsError(f"{name} contains excessive percent encoding")
    return decoded


def _reject_control_characters(value: str, name: str) -> None:
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise SettingsError(f"{name} contains a control character")


def _canonical_origin(parsed: SplitResult) -> str:
    hostname = _canonical_hostname(parsed.hostname or "", "APP_BASE_URL")
    host = f"[{hostname}]" if ":" in hostname and not hostname.startswith("[") else hostname
    default_port = 443 if parsed.scheme == "https" else 80
    port = parsed.port
    authority = host if port is None or port == default_port else f"{host}:{port}"
    return f"{parsed.scheme}://{authority}"


def _trusted_hosts(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        name = "APP_TRUSTED_HOSTS"
        if value == "*" or value.startswith(".") or "*" in value:
            raise SettingsError(f"{name} cannot contain wildcards or suffix patterns")
        if "://" in value or "/" in value or "@" in value or "?" in value or "#" in value:
            raise SettingsError(f"{name} must contain host names only")
        host = value
        port: int | None = None
        if value.startswith("["):
            closing = value.find("]")
            if closing < 0:
                raise SettingsError(f"{name} contains an invalid IPv6 host")
            host = value[1:closing]
            suffix = value[closing + 1 :]
            if suffix:
                if not suffix.startswith(":") or not suffix[1:].isdigit():
                    raise SettingsError(f"{name} contains an invalid port")
                port = int(suffix[1:])
        elif value.count(":") == 1:
            candidate_host, candidate_port = value.rsplit(":", 1)
            if candidate_port.isdigit():
                host = candidate_host
                port = int(candidate_port)
        if port is not None and not 1 <= port <= 65_535:
            raise SettingsError(f"{name} contains an invalid port")
        canonical_host = _canonical_hostname(host, name)
        rendered = f"[{canonical_host}]" if ":" in canonical_host else canonical_host
        if port is not None:
            rendered = f"{rendered}:{port}"
        if rendered not in normalized:
            normalized.append(rendered)
    if not normalized:
        raise SettingsError("APP_TRUSTED_HOSTS must contain at least one value")
    return tuple(normalized)


def _canonical_hostname(hostname: str, name: str) -> str:
    normalized = hostname.lower().rstrip(".")
    if not normalized:
        raise SettingsError(f"{name} contains an invalid host")
    try:
        return ip_address(normalized).compressed
    except ValueError:
        pass
    try:
        ascii_host = normalized.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise SettingsError(f"{name} contains an invalid host") from exc
    if len(ascii_host) > 253 or any(
        not _HOST_LABEL_RE.fullmatch(label) for label in ascii_host.split(".")
    ):
        raise SettingsError(f"{name} contains an invalid host")
    return ascii_host


def _client_id(value: str, *, environment: str) -> str:
    normalized = _required_text_value(value, "MS_ENTRA_CLIENT_ID")
    try:
        return str(UUID(normalized))
    except ValueError as exc:
        if environment != "production":
            return normalized
        raise SettingsError("MS_ENTRA_CLIENT_ID must be a UUID in production") from exc


def _tenant_id(value: str) -> str:
    normalized = _required_text_value(value, "MS_ENTRA_TENANT_ID").lower()
    if normalized in _SINGLE_TENANT_ALIASES:
        raise SettingsError("MS_ENTRA_TENANT_ID must identify one tenant")
    try:
        return str(UUID(normalized))
    except ValueError:
        if "://" in normalized or "/" in normalized or "@" in normalized:
            raise SettingsError("MS_ENTRA_TENANT_ID must be a tenant UUID or verified domain")
        return _canonical_hostname(normalized, "MS_ENTRA_TENANT_ID")


def _redis_url(value: str, *, tls_required: bool) -> str:
    parsed = _parsed_url(value, "REDIS_URL", schemes=("redis", "rediss"), allow_credentials=True)
    controlled_options = {
        name.casefold()
        for name, _ in parse_qsl(parsed.query, keep_blank_values=True)
        if name.casefold() in _REDIS_CONTROLLED_QUERY_OPTIONS
    }
    if controlled_options:
        names = ", ".join(sorted(controlled_options))
        raise SettingsError(f"REDIS_URL cannot override application-controlled options: {names}")
    if tls_required and parsed.scheme != "rediss":
        raise SettingsError("REDIS_URL must use rediss when REDIS_TLS_REQUIRED is true")
    return value


def _validate_proxy_hops(proxy_hops: object) -> None:
    if not isinstance(proxy_hops, ProxyHops):
        raise SettingsError("proxy_hops must be ProxyHops")
    for name, value in (
        ("PROXY_X_FOR", proxy_hops.x_for),
        ("PROXY_X_PROTO", proxy_hops.x_proto),
        ("PROXY_X_HOST", proxy_hops.x_host),
        ("PROXY_X_PORT", proxy_hops.x_port),
        ("PROXY_X_PREFIX", proxy_hops.x_prefix),
    ):
        _validate_bounded_non_negative_int(value, name, maximum=5)


def _validate_environment_security(
    *,
    environment: str,
    base_url: str,
    redirect_uri: str,
    trusted_hosts: tuple[str, ...],
    cookie_secure: bool,
    cookie_samesite: str,
    redis_tls_required: bool,
    testing: bool,
    debug: bool,
    csrf_enabled: bool,
    secret_key: str,
    session_signing_keys: tuple[str, ...],
    csrf_secret_key: str,
    client_secret: str,
    session_payload_keys: tuple[str, ...],
    session_namespace: str,
    session_schema_strict: bool,
    redis_ca_certs_file: str,
) -> None:
    base = urlsplit(base_url)
    redirect = urlsplit(redirect_uri)
    if _origin(base) != _origin(redirect):
        raise SettingsError("MS_ENTRA_REDIRECT_URI must use the same origin as APP_BASE_URL")
    base_host = _render_host_for_trust(base)
    canonical_hostname = _canonical_hostname(base.hostname or "", "APP_BASE_URL")
    host_without_port = (
        f"[{canonical_hostname}]" if ":" in canonical_hostname else canonical_hostname
    )
    if not {base_host, host_without_port}.intersection(trusted_hosts):
        raise SettingsError("APP_TRUSTED_HOSTS must include the APP_BASE_URL host")
    if cookie_samesite == "None" and not cookie_secure:
        raise SettingsError("SESSION_COOKIE_SECURE must be true when SameSite=None")
    if environment == "production":
        if base.scheme != "https":
            raise SettingsError("APP_BASE_URL must use HTTPS in production")
        if not cookie_secure:
            raise SettingsError("SESSION_COOKIE_SECURE must be true in production")
        if not redis_tls_required:
            raise SettingsError("REDIS_TLS_REQUIRED must be true in production")
        if testing:
            raise SettingsError("TESTING must be false in production")
        if debug:
            raise SettingsError("DEBUG must be false in production")
        if not csrf_enabled:
            raise SettingsError("WTF_CSRF_ENABLED must be true in production")
        independent = (
            secret_key,
            csrf_secret_key,
            client_secret,
            *session_signing_keys,
            *session_payload_keys,
        )
        if len(set(independent)) != len(independent):
            raise SettingsError("production secrets must use independent values")
        if session_namespace == "msentra-template":
            raise SettingsError(
                "SESSION_NAMESPACE must be unique per application and environment in production"
            )
        if not session_schema_strict:
            raise SettingsError("SESSION_SCHEMA_STRICT must be true in production")
        if redis_tls_required and redis_ca_certs_file and not Path(redis_ca_certs_file).is_file():
            raise SettingsError("REDIS_CA_CERTS_FILE must reference a readable regular file")


def _render_host_for_trust(parsed: SplitResult) -> str:
    hostname = _canonical_hostname(parsed.hostname or "", "APP_BASE_URL")
    rendered = f"[{hostname}]" if ":" in hostname else hostname
    default_port = 443 if parsed.scheme == "https" else 80
    if parsed.port is not None and parsed.port != default_port:
        return f"{rendered}:{parsed.port}"
    return rendered


def _origin(parsed: SplitResult) -> tuple[str, str, int]:
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme.lower() == "https" else 80
    return (parsed.scheme.lower(), _canonical_hostname(parsed.hostname or "", "URL"), port)


def _is_loopback(hostname: str | None) -> bool:
    normalized = (hostname or "").lower().rstrip(".")
    if normalized == "localhost":
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


__all__ = ["AppSettings", "ProxyHops", "SettingsError"]
