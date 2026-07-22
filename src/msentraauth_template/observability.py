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
_MAX_LOG_MESSAGE_LENGTH = 4096
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
            "message": _safe_message(record),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        exception_type = _exception_type(record)
        if exception_type is not None:
            payload["exception_type"] = exception_type
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class TextLogFormatter(logging.Formatter):
    # Gera logs de linha única com os mesmos campos conservadores do JSON

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
                parts.append(f"{field}={_text_value(value)}")
        exception_type = _exception_type(record)
        if exception_type is not None:
            parts.append(f"exception_type={exception_type}")
        return " ".join(parts)


def configure_observability(app: Flask, settings: AppSettings) -> None:
    app.logger.setLevel(getattr(logging, settings.log_level))
    formatter: logging.Formatter
    if settings.log_format == "json":
        formatter = JsonLogFormatter()
    else:
        formatter = TextLogFormatter()
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


def _safe_message(record: logging.LogRecord) -> str:
    try:
        message = record.getMessage()
    except Exception:
        message = "<unformattable log message>"
    normalized = message.replace("\r", "\\r").replace("\n", "\\n")
    if len(normalized) <= _MAX_LOG_MESSAGE_LENGTH:
        return normalized
    return f"{normalized[:_MAX_LOG_MESSAGE_LENGTH]}…"


def _text_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _exception_type(record: logging.LogRecord) -> str | None:
    if record.exc_info and record.exc_info[0] is not None:
        return record.exc_info[0].__name__
    return None


__all__ = ["JsonLogFormatter", "TextLogFormatter", "configure_observability"]
