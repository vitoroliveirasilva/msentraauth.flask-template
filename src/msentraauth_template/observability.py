from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from flask import Flask, Response, g, request

from .settings import AppSettings

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
_EXTRA_FIELDS = (
    "request_id",
    "method",
    "endpoint",
    "status_code",
    "duration_ms",
    "error_type",
    "had_identity",
)


class JsonLogFormatter(logging.Formatter):
    # Gera um JSON estável sem serializar dados de registro arbitrários

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_observability(app: Flask, settings: AppSettings) -> None:
    app.logger.setLevel(getattr(logging, settings.log_level))
    formatter: logging.Formatter
    if settings.log_format == "json":
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    for handler in app.logger.handlers:
        handler.setFormatter(formatter)

    @app.before_request
    def start_request() -> None:
        supplied = request.headers.get("X-Request-ID", "")
        g.request_id = supplied if _REQUEST_ID_RE.fullmatch(supplied) else uuid4().hex
        g.request_started_at = perf_counter()

    @app.after_request
    def finish_request(response: Response) -> Response:
        started_at = getattr(g, "request_started_at", perf_counter())
        duration_ms = (perf_counter() - started_at) * 1000
        app.logger.info(
            "http request completed",
            extra={
                "request_id": getattr(g, "request_id", None),
                "method": request.method,
                "endpoint": request.endpoint or "unmatched",
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 3),
            },
        )
        response.headers["X-Request-ID"] = getattr(g, "request_id", uuid4().hex)
        return response


__all__ = ["JsonLogFormatter", "configure_observability"]
