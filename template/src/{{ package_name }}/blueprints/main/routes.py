from flask import Blueprint, render_template


def create_main_blueprint() -> Blueprint:
    blueprint = Blueprint("main", __name__)

    @blueprint.get("/")
    def home() -> str:
        return render_template("main/home.html")

    return blueprint


__all__ = ["create_main_blueprint"]
