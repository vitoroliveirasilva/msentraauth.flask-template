from __future__ import annotations

from flask import Blueprint, Response, current_app, g, make_response, render_template
from flask_ms_entra_auth import MicrosoftEntraAuth, current_identity

from .client import (
    GraphClaimsChallenge,
    GraphClient,
    GraphError,
    GraphForbidden,
    GraphRateLimited,
    GraphUnauthorized,
    GraphUnavailable,
)


def create_graph_blueprint(
    extension: MicrosoftEntraAuth,
    graph: GraphClient,
) -> Blueprint:
    blueprint = Blueprint("graph", __name__)

    @blueprint.get("/profile")
    @extension.login_required
    def profile() -> str:
        token = extension.acquire_token(["User.Read"])
        graph_profile = graph.get_profile(token)
        return render_template(
            "profile.html",
            identity=current_identity,
            profile=graph_profile,
        )

    @blueprint.app_errorhandler(GraphClaimsChallenge)
    def handle_graph_claims_challenge(error: GraphClaimsChallenge) -> Response:
        current_app.logger.warning(
            "microsoft graph requested additional authentication claims",
            extra={"error_type": type(error).__name__},
        )
        response = make_response(
            render_template(
                "error.html",
                title="Reautenticação adicional necessária",
                message=(
                    "O Microsoft Entra ID exigiu validação adicional. "
                    "O fluxo automático depende de suporte da extensão de autenticação."
                ),
                status_code=401,
                request_id=getattr(g, "request_id", None),
            ),
            401,
        )
        response.headers["WWW-Authenticate"] = 'Bearer error="insufficient_claims"'
        return response

    @blueprint.app_errorhandler(GraphUnauthorized)
    def handle_graph_unauthorized(error: GraphUnauthorized) -> tuple[str, int]:
        current_app.logger.warning(
            "microsoft graph rejected delegated access",
            extra={"error_type": type(error).__name__},
        )
        return (
            render_template(
                "error.html",
                title="Microsoft Graph recusou o acesso",
                message="Entre novamente e repita a operação.",
                status_code=401,
                request_id=getattr(g, "request_id", None),
            ),
            401,
        )

    @blueprint.app_errorhandler(GraphForbidden)
    def handle_graph_forbidden(error: GraphForbidden) -> tuple[str, int]:
        current_app.logger.warning(
            "microsoft graph denied the requested operation",
            extra={"error_type": type(error).__name__},
        )
        return (
            render_template(
                "error.html",
                title="Operação não autorizada no Microsoft Graph",
                message="A identidade atual não possui permissão para esta operação.",
                status_code=403,
                request_id=getattr(g, "request_id", None),
            ),
            403,
        )

    @blueprint.app_errorhandler(GraphRateLimited)
    def handle_graph_rate_limited(error: GraphRateLimited) -> Response:
        current_app.logger.warning(
            "microsoft graph rate limit was reached",
            extra={"error_type": type(error).__name__},
        )
        response = make_response(
            render_template(
                "error.html",
                title="Microsoft Graph temporariamente limitado",
                message="Aguarde alguns instantes antes de tentar novamente.",
                status_code=503,
                request_id=getattr(g, "request_id", None),
            ),
            503,
        )
        response.headers["Retry-After"] = str(error.retry_after or 30)
        return response

    @blueprint.app_errorhandler(GraphUnavailable)
    def handle_graph_unavailable(error: GraphUnavailable) -> Response:
        current_app.logger.warning(
            "microsoft graph is unavailable",
            extra={"error_type": type(error).__name__},
        )
        response = make_response(
            render_template(
                "error.html",
                title="Microsoft Graph indisponível",
                message="O serviço externo não respondeu. Tente novamente em instantes.",
                status_code=503,
                request_id=getattr(g, "request_id", None),
            ),
            503,
        )
        response.headers["Retry-After"] = str(error.retry_after or 30)
        return response

    @blueprint.app_errorhandler(GraphError)
    def handle_graph_error(error: GraphError) -> tuple[str, int]:
        current_app.logger.warning(
            "microsoft graph returned an invalid response",
            extra={"error_type": type(error).__name__},
        )
        return (
            render_template(
                "error.html",
                title="Resposta inválida do Microsoft Graph",
                message="A resposta externa não pôde ser processada.",
                status_code=502,
                request_id=getattr(g, "request_id", None),
            ),
            502,
        )

    return blueprint


__all__ = ["create_graph_blueprint"]
