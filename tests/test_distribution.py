from __future__ import annotations

import os
import tarfile
import zipfile
from pathlib import Path

import pytest


def _dist_dir() -> Path:
    configured = os.environ.get("DIST_DIR")
    if configured is None:
        pytest.skip("set DIST_DIR after running `python -m build`")
    return Path(configured)


@pytest.mark.distribution
def test_build_contains_application_assets_and_operational_files() -> None:
    dist_dir = _dist_dir()
    wheels = list(dist_dir.glob("msentraauth_flask_template-1.0.0-*.whl"))
    sdists = list(dist_dir.glob("msentraauth_flask_template-1.0.0.tar.gz"))
    assert len(wheels) == 1
    assert len(sdists) == 1

    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
        assert "msentraauth_template/settings.py" in names
        assert "msentraauth_template/session_backend.py" in names
        assert "msentraauth_template/storage.py" in names
        assert "msentraauth_template/graph/client.py" in names
        assert "msentraauth_template/templates/home.html" in names
        assert "msentraauth_template/static/app.css" in names
        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata = wheel.read(metadata_name).decode()
        assert "Version: 1.0.0" in metadata
        assert "Requires-Dist: flask-ms-entra-auth<2,>=1.0" in metadata

    with tarfile.open(sdists[0], "r:gz") as sdist:
        names = set(sdist.getnames())
        for suffix in (
            "/Dockerfile",
            "/compose.yaml",
            "/.env.example",
            "/.github/workflows/ci.yml",
            "/docs/implementation/status.md",
            "/tests/test_extension_contract.py",
            "/wsgi.py",
        ):
            assert any(name.endswith(suffix) for name in names)
