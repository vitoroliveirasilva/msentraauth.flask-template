#!/usr/bin/env sh
set -eu

python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src tests
python -m compileall -q src tests
pytest
bandit -c pyproject.toml -r src
pip-audit .
python -m pip check

rm -rf dist build
python -m build
python -m twine check dist/*
DIST_DIR=dist pytest tests/test_distribution.py --no-cov
