from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from template_tests.render import ROOT, render_project


@pytest.fixture()
def generated(tmp_path: Path) -> Path:
    return render_project(
        tmp_path / "app",
        project_name="Acme Portal",
        project_slug="acme-portal",
        package_name="acme_portal",
        include_graph_example=False,
        python_version="3.12",
    )


def test_copier_contract_exists() -> None:
    text = (ROOT / "copier.yml").read_text(encoding="utf-8")
    assert "_min_copier_version" in text and "include_graph_example" in text


def test_default_render_uses_requested_package(generated: Path) -> None:
    assert (generated / "src/acme_portal/__init__.py").is_file()
    assert not (generated / "src/msentraauth_template").exists()
    assert (generated / ".copier-answers.yml").is_file()


def test_default_render_omits_graph(generated: Path) -> None:
    assert not (generated / "src/acme_portal/features/graph").exists()
    assert not (generated / "src/acme_portal/blueprints/account").exists()
    assert "requests>=" not in (generated / "pyproject.toml").read_text(encoding="utf-8")


def test_graph_render_includes_graph(tmp_path: Path) -> None:
    root = render_project(
        tmp_path / "graph",
        project_name="Graph App",
        project_slug="graph-app",
        package_name="graph_app",
        include_graph_example=True,
    )
    assert (root / "src/graph_app/features/graph/client.py").is_file()
    assert (root / "docs/GRAPH.md").is_file()
    assert "requests>=" in (root / "pyproject.toml").read_text(encoding="utf-8")


def test_slug_and_package_can_diverge(tmp_path: Path) -> None:
    root = render_project(
        tmp_path / "ops",
        project_name="Ops Web",
        project_slug="ops-web",
        package_name="ops_core",
        include_graph_example=False,
    )
    assert (root / "src/ops_core/settings.py").is_file()
    assert 'packages = ["src/ops_core"]' in (root / "pyproject.toml").read_text(encoding="utf-8")


def test_rendered_project_has_namespaced_templates(generated: Path) -> None:
    assert (generated / "src/acme_portal/templates/layout/base.html").is_file()
    assert (generated / "src/acme_portal/templates/main/home.html").is_file()
    assert not (generated / "src/acme_portal/templates/base.html").exists()
    runtime_templates = (generated / "src/acme_portal/templates").rglob("*.html")
    assert all("{% raw %}" not in path.read_text(encoding="utf-8") for path in runtime_templates)


def test_example_environment_is_bootable(generated: Path) -> None:
    environment = (generated / ".env.example").read_text(encoding="utf-8")
    compose = (generated / "compose.yaml").read_text(encoding="utf-8")
    assert "MS_ENTRA_SCOPES=User.Read" in environment
    assert "REDIS_PASSWORD=" in environment
    assert "@redis:6379/0" in compose
    assert "internal: true" in compose


def test_login_ui_is_separate_from_extension_route(generated: Path) -> None:
    text = (generated / "src/acme_portal/blueprints/auth_ui/routes.py").read_text(encoding="utf-8")
    html = (generated / "src/acme_portal/templates/auth/login.html").read_text(encoding="utf-8")
    assert '@blueprint.get("/login")' in text
    assert "ms_entra_auth.login" in html


def test_local_user_registry_is_gone(generated: Path) -> None:
    all_python = "\n".join(p.read_text(encoding="utf-8") for p in (generated / "src").rglob("*.py"))
    assert "LocalUserRegistry" not in all_python
    assert "AuthenticatedIdentityHandler" in all_python


def test_security_defaults_are_strict(generated: Path) -> None:
    text = (generated / "src/acme_portal/infrastructure/security.py").read_text(encoding="utf-8")
    assert '"frame-ancestors": ("\'none\'",)' in text
    assert "unsafe-inline" not in text
    assert "Strict-Transport-Security" in text


def test_session_is_redis_and_aead_based(generated: Path) -> None:
    envelope = (generated / "src/acme_portal/infrastructure/session_envelope.py").read_text(
        encoding="utf-8"
    )
    backend = (generated / "src/acme_portal/infrastructure/session_backend.py").read_text(
        encoding="utf-8"
    )
    assert "AESGCM" in envelope and "HKDF" in envelope
    assert "_ATOMIC_ROTATE_SCRIPT" in backend and "subject_fingerprint" in backend


def test_readiness_is_independent_from_graph(generated: Path) -> None:
    text = (generated / "src/acme_portal/blueprints/ops/routes.py").read_text(encoding="utf-8")
    assert "/health/ready" in text and "Graph" not in text


def test_generated_ci_has_quality_and_security_gates(generated: Path) -> None:
    text = (generated / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    for command in ("ruff check", "mypy src", "pytest", "bandit", "pip-audit", "docker build"):
        assert command in text


def test_generated_python_compiles(generated: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            str(generated / "src"),
            str(generated / "tests"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_generated_scanner_passes(generated: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_generated_project.py"), str(generated)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
