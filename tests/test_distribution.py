from __future__ import annotations

import os
import tarfile
import tomllib
import zipfile
from pathlib import Path
from typing import cast

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROJECT_DATA = tomllib.loads((_PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
_PROJECT = cast(dict[str, object], _PROJECT_DATA["project"])
_VERSION = cast(str, _PROJECT["version"])
_PROJECT_NAME = cast(str, _PROJECT["name"])
_WHEEL_DISTRIBUTION = _PROJECT_NAME.replace("-", "_")


def _dist_dir() -> Path:
    configured = os.environ.get("DIST_DIR")
    if configured is None:
        pytest.skip("set DIST_DIR after running `python -m build`")
    dist_dir = Path(configured)
    if not dist_dir.is_dir():
        pytest.fail(f"DIST_DIR does not exist or is not a directory: {dist_dir}")
    return dist_dir


@pytest.mark.distribution
def test_build_contains_application_assets_and_operational_files() -> None:
    dist_dir = _dist_dir()
    wheels = list(dist_dir.glob(f"{_WHEEL_DISTRIBUTION}-{_VERSION}-*.whl"))
    sdists = list(dist_dir.glob(f"{_WHEEL_DISTRIBUTION}-{_VERSION}.tar.gz"))
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
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = wheel.read(metadata_name).decode()
        assert f"Version: {_VERSION}" in metadata
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
