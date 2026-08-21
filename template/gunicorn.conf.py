from __future__ import annotations

import ipaddress
import os


def _integer_setting(
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{name} must be between {minimum} and {maximum}")
    return value


def _forwarded_allow_ips() -> str:
    raw = os.getenv("GUNICORN_FORWARDED_ALLOW_IPS", "127.0.0.1,::1")
    values = [item.strip() for item in raw.split(",")]
    if not values or len(values) > 16 or any(not value for value in values):
        raise RuntimeError("GUNICORN_FORWARDED_ALLOW_IPS must contain 1 to 16 IP addresses")
    normalized: list[str] = []
    for value in values:
        if value == "*":
            raise RuntimeError("GUNICORN_FORWARDED_ALLOW_IPS cannot trust every source")
        try:
            normalized.append(str(ipaddress.ip_address(value)))
        except ValueError as exc:
            raise RuntimeError("GUNICORN_FORWARDED_ALLOW_IPS contains an invalid IP") from exc
    if len(set(normalized)) != len(normalized):
        raise RuntimeError("GUNICORN_FORWARDED_ALLOW_IPS contains duplicate IPs")
    return ",".join(normalized)


port = _integer_setting("PORT", 8000, minimum=1, maximum=65_535)
bind = f"0.0.0.0:{port}"
workers = _integer_setting("WEB_CONCURRENCY", 2, minimum=1, maximum=32)
threads = _integer_setting("GUNICORN_THREADS", 4, minimum=1, maximum=32)
worker_class = "gthread"
timeout = _integer_setting("GUNICORN_TIMEOUT", 30, minimum=5, maximum=120)
graceful_timeout = _integer_setting("GUNICORN_GRACEFUL_TIMEOUT", 30, minimum=5, maximum=120)
keepalive = _integer_setting("GUNICORN_KEEPALIVE", 5, minimum=0, maximum=15)
max_requests = _integer_setting("GUNICORN_MAX_REQUESTS", 1000, minimum=100, maximum=100_000)
max_requests_jitter = _integer_setting(
    "GUNICORN_MAX_REQUESTS_JITTER", 100, minimum=0, maximum=10_000
)
backlog = _integer_setting("GUNICORN_BACKLOG", 1024, minimum=64, maximum=4096)
limit_request_line = _integer_setting(
    "GUNICORN_LIMIT_REQUEST_LINE", 4094, minimum=256, maximum=8190
)
limit_request_fields = _integer_setting(
    "GUNICORN_LIMIT_REQUEST_FIELDS", 100, minimum=16, maximum=100
)
limit_request_field_size = _integer_setting(
    "GUNICORN_LIMIT_REQUEST_FIELD_SIZE", 8190, minimum=1024, maximum=8190
)
forwarded_allow_ips = _forwarded_allow_ips()
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
worker_tmp_dir = "/dev/shm"
accesslog = "-"
# Query strings, cookies, forwarded headers and raw client IPs are intentionally omitted.
access_log_format = '%(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s %(L)s request_id=%({x-request-id}o)s'
errorlog = "-"
capture_output = False
disable_redirect_access_to_syslog = True
