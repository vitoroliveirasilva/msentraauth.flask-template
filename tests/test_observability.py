from __future__ import annotations

import json
import logging
from dataclasses import replace
from io import StringIO
from typing import cast

from flask import Flask, Response

from msentraauth_template.observability import JsonLogFormatter, configure_observability
from msentraauth_template.settings import AppSettings


def test_json_formatter_uses_allowlisted_fields_and_exception_type() -> None:
    formatter = JsonLogFormatter()
    try:
        raise ValueError("sensitive-value")
    except ValueError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="safe message",
            args=(),
            exc_info=__import__("sys").exc_info(),
        )
    record.request_id = "request-12345678"
    record.secret = "must-not-appear"
    payload = json.loads(formatter.format(record))
    assert payload["message"] == "safe message"
    assert payload["request_id"] == "request-12345678"
    assert payload["exception_type"] == "ValueError"
    assert "secret" not in payload
    assert "sensitive-value" not in json.dumps(payload)


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
        assert "http request completed" in stream.getvalue()
        if log_format == "json":
            assert json.loads(stream.getvalue())["endpoint"] == "index"


def test_after_request_fallbacks_without_before_request(settings: AppSettings) -> None:
    app = Flask("observability-fallback")
    configure_observability(app, settings)
    finish_request = app.after_request_funcs[None][0]
    with app.test_request_context("/missing"):
        response = cast(Response, finish_request(Response("ok")))
    assert response.headers["X-Request-ID"]
