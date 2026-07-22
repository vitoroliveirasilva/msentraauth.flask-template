from __future__ import annotations

import json
import logging
from dataclasses import replace
from io import StringIO
from typing import cast

from flask import Flask, Response

from msentraauth_template.observability import (
    JsonLogFormatter,
    TextLogFormatter,
    configure_observability,
)
from msentraauth_template.settings import AppSettings


def _exception_record(message: str = "safe message") -> logging.LogRecord:
    try:
        raise ValueError("sensitive-value")
    except ValueError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg=message,
            args=(),
            exc_info=__import__("sys").exc_info(),
        )
    record.request_id = "request-12345678"
    record.secret = "must-not-appear"
    return record


def test_json_formatter_uses_allowlisted_fields_and_exception_type() -> None:
    payload = json.loads(JsonLogFormatter().format(_exception_record()))
    assert payload["message"] == "safe message"
    assert payload["request_id"] == "request-12345678"
    assert payload["exception_type"] == "ValueError"
    assert "secret" not in payload
    assert "sensitive-value" not in json.dumps(payload)


def test_text_formatter_is_single_line_allowlisted_and_sanitized() -> None:
    rendered = TextLogFormatter().format(_exception_record("safe\ninjected"))
    assert "safe\\ninjected" in rendered
    assert 'request_id="request-12345678"' in rendered
    assert "exception_type=ValueError" in rendered
    assert "must-not-appear" not in rendered
    assert "sensitive-value" not in rendered
    assert "\n" not in rendered


def test_json_and_text_observability_configuration(settings: AppSettings) -> None:
    for log_format in ("json", "text"):
        app = Flask(f"observability-{log_format}")
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        app.logger.handlers = [handler]
        configure_observability(app, replace(settings, log_format=log_format))

        @app.get("/")
        def index() -> str:
            return "ok"

        response = app.test_client().get("/", headers={"X-Request-ID": "unsafe value"})
        assert response.status_code == 200
        assert len(response.headers["X-Request-ID"]) == 32
        rendered = stream.getvalue()
        assert "http request completed" in rendered
        if log_format == "json":
            payload = json.loads(rendered)
            assert payload["endpoint"] == "index"
            assert payload["status_code"] == 200
        else:
            assert 'endpoint="index"' in rendered
            assert "status_code=200" in rendered
            assert "duration_ms=" in rendered


def test_after_request_fallbacks_without_before_request(settings: AppSettings) -> None:
    app = Flask("observability-fallback")
    configure_observability(app, settings)
    finish_request = app.after_request_funcs[None][0]
    with app.test_request_context("/missing"):
        response = cast(Response, finish_request(Response("ok")))
    assert response.headers["X-Request-ID"]


def test_formatters_bound_and_tolerate_unformattable_messages() -> None:
    broken = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="%s %s",
        args=("only-one",),
        exc_info=None,
    )
    assert "<unformattable log message>" in TextLogFormatter().format(broken)

    long_record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="x" * 5000,
        args=(),
        exc_info=None,
    )
    payload = json.loads(JsonLogFormatter().format(long_record))
    assert payload["message"].endswith("…")
    assert len(payload["message"]) == 4097
