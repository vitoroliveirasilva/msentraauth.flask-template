from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".py", ".toml", ".yml", ".yaml", ".md", ".html", ".css", ".js", ".txt"}
FORBIDDEN = (
    "msentraauth_template",
    "msentraauth-flask-template",
    "msentra-template-local",
    "template_settings",
    "template_redis",
    "template_session_codec",
    "template_entra_auth",
    "template_graph",
    "MS Entra Auth",
)
COPIER_TOKEN = re.compile(
    r"(?:\{\{\s*(?:project_name|project_slug|package_name|distribution_name|"
    r"project_description|include_graph_example|python_image|"
    r"python_version)\b|\{%\s*(?:if|endif).*include_graph_example|\{%\s*raw\s*%\})"
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_generated_project.py <project-root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"generated project directory not found: {root}", file=sys.stderr)
        return 2
    failures: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        rel = path.relative_to(root).as_posix()
        if COPIER_TOKEN.search(text):
            failures.append(f"unresolved Copier token: {rel}")
        if rel != ".copier-answers.yml":
            for value in FORBIDDEN:
                if value in text:
                    failures.append(f"forbidden template identity {value!r}: {rel}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
