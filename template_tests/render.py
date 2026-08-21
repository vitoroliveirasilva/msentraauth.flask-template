from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).parents[1]
TEMPLATE = ROOT / "template"


def render_project(
    output: Path,
    *,
    project_name: str,
    project_slug: str,
    package_name: str,
    include_graph_example: bool,
    python_version: str = "3.12",
) -> Path:
    context = {
        "project_name": project_name,
        "project_slug": project_slug,
        "package_name": package_name,
        "distribution_name": project_slug,
        "app_display_name": project_name,
        "project_description": "Aplicação Flask com Microsoft Entra ID e sessão Redis server-side.",
        "include_graph_example": include_graph_example,
        "python_version": python_version,
        "python_image": {
            "3.12": "python:3.12-slim-bookworm@sha256:a116514e19457bcb7af7efe9c3dd0b9b71e85b317694e7882a1c52aa15a78134",
            "3.13": "python:3.13-slim-bookworm@sha256:00faa2debb87529f9f0764e9491d8ba400a3678976616c3bd7cb193745ac20d1",
            "3.14": "python:3.14-slim-bookworm@sha256:23c59390fc717bf09f9336908199a0ae75d9c4264bf296123f94ad772fea3b52",
        }[python_version],
    }
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True, autoescape=False)
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)

    for source in sorted(TEMPLATE.rglob("*")):
        if source.name == "{{ _copier_conf.answers_file }}.jinja":
            continue
        relative = source.relative_to(TEMPLATE)
        rendered_parts = [env.from_string(part).render(context) for part in relative.parts]
        rendered_relative = Path(*rendered_parts)
        if not include_graph_example and _graph_only(rendered_relative):
            continue
        if source.is_dir():
            (output / rendered_relative).mkdir(parents=True, exist_ok=True)
            continue
        target = output / rendered_relative
        if target.name.endswith(".jinja"):
            target = target.with_name(target.name.removesuffix(".jinja"))
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.name.endswith(".jinja"):
            target.write_text(
                env.from_string(source.read_text(encoding="utf-8")).render(context),
                encoding="utf-8",
            )
        else:
            shutil.copy2(source, target)
    (output / ".copier-answers.yml").write_text(
        "\n".join(
            [
                "_commit: local-validation",
                "project_name: " + project_name,
                "project_slug: " + project_slug,
                "package_name: " + package_name,
                "include_graph_example: " + str(include_graph_example).lower(),
                "python_version: '" + python_version + "'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def _graph_only(path: Path) -> bool:
    posix = path.as_posix()
    return (
        "/features/graph/" in f"/{posix}/"
        or "/blueprints/account/" in f"/{posix}/"
        or "/templates/account/" in f"/{posix}/"
        or posix in {"docs/GRAPH.md", "tests/test_graph.py", "tests/test_graph.py.jinja"}
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--graph", action="store_true")
    parser.add_argument("--python-version", default="3.12")
    args = parser.parse_args()
    render_project(
        args.output,
        project_name=args.project_name,
        project_slug=args.project_slug,
        package_name=args.package_name,
        include_graph_example=args.graph,
        python_version=args.python_version,
    )


if __name__ == "__main__":
    main()
