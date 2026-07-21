$ErrorActionPreference = "Stop"

python -m pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src tests
python -m compileall -q src tests
pytest
bandit -c pyproject.toml -r src
pip-audit .
python -m pip check

Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
python -m build
python -m twine check dist/*
$env:DIST_DIR = "dist"
try {
    pytest tests/test_distribution.py --no-cov
}
finally {
    Remove-Item Env:DIST_DIR -ErrorAction SilentlyContinue
}
