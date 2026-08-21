from __future__ import annotations

from flask import Blueprint, Response, current_app, g, make_response, render_template
from flask_ms_entra_auth import MicrosoftEntraAuth, current_identity

from ...features.graph.client import (
    GraphClient,
    GraphError,
    GraphForbidden,
    GraphRateLimited,
    GraphUnauthorized,
    GraphUnavailable,
)


def create_account_blueprint(extension: MicrosoftEntraAuth, graph: GraphClient) -> Blueprint:
    blueprint = Blueprint("account", __name__)

    @blueprint.get("/profile")
    @extension.login_required
    def profile() -> str:
        token = extension.acquire_token(["User.Read"])
        return render_template(
            "account/profile.html",
            identity=current_identity,
            profile=graph.get_profile(token),
        )

    @blueprint.app_errorhandler(GraphUnauthorized)
    def unauthorized(error: GraphUnauthorized) -> tuple[str, int]:
        current_app.logger.warning("graph unauthorized", extra={"error_type": type(error).__name__})
        return _render(
            "Microsoft Graph recusou o acesso",
            "Entre novamente e repita a operação.",
            401,
        )

    @blueprint.app_errorhandler(GraphForbidden)
    def forbidden(error: GraphForbidden) -> tuple[str, int]:
        current_app.logger.warning("graph forbidden", extra={"error_type": type(error).__name__})
        return _render("Operação não autorizada", "A identidade atual não possui permissão.", 403)

    @blueprint.app_errorhandler(GraphRateLimited)
    def rate_limited(error: GraphRateLimited) -> Response:
        response = make_response(
            _render(
                "Microsoft Graph temporariamente limitado",
                "Tente novamente em instantes.",
                503,
            )
        )
        response.headers["Retry-After"] = str(error.retry_after or 30)
        return response

    @blueprint.app_errorhandler(GraphUnavailable)
    def unavailable(error: GraphUnavailable) -> Response:
        response = make_response(
            _render(
                "Microsoft Graph indisponível",
                "O serviço externo não respondeu.",
                503,
            )
        )
        response.headers["Retry-After"] = str(error.retry_after or 30)
        return response

    @blueprint.app_errorhandler(GraphError)
    def graph_error(error: GraphError) -> tuple[str, int]:
        current_app.logger.warning(
            "graph response rejected", extra={"error_type": type(error).__name__}
        )
        return _render(
            "Resposta inválida do Microsoft Graph",
            "A resposta externa não pôde ser processada.",
            502,
        )

    return blueprint


def _render(title: str, message: str, status_code: int) -> tuple[str, int]:
    return (
        render_template(
            "errors/error.html",
            title=title,
            message=message,
            status_code=status_code,
            request_id=getattr(g, "request_id", None),
        ),
        status_code,
    )


__all__ = ["create_account_blueprint"]
