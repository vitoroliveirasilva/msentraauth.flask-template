from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from flask import Flask, Response, g, request

from ..settings import AppSettings

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
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _safe_message(record),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class TextLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        parts = [
            datetime.now(UTC).isoformat(),
            record.levelname,
            record.name,
            _safe_message(record),
        ]
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                parts.append(
                    f"{field}={json.dumps(value, ensure_ascii=False, separators=(',', ':'))}"
                )
        return " ".join(parts)


def configure_observability(app: Flask, settings: AppSettings) -> None:
    app.logger.setLevel(getattr(logging, settings.log_level))
    formatter: logging.Formatter = (
        JsonLogFormatter() if settings.log_format == "json" else TextLogFormatter()
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
        started = getattr(g, "request_started_at", perf_counter())
        app.logger.info(
            "http request completed",
            extra={
                "request_id": getattr(g, "request_id", None),
                "method": request.method,
                "endpoint": request.endpoint or "unmatched",
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 3),
            },
        )
        response.headers["X-Request-ID"] = getattr(g, "request_id", uuid4().hex)
        return response


def _safe_message(record: logging.LogRecord) -> str:
    try:
        message = record.getMessage()
    except Exception:
        message = "<unformattable log message>"
    return message.replace("\r", "\\r").replace("\n", "\\n")[:4096]


__all__ = ["JsonLogFormatter", "TextLogFormatter", "configure_observability"]
