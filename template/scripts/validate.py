from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence


def _run(arguments: Sequence[str]) -> None:
    subprocess.run(arguments, check=True)


def main() -> int:
    python = sys.executable
    _run((python, "-m", "compileall", "-q", "src", "tests", "scripts"))
    _run(("ruff", "check", "src", "tests", "scripts", "gunicorn.conf.py", "wsgi.py"))
    _run(("mypy", "src"))
    _run(("pytest",))
    _run(("bandit", "-q", "-r", "src"))
    _run(("pip-audit", "--local"))
    _run((python, "-m", "pip", "check"))
    _run((python, "-m", "build"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
