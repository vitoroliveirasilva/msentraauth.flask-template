from __future__ import annotations

from flask import Flask, Response, g, render_template
from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    MethodNotAllowed,
    NotFound,
    RequestEntityTooLarge,
    SecurityError,
)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(BadRequest)
    def bad_request(error: BadRequest) -> Response | tuple[str, int]:
        if isinstance(error, SecurityError):
            return app.response_class(
                "Bad Request\n",
                status=400,
                mimetype="text/plain",
            )
        return _render("Requisição inválida", "Revise os dados enviados.", 400)

    @app.errorhandler(Forbidden)
    def forbidden(_: Forbidden) -> tuple[str, int]:
        return _render("Acesso negado", "Esta operação não foi autorizada.", 403)

    @app.errorhandler(NotFound)
    def not_found(_: NotFound) -> tuple[str, int]:
        return _render("Página não encontrada", "O endereço informado não existe.", 404)

    @app.errorhandler(MethodNotAllowed)
    def method_not_allowed(_: MethodNotAllowed) -> tuple[str, int]:
        return _render(
            "Método não permitido", "Use o método HTTP esperado por esta rota.", 405
        )

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_: RequestEntityTooLarge) -> tuple[str, int]:
        return _render(
            "Requisição muito grande", "O conteúdo excede o limite aceito.", 413
        )

    @app.errorhandler(500)
    def internal_error(_: object) -> tuple[str, int]:
        return _render(
            "Falha interna",
            "A operação não pôde ser concluída. Use o identificador da requisição no suporte.",
            500,
        )


def _render(title: str, message: str, status_code: int) -> tuple[str, int]:
    return (
        render_template(
            "error.html",
            title=title,
            message=message,
            status_code=status_code,
            request_id=getattr(g, "request_id", None),
        ),
        status_code,
    )


__all__ = ["register_error_handlers"]
