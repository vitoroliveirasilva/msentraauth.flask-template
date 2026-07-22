from __future__ import annotations

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


port = _integer_setting("PORT", 8000, minimum=1, maximum=65_535)
bind = f"0.0.0.0:{port}"
workers = _integer_setting("WEB_CONCURRENCY", 2, minimum=1, maximum=1024)
threads = _integer_setting("GUNICORN_THREADS", 4, minimum=1, maximum=1024)
worker_class = "gthread"
timeout = _integer_setting("GUNICORN_TIMEOUT", 30, minimum=1, maximum=3600)
graceful_timeout = _integer_setting(
    "GUNICORN_GRACEFUL_TIMEOUT", 30, minimum=1, maximum=3600
)
keepalive = _integer_setting("GUNICORN_KEEPALIVE", 5, minimum=0, maximum=300)
max_requests = _integer_setting(
    "GUNICORN_MAX_REQUESTS", 1000, minimum=0, maximum=10_000_000
)
max_requests_jitter = _integer_setting(
    "GUNICORN_MAX_REQUESTS_JITTER",
    100,
    minimum=0,
    maximum=1_000_000,
)
worker_tmp_dir = "/dev/shm"
accesslog = "-"
# Do not use %(r)s here: OAuth callbacks carry code/state in the query string
access_log_format = '%(h)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s %(L)s'
errorlog = "-"
capture_output = True
