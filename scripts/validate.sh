#!/usr/bin/env sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repository_root=$(dirname -- "$script_dir")
output_root="$repository_root/.template-test-output"

case "$output_root" in
    "$repository_root"/*) ;;
    *) echo "refusing to remove output outside the repository" >&2; exit 1 ;;
esac
rm -rf -- "$output_root"
mkdir -p -- "$output_root"
cd -- "$repository_root"

python -m pip install \
    --constraint requirements/generator.constraints.txt \
    copier jinja2 mypy pytest pyyaml ruff
ruff check template_tests scripts/check_generated_project.py
mypy template_tests scripts/check_generated_project.py
pytest -q

render_and_check() {
    destination=$1
    project_name=$2
    project_slug=$3
    package_name=$4
    graph=$5
    copier copy --trust --defaults \
        --data "project_name=$project_name" \
        --data "project_slug=$project_slug" \
        --data "package_name=$package_name" \
        --data "include_graph_example=$graph" \
        --data "python_version=3.12" \
        . "$destination"
    python scripts/check_generated_project.py "$destination"
    python -m compileall -q "$destination/src" "$destination/tests"
}

render_and_check "$output_root/minimal" "Acme Portal" "acme-portal" "acme_portal" false
render_and_check "$output_root/graph" "Graph App" "graph-app" "graph_core" true
