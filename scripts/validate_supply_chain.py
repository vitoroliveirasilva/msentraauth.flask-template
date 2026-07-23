from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

_ACTION_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^@\s]+)@([^#\s]+)(?:\s+#\s*(.+))?\s*$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_EXACT_REQUIREMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?==[^;\s]+$")
_EXPECTED_ACTIONS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/setup-python": "5fda3b95a4ea91299a34e894583c3862153e4b97",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "actions/download-artifact": "d3f86a106a0bac45b974a628896c90dbdf5c8093",
    "actions/attest-build-provenance": "977bb373ede98d70efdf65b84cb5f73e068dcc2a",
    "actions/dependency-review-action": "2031cfc080254a8a887f58cffee85186f0e49e48",
    "docker/setup-qemu-action": "96fe6ef7f33517b61c61be40b68a1882f3264fb8",
    "docker/setup-buildx-action": "bb05f3f5519dd87d3ba754cc423b652a5edd6d2c",
    "docker/build-push-action": "53b7df96c91f9c12dcc8a07bcb9ccacbed38856a",
    "docker/login-action": "af1e73f918a031802d376d3c8bbc3fe56130a9b0",
    "docker/metadata-action": "dc802804100637a589fabce1cb79ff13a1411302",
    "aquasecurity/trivy-action": "ed142fd0673e97e23eac54620cfb913e5ce36c25",
}
_EXPECTED_PYTHON_DIGEST = "sha256:a9bee15510a364124aa24692899d269835683b883de42f7ebec8c293cf679ccb"
_EXPECTED_REDIS_DIGEST = "sha256:9d317178eceac8454a2284a9e6df2466b93c745529947f0cd42a0fa9609d7005"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _workflow_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        text = _read(path)
        lines = text.splitlines()
        if "permissions: {}" not in text:
            violations.append(f"{path}: workflow must default to permissions: {{}}")
        checkout_indexes: list[int] = []
        for index, line in enumerate(lines):
            match = _ACTION_RE.match(line)
            if match is None:
                continue
            action, ref, annotation = match.groups()
            if action.startswith("./"):
                continue
            if not _SHA_RE.fullmatch(ref):
                violations.append(f"{path}:{index + 1}: mutable action reference {action}@{ref}")
                continue
            expected = _EXPECTED_ACTIONS.get(action)
            if expected is None:
                violations.append(f"{path}:{index + 1}: action {action} is not allowlisted")
            elif ref != expected:
                violations.append(f"{path}:{index + 1}: unexpected SHA for {action}")
            if not annotation:
                violations.append(f"{path}:{index + 1}: pinned action requires version annotation")
            if action == "actions/checkout":
                checkout_indexes.append(index)
        for index in checkout_indexes:
            block = "\n".join(lines[index : index + 8])
            if "persist-credentials: false" not in block:
                violations.append(
                    f"{path}:{index + 1}: checkout must disable persisted credentials"
                )
        if "pip install --upgrade pip" in text:
            violations.append(f"{path}: dynamic pip bootstrap is forbidden")
    return violations


def _constraint_violations(root: Path) -> list[str]:
    violations: list[str] = []
    expected = {
        "runtime.constraints.txt",
        "development.constraints.txt",
        "build.constraints.txt",
    }
    present = {path.name for path in (root / "requirements").glob("*.constraints.txt")}
    missing = sorted(expected - present)
    if missing:
        violations.append(f"missing constraints: {', '.join(missing)}")
    for path in sorted((root / "requirements").glob("*.constraints.txt")):
        seen: set[str] = set()
        for number, raw in enumerate(_read(path).splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if not _EXACT_REQUIREMENT_RE.fullmatch(line):
                violations.append(f"{path}:{number}: requirement must use exact == pin")
                continue
            name = line.partition("==")[0].casefold()
            if name in seen:
                violations.append(f"{path}:{number}: duplicate requirement {name}")
            seen.add(name)
    return violations


def _container_violations(root: Path) -> list[str]:
    violations: list[str] = []
    dockerfile = _read(root / "Dockerfile")
    compose = _read(root / "compose.yaml")
    ci = _read(root / ".github" / "workflows" / "ci.yml")
    publish = _read(root / ".github" / "workflows" / "publish-container.yml")
    dockerignore = _read(root / ".dockerignore")
    if _EXPECTED_PYTHON_DIGEST not in dockerfile:
        violations.append("Dockerfile: Python base image is not pinned to the approved digest")
    if "pip install --upgrade pip" in dockerfile:
        violations.append("Dockerfile: dynamic pip bootstrap is forbidden")
    if dockerfile.count("pip==26.1.2") < 3:
        violations.append("Dockerfile: builder and runtime must use the approved pip version")
    sources = (("compose.yaml", compose), ("ci.yml", ci), ("publish-container.yml", publish))
    for path, text in sources:
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "redis:8-alpine" in line and _EXPECTED_REDIS_DIGEST not in line:
                violations.append(f"{path}:{line_number}: Redis image is not digest-pinned")
    if not dockerignore.startswith("**\n"):
        violations.append(".dockerignore: build context must use a deny-all allowlist")
    for token in (
        '"127.0.0.1:5000:8000"',
        "internal: true",
        "pids_limit:",
        "mem_limit:",
        "cpus:",
        "cap_drop:",
        "no-new-privileges:true",
        "read_only: true",
        "--requirepass",
    ):
        if token not in compose:
            violations.append(f"compose.yaml: missing hardening token {token}")
    return violations


def _project_violations(root: Path) -> list[str]:
    violations: list[str] = []
    data = tomllib.loads(_read(root / "pyproject.toml"))
    build_requires = data["build-system"]["requires"]
    if build_requires != ["hatchling==1.31.0"]:
        violations.append("pyproject.toml: build backend must be exactly pinned")
    dependencies = data["project"]["dependencies"]
    if "flask-ms-entra-auth==1.0.0" not in dependencies:
        violations.append("pyproject.toml: extension contract must be exactly pinned")
    scripts = _read(root / "scripts" / "validate.sh") + _read(root / "scripts" / "validate.ps1")
    if "pip==26.1.2" not in scripts:
        violations.append("validation scripts must bootstrap the approved pip version")
    if "requirements/development.constraints.txt" not in scripts:
        violations.append("validation scripts must install through development constraints")
    publish = _read(root / ".github" / "workflows" / "publish-container.yml")
    for token in (
        "Build multi-platform candidate once",
        "Verify exact candidate digest",
        "without rebuilding",
        "subject-digest:",
        "subject-checksums:",
        "SHA256SUMS",
        "sbom: true",
    ):
        if token not in publish:
            violations.append(f"publish workflow: missing build-once material {token}")
    return violations


def validate(root: Path) -> list[str]:
    return [
        *_workflow_violations(root),
        *_constraint_violations(root),
        *_container_violations(root),
        *_project_violations(root),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate immutable supply-chain policy")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    violations = validate(root)
    if violations:
        print("Supply-chain policy violations:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1
    print("Supply-chain policy validated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
