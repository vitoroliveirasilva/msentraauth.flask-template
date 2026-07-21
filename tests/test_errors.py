from __future__ import annotations

from typing import NoReturn

from flask import abort

from conftest import FakeMsalClient, GraphTransportDouble, RedisDouble
from msentraauth_template import create_app
from msentraauth_template.settings import AppSettings


def test_sanitized_http_error_pages(
    settings: AppSettings,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    app = create_app(
        settings,
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=GraphTransportDouble(),
    )
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.get("/abort/<int:status>")
    def abort_status(status: int) -> NoReturn:
        abort(status)

    @app.get("/explode")
    def explode() -> NoReturn:
        raise RuntimeError("must-not-be-rendered")

    client = app.test_client()
    expectations = {
        "/abort/400": (400, "Requisição inválida"),
        "/abort/403": (403, "Acesso negado"),
        "/missing": (404, "Página não encontrada"),
        "/abort/413": (413, "Requisição muito grande"),
        "/explode": (500, "Falha interna"),
    }
    for path, (status, text) in expectations.items():
        response = client.get(path, headers={"X-Request-ID": "request-12345678"})
        assert response.status_code == status
        assert text in response.text
        assert "request-12345678" in response.text
        assert "must-not-be-rendered" not in response.text

    method = client.post("/")
    assert method.status_code == 405
    assert "Método não permitido" in method.text


def test_untrusted_host_returns_plain_sanitized_bad_request(
    settings: AppSettings,
    redis_double: RedisDouble,
    msal_runtime: tuple[FakeMsalClient, object],
) -> None:
    _, factory = msal_runtime
    app = create_app(
        settings,
        redis_client=redis_double,
        msal_client_factory=factory,  # type: ignore[arg-type]
        graph_transport=GraphTransportDouble(),
    )

    response = app.test_client().get("/", headers={"Host": "evil.example.test"})

    assert response.status_code == 400
    assert response.mimetype == "text/plain"
    assert response.text == "Bad Request\n"
    assert "evil.example.test" not in response.text
