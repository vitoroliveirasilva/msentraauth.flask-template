from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_policy(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/validate_supply_chain.py", "--root", str(root)],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def _copy_repository(tmp_path: Path) -> Path:
    target = tmp_path / "repository"
    shutil.copytree(
        _repository_root(),
        target,
        ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache"),
    )
    return target


def test_supply_chain_policy_is_self_consistent() -> None:
    completed = _run_policy(_repository_root())
    assert completed.returncode == 0, completed.stderr
    assert "validated successfully" in completed.stdout


def test_supply_chain_policy_rejects_mutable_action(tmp_path: Path) -> None:
    root = _copy_repository(tmp_path)
    workflow = root / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")
    workflow.write_text(
        text.replace(
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7",
            "actions/checkout@v7",
            1,
        ),
        encoding="utf-8",
    )

    completed = _run_policy(root)
    assert completed.returncode == 1
    assert "mutable action reference" in completed.stderr


def test_supply_chain_policy_rejects_ranged_constraint(tmp_path: Path) -> None:
    root = _copy_repository(tmp_path)
    constraints = root / "requirements" / "runtime.constraints.txt"
    text = constraints.read_text(encoding="utf-8")
    constraints.write_text(text.replace("Flask==3.1.3", "Flask>=3.1.3"), encoding="utf-8")

    completed = _run_policy(root)
    assert completed.returncode == 1
    assert "requirement must use exact == pin" in completed.stderr


def test_supply_chain_policy_rejects_mutable_redis_image(tmp_path: Path) -> None:
    root = _copy_repository(tmp_path)
    compose = root / "compose.yaml"
    text = compose.read_text(encoding="utf-8")
    compose.write_text(
        text.replace(
            "redis:8-alpine@sha256:9d317178eceac8454a2284a9e6df2466b93c745529947f0cd42a0fa9609d7005",
            "redis:8-alpine",
            1,
        ),
        encoding="utf-8",
    )

    completed = _run_policy(root)
    assert completed.returncode == 1
    assert "Redis image is not digest-pinned" in completed.stderr
