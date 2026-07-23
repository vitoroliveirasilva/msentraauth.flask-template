#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(dirname -- "$script_dir")
cd -- "$repository_root"

python -m pip install --constraint requirements/build.constraints.txt pip==26.1.2
python -m pip install --constraint requirements/development.constraints.txt -e ".[dev]"
python scripts/validate_supply_chain.py
ruff check .
ruff format --check .
mypy src tests
python -m compileall -q src tests scripts
pytest
bandit -c pyproject.toml -r src scripts
pip-audit --local
python -m pip check

rm -rf dist build
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
